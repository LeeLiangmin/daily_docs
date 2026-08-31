# nginx bot-forge 负载均衡与静态服务配置方案

## 1. 架构总览

```
客户端 --HTTP--> C (nginx, 反向代理 + 加权负载均衡)
                    ├── A (nginx 静态服务, weight=2)  /var/www/bot-forge/
                    └── B (nginx 静态服务, weight=1)  /var/www/bot-forge/
```

- **A / B**：各自用 nginx 提供 bot-forge 静态文件，站点路径 `/bot-forge/`，并配置 CORS 跨域支持。
- **C**：接收 `http://xxx/bot-forge/` 请求，按 **2:1 权重** 轮询转发给 A / B，**保留原路径前缀**。
- 操作系统：Ubuntu/Debian；暂用 HTTP（80 端口）。

## 2. A / B 机器配置（静态文件服务，两台都执行）

### 2.1 安装 nginx

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
```

### 2.2 准备静态文件目录

```bash
sudo mkdir -p /var/www/bot-forge
# 将 bot-forge 的静态文件放入 /var/www/bot-forge/
```

### 2.3 新建站点配置（含 CORS）

```bash
sudo tee /etc/nginx/sites-available/bot-forge > /dev/null <<'EOF'
server {
    listen 80;
    server_name A的IP;   # A 机填 A 的 IP，B 机填 B 的 IP

    location /bot-forge/ {
        alias /var/www/bot-forge/;
        index index.html;

        # CORS 响应头
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;

        # 拦截浏览器预检请求，直接返回 204
        if ($request_method = OPTIONS) {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, HEAD, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
            add_header Access-Control-Max-Age 86400;
            return 204;
        }
    }

    location ~ \.php$ { return 404; }
}
EOF
```

说明：
- `alias` 让 `/bot-forge/xxx` 对应磁盘 `/var/www/bot-forge/xxx`，两端路径都带 `/` 才能正确拼接。
- `if ($request_method = OPTIONS)` 拦截预检请求，避免打到静态目录。
- `always` 让 404 等错误响应也带上 CORS 头，跨域下前端能正确读取错误。
- 若前端需要携带 Cookie（凭证），将 `Access-Control-Allow-Origin` 改为具体来源域名，并添加 `add_header Access-Control-Allow-Credentials true;`（注意此时不能再使用 `*`）。

### 2.4 启用站点并去掉默认站点

```bash
sudo ln -s /etc/nginx/sites-available/bot-forge /etc/nginx/sites-enabled/bot-forge
sudo rm -f /etc/nginx/sites-enabled/default
```

### 2.5 校验并生效

```bash
sudo nginx -t          # 输出 syntax is ok 即通过
sudo systemctl reload nginx
```

### 2.6 验证本机

```bash
curl -I http://127.0.0.1/bot-forge/index.html
```

应返回 200，并带 `Access-Control-Allow-Origin` 头。

## 3. C 机器配置（反向代理 + 加权负载均衡）

### 3.1 安装 nginx

```bash
sudo apt update && sudo apt install -y nginx
sudo systemctl enable nginx
```

### 3.2 新建代理配置

```bash
sudo tee /etc/nginx/sites-available/bot-forge > /dev/null <<'EOF'
upstream bot_forge_backend {
    server A的IP:80 weight=2;
    server B的IP:80 weight=1;
}

server {
    listen 80;
    server_name xxx;   # 对外域名或 C 的 IP

    location /bot-forge/ {
        proxy_pass http://bot_forge_backend;   # 不带 URI，保留 /bot-forge/ 前缀
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

关键点：
- `proxy_pass http://bot_forge_backend;` 末尾**不带路径**（写成 `http://bot_forge_backend/` 就会丢掉前缀），这样原始 URI 原样转发到后端 `/bot-forge/...`，与 A/B 的 `alias` 对应。
- **C 不需要配置 CORS**：`proxy_pass` 默认透传后端响应头，A/B 返回的 CORS 头会原样出现在 C 的响应里，不会重复。

### 3.3 启用站点

```bash
sudo ln -s /etc/nginx/sites-available/bot-forge /etc/nginx/sites-enabled/bot-forge
sudo rm -f /etc/nginx/sites-enabled/default
```

### 3.4 校验并生效

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 4. 防火墙放行（三台机器都做）

```bash
sudo ufw allow 80/tcp
# 若用云厂商安全组，需在控制台放行 80 端口
```

## 5. 验证

在客户端机器执行：

```bash
# 普通请求，应返回 200 并带 CORS 头
curl -I -H "Origin: http://frontend.example.com" http://xxx/bot-forge/index.html

# 预检请求，应返回 204 + CORS 头
curl -X OPTIONS -i http://xxx/bot-forge/index.html \
  -H "Origin: http://frontend.example.com" \
  -H "Access-Control-Request-Method: GET"
```

确认流量按 2:1 分布（多刷新几次，查看 A/B 的 access.log）：

```bash
sudo tail -f /var/log/nginx/access.log
```

## 6. 常用运维命令

```bash
sudo nginx -t                 # 校验配置语法
sudo systemctl reload nginx   # 平滑重载，不中断请求
sudo systemctl restart nginx  # 重启
sudo systemctl status nginx   # 查看状态
sudo journalctl -u nginx -f   # 查看日志
```

## 7. 备注

- **健康检查**：上游默认已有基础能力（失败请求会被标记），可增强为 `server A的IP:80 weight=2 max_fails=3 fail_timeout=30s;`，连续 3 次失败则 30 秒内自动摘除。
- **HTTPS**：后续需要时在 C 上做 TLS 终止，`listen 80;` 改为 `listen 443 ssl;` 并配置证书。
- **Cookie 凭证场景**：CORS 的 `Access-Control-Allow-Origin` 需改为精确来源域名并加 `Access-Control-Allow-Credentials true;`。
