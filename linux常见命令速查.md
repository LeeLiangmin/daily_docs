
# Linux 常用命令速查手册（瑞士军刀版）

> 高频、实用，覆盖日常运维/开发排查场景。按场景分类，可直接搜索关键字使用。

---

## 一、系统 & 硬件信息

### 系统版本 / 内核
```bash
uname -a                # 全部内核信息
uname -r                # 内核版本
uname -m                # 硬件架构（如 x86_64, aarch64）
cat /etc/os-release      # 发行版信息（Ubuntu/CentOS/Debian 等）
lsb_release -a           # 发行版详细信息（部分系统需安装 lsb-release）
hostnamectl              # 主机名 + 系统 + 内核 + 架构 一站式查看
```

### CPU 架构 / 信息
```bash
lscpu                    # CPU 架构、核心数、线程数、主频等（首选）
cat /proc/cpuinfo        # 更详细的每核信息
nproc                    # 当前可用 CPU 核心数
arch                     # 等价于 uname -m，查看架构
```

### 内存
```bash
free -h                  # 内存/交换分区使用情况（人类可读）
cat /proc/meminfo        # 详细内存信息
vmstat 1                 # 每秒刷新的内存/CPU/IO 概览
```

### 磁盘 & 分区
```bash
df -h                    # 各分区磁盘使用率
du -sh *                 # 当前目录下各文件/文件夹大小
du -sh --max-depth=1 /path   # 指定目录下一层大小汇总
lsblk                    # 块设备/分区树状图
fdisk -l                 # 分区详细信息（需 root）
mount | column -t        # 已挂载文件系统列表
```

---

## 二、进程 & 资源监控

```bash
top                       # 实时进程监控
htop                       # top 的增强版（需安装）
ps aux                     # 所有进程快照
ps aux --sort=-%cpu | head # CPU 占用 Top 进程
ps aux --sort=-%mem | head # 内存占用 Top 进程
pidof <进程名>              # 查找进程 PID
kill -9 <PID>               # 强制杀进程
pkill -f <关键字>            # 按名称模糊杀进程
nohup command &             # 后台运行，忽略挂起信号
disown                      # 让后台任务脱离当前 shell
uptime                      # 系统运行时长 + 负载
```

---

## 三、网络

```bash
ip a                        # 查看所有网卡 IP（替代旧版 ifconfig）
ip route                    # 路由表
hostname -I                 # 快速查看本机 IP
curl ifconfig.me             # 查看公网 IP
ping -c 4 目标地址            # 测试连通性
traceroute 目标地址           # 路由跟踪
netstat -tulnp               # 查看监听端口及对应进程（可用 ss 替代）
ss -tulnp                    # netstat 的现代替代，速度更快
lsof -i :端口号                # 查看指定端口被哪个进程占用
curl -I 网址                  # 只看 HTTP 响应头
wget 网址                     # 下载文件
scp 文件 user@host:路径        # 远程拷贝文件
nslookup 域名 / dig 域名        # DNS 查询
```

---

## 四、文件 & 目录操作

```bash
ls -lah                     # 详细列出（含隐藏文件、人类可读大小）
find /path -name "*.log"    # 按文件名查找
find /path -mtime -1        # 查找 1 天内修改过的文件
find /path -size +100M      # 查找大于 100MB 的文件
tree -L 2                   # 树状展示目录结构（需安装）
cp -r 源 目标                # 递归拷贝目录
mv 源 目标                   # 移动/重命名
rm -rf 目标                  # 强制递归删除（谨慎使用）
ln -s 源 软链接名             # 创建软链接
stat 文件名                  # 文件详细元信息
file 文件名                  # 判断文件类型
```

---

## 五、文本处理

```bash
cat 文件                     # 输出全部内容
less 文件                    # 分页查看（q 退出）
head -n 20 文件              # 前 20 行
tail -n 20 文件              # 后 20 行
tail -f 文件                 # 实时追踪日志（最常用）
grep "关键字" 文件            # 查找匹配行
grep -r "关键字" 目录         # 递归查找
grep -n "关键字" 文件         # 显示行号
grep -i "关键字" 文件         # 忽略大小写
awk '{print $1}' 文件        # 按列提取
sed 's/旧/新/g' 文件          # 替换文本
wc -l 文件                   # 统计行数
sort 文件 | uniq -c          # 去重并计数
diff 文件1 文件2              # 比较两个文件差异
cut -d',' -f1 文件            # 按分隔符提取列
```

---

## 六、权限 & 用户

```bash
chmod 755 文件               # 修改权限
chmod +x 脚本.sh             # 添加执行权限
chown user:group 文件        # 修改属主/属组
whoami                       # 当前用户
id                            # 当前用户 UID/GID/组信息
sudo -i                       # 切换到 root 交互 shell
su - 用户名                    # 切换用户
passwd 用户名                  # 修改密码
useradd / userdel 用户名        # 添加/删除用户
usermod -aG 组名 用户名          # 用户加入组
```

---

## 七、压缩 & 打包

```bash
tar -czvf 打包名.tar.gz 目录/     # 打包并 gzip 压缩
tar -xzvf 文件.tar.gz             # 解压
tar -tzvf 文件.tar.gz             # 查看压缩包内容（不解压）
zip -r 打包名.zip 目录/            # zip 压缩
unzip 文件.zip                    # 解压 zip
```

---

## 八、包管理

