# 部署指南 (Deployment Guide)

本指南将帮助你将 QuickLink 部署到已运行 Nginx 的云服务器上，并与现有的个人主页共存。
我们将使用 **路径区分** 的方式，让 QuickLink 运行在 `http://<YOUR_IP>/quicklink/` 下。

## 自动化部署 (推荐)

我为你准备了两个自动化脚本，你可以根据情况选择。

### 选项 A: 首次部署 (初始化服务器)
如果你是第一次部署，或者服务器上还没有配置 Python 环境和 Systemd 服务，请使用 `setup_server.sh`。
参考上文的 "服务器运行" 步骤。

### 选项 B: 快速更新部署 (CI/CD 风格)
如果你已经完成了首次部署，后续只是想更新代码 (前端或后端)，可以使用本地的 Node.js 脚本一键部署。

**前提**: 
1. 本地安装了 Node.js。
2. 本地可以通过 SSH 免密登录服务器 (或者配置了 SSH Key)。
3. 服务器 Hostname 为 `taoserver` (或者在运行脚本时指定)。

**运行方式**:
在本地项目根目录下运行：

```bash
# 默认部署到 taoserver
node script/deploy_quicklink.mjs

# 或者指定 host
node script/deploy_quicklink.mjs --host <YOUR_SERVER_IP>
```

**脚本功能**:
1. 自动构建前端 (`npm run build`).
2. 通过 SSH/Rsync 将前端 `dist` 和后端 `backend` 代码同步到服务器 `/opt/quicklink` 目录。
3. 远程执行 `pip install` 更新依赖。
4. 远程重启 `quicklink` 服务。

---

## 手动部署 (Manual Deployment)

以下是手动步骤，如果你想了解细节或脚本运行失败，可以参考。

确保你的服务器已安装：
- Python 3.10+
- Node.js 18+ (仅用于构建，如果本地构建则不需要)
- Nginx

## 2. 前端构建 (Frontend)

在本地或服务器上执行以下命令生成静态文件：

```bash
cd frontend
npm install
npm run build
```

构建完成后，会生成 `dist` 目录。将此目录上传到服务器，例如 `/var/www/quicklink/dist`。

## 3. 后端部署 (Backend)

将 `backend` 目录上传到服务器，例如 `/var/www/quicklink/backend`。

### 安装依赖

```bash
cd /var/www/quicklink/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 运行后端

推荐使用 `supervisor` 或 `systemd` 来保持后端运行。这里使用简单的 `systemd` 示例：

创建 `/etc/systemd/system/quicklink.service`:

```ini
[Unit]
Description=QuickLink Backend Service
After=network.target

[Service]
User=root
WorkingDirectory=/var/www/quicklink/backend
ExecStart=/var/www/quicklink/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start quicklink
sudo systemctl enable quicklink
```

## 4. Nginx 配置

编辑你的 Nginx 配置文件 (通常在 `/etc/nginx/sites-available/default` 或 `/etc/nginx/nginx.conf`)。
在现有的 `server { ... }` 块中添加以下内容：

```nginx
server {
    listen 80;
    server_name YOUR_IP_OR_DOMAIN; # 保持原有的 server_name

    # 原有的个人主页配置 (假设)
    location / {
        # ... existing config ...
    }

    # QuickLink 前端静态文件
    location /quicklink/ {
        alias /var/www/quicklink/dist/;
        try_files $uri $uri/ /quicklink/index.html;
    }

    # QuickLink 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # QuickLink WebSocket 代理
    location /api/ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 5. 重启 Nginx

```bash
sudo nginx -t
sudo systemctl restart nginx
```

## 6. 访问

现在你可以通过以下地址访问：
- 个人主页: `http://<YOUR_IP>/`
- QuickLink: `http://<YOUR_IP>/quicklink/`
