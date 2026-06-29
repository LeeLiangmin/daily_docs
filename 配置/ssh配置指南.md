# VSCode SSH 免密登录配置指南

> 通过配置 SSH 密钥对认证，避免每次连接远程服务器时重复输入密码。

---

## 第一步：生成 SSH 密钥（本地机器）

在本地终端执行：

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

一路回车即可（也可设置 Passphrase，但每次仍需输入该密码）。

生成后产生两个文件：

| 文件 | 路径 | 说明 |
|------|------|------|
| 私钥 | `~/.ssh/id_ed25519` | 保留在本地，切勿泄露 |
| 公钥 | `~/.ssh/id_ed25519.pub` | 需要复制到远程服务器 |

---

## 第二步：将公钥复制到远程服务器

**方法 A：一键命令（推荐）**

```bash
ssh-copy-id username@remote_host
```

**方法 B：手动复制**

```bash
# 查看公钥内容
cat ~/.ssh/id_ed25519.pub

# SSH 登录到服务器后执行：
mkdir -p ~/.ssh
echo "粘贴公钥内容" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

**Windows 用户（PowerShell）**

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh username@remote_host "cat >> ~/.ssh/authorized_keys"
```

---

## 第三步：配置 VSCode SSH Config

编辑 `~/.ssh/config`（没有则新建）：

```
Host my-server              # 连接别名，随意起
    HostName 192.168.1.100  # 服务器 IP 或域名
    User username           # 登录用户名
    IdentityFile ~/.ssh/id_ed25519  # 私钥路径
```

> Windows 用户私钥路径写法：`IdentityFile C:/Users/YourName/.ssh/id_ed25519`

配置完成后，在 VSCode Remote SSH 插件中选择 `my-server` 即可免密连接。

---

## 常见问题排查

| 问题现象 | 可能原因 | 解决方案 |
|----------|----------|----------|
| 仍然需要输入密码 | 服务器目录权限不正确 | 检查并修复 `~/.ssh` 权限 |
| Permission denied (publickey) | 公钥未正确写入 | 检查 `authorized_keys` 文件内容 |
| 找不到私钥文件 | config 路径配置有误 | 确认 `IdentityFile` 路径与实际一致 |
| Windows 路径问题 | 路径分隔符不正确 | 使用正斜杠 `/` 或双反斜杠 `\\` |

**修复服务器权限：**

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chown -R $USER:$USER ~/.ssh
```

**检查服务器 SSH 服务配置**（`/etc/ssh/sshd_config`）：

```
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
```

修改后重启服务：

```bash
sudo systemctl restart sshd
```

---

## 安全注意事项

- 私钥请妥善保管，切勿上传到 GitHub 等公开平台
- 建议设置 Passphrase，配合 `ssh-agent` 使用兼顾安全与便利
- 定期轮换密钥，废弃的公钥及时从 `authorized_keys` 删除
- 可通过 `AllowUsers` / `DenyUsers` 限制可登录的用户范围