```bash
# Debian/Ubuntu 系
apt update && apt upgrade    # 更新源 + 升级
apt install <包名>           # 安装
apt remove <包名>            # 卸载
dpkg -l | grep <包名>        # 查询是否已安装

# RHEL/CentOS 系
yum install <包名> / dnf install <包名>
rpm -qa | grep <包名>
```

---

## 九、SSH & SFTP

### SSH 连接
```bash
ssh user@host                     # 基本连接
ssh -p 2222 user@host             # 指定端口
ssh -i ~/.ssh/id_rsa user@host    # 指定私钥登录
ssh user@host command             # 远程执行单条命令后退出
ssh -v user@host                  # 打印调试信息，排查连接问题
ssh -N -L 本地端口:目标host:目标端口 user@跳板机   # 本地端口转发（访问内网服务）
ssh -N -R 远程端口:localhost:本地端口 user@目标host # 远程端口转发（内网穿透）
ssh -N -D 1080 user@host          # 动态端口转发（SOCKS5 代理）
```

### 密钥管理
```bash
ssh-keygen -t ed25519 -C "邮箱备注"   # 生成新密钥对（推荐 ed25519）
ssh-keygen -t rsa -b 4096            # 生成 RSA 4096 位密钥
ssh-copy-id user@host                # 把本地公钥拷贝到远程 authorized_keys
cat ~/.ssh/id_ed25519.pub            # 查看公钥内容
chmod 600 ~/.ssh/id_rsa              # 私钥权限必须收紧，否则 SSH 会拒绝使用
chmod 700 ~/.ssh                     # .ssh 目录权限
```

### 免密登录排查
```bash
ssh -T git@github.com                # 测试是否可用密钥免密（以 GitHub 为例）
cat ~/.ssh/known_hosts | grep host   # 查看是否已记录目标主机指纹
ssh-keygen -R host                   # 清除某主机的旧指纹记录（host key 变化时用）
```

### ~/.ssh/config 免记忆配置（强烈推荐）
```
Host myserver
    HostName 1.2.3.4
    User root
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
```
配置好后可直接 `ssh myserver` 连接，无需再输入 IP/端口/用户名。

### SCP（基于 SSH 的文件拷贝）
```bash
scp 本地文件 user@host:/远程路径/          # 本地 → 远程
scp user@host:/远程文件 本地路径/          # 远程 → 本地
scp -r 本地目录/ user@host:/远程路径/      # 递归拷贝目录
scp -P 2222 文件 user@host:/路径/          # 指定端口（大写 -P）
scp -i ~/.ssh/id_rsa 文件 user@host:/路径/ # 指定密钥
```

### SFTP（交互式安全文件传输）
```bash
sftp user@host                 # 连接
sftp -P 2222 user@host         # 指定端口
sftp -i ~/.ssh/id_rsa user@host # 指定密钥
```
进入交互模式后常用子命令：
```
ls / lls           # 远程 / 本地 列出文件
cd / lcd            # 远程 / 本地 切换目录
pwd / lpwd           # 远程 / 本地 当前路径
get 文件              # 下载单个文件
get -r 目录            # 递归下载目录
put 文件               # 上传单个文件
put -r 目录             # 递归上传目录
mkdir 目录名             # 远程新建目录
rm 文件                 # 删除远程文件
rename 旧名 新名          # 重命名远程文件
bye / exit / quit        # 退出
```

### 常见排查
```bash
ssh -vvv user@host                       # 详细调试日志，定位连接失败原因
sudo systemctl status sshd               # 查看 SSH 服务端状态
sudo tail -f /var/log/auth.log           # 查看 SSH 登录日志（Debian/Ubuntu）
sudo tail -f /var/log/secure             # 查看 SSH 登录日志（CentOS/RHEL）
sshd -T | grep -i port                   # 查看 sshd 生效配置（如监听端口）
```

---

## 十、系统服务 (systemd)

```bash
systemctl status <服务名>     # 查看状态
systemctl start/stop/restart <服务名>
systemctl enable/disable <服务名>   # 开机自启
journalctl -u <服务名> -f      # 实时查看服务日志
journalctl --since "10 min ago"  # 查看近期系统日志
```

---

## 十一、环境变量 & Shell

```bash
env                          # 查看所有环境变量
echo $PATH                   # 查看 PATH
export VAR=value             # 临时设置环境变量
alias ll='ls -lah'           # 设置命令别名
history                      # 历史命令
history | grep 关键字        # 查找历史命令
which 命令名                 # 查看命令路径
type 命令名                  # 判断命令是内建/别名/可执行文件
```

---

## 十二、快捷组合（高频排查场景）

```bash
# 查看某端口占用并杀掉
lsof -i :8080 && kill -9 $(lsof -t -i:8080)

# 查看磁盘占用最大的前 10 个目录
du -ah / 2>/dev/null | sort -rh | head -10

# 实时监控某进程日志
tail -f /var/log/xxx.log | grep --line-buffered "ERROR"

# 快速查看系统整体信息（内核+架构+发行版一步到位）
hostnamectl && lscpu | grep Architecture && free -h && df -h

# 通过跳板机访问内网数据库（本地转发示例）
ssh -N -L 3306:内网DB地址:3306 user@跳板机 &
```

---

## 备注

- `ss` 建议替代 `netstat`，`ip` 建议替代 `ifconfig`，均为现代发行版推荐工具。
- 涉及删除、杀进程、权限修改的命令请务必确认路径/PID 后再执行，尤其是 `rm -rf`。
- 以上命令绝大多数在 Ubuntu/Debian/CentOS/RHEL 上通用，个别工具（如 `htop`、`tree`）需要额外安装。