#!/bin/bash

# setup_server.sh
# QuickLink Server Setup Script
# Usage: sudo ./setup_server.sh

set -e

echo ">>> 开始 QuickLink 服务器端配置..."

# 1. 检查 root 权限
if [ "$EUID" -ne 0 ]; then 
  echo "错误: 请使用 sudo 运行此脚本"
  exit 1
fi

# 2. 获取当前目录 (假设脚本在项目根目录运行)
PROJECT_DIR=$(pwd)
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIST="$PROJECT_DIR/frontend/dist"

echo ">>> 项目目录: $PROJECT_DIR"

# 3. 安装系统依赖
echo ">>> 安装系统依赖 (python3-venv, nginx)..."
apt-get update
apt-get install -y python3-venv python3-pip nginx

# 4. 配置后端环境
echo ">>> 配置后端 Python 环境..."
if [ ! -d "$BACKEND_DIR" ]; then
    echo "错误: 找不到后端目录 $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 安装 Python 依赖
./venv/bin/pip install -r requirements.txt

# 5. 配置 Systemd 服务
echo ">>> 配置 Systemd 服务 (quicklink.service)..."
SERVICE_FILE="/etc/systemd/system/quicklink.service"

cat > $SERVICE_FILE <<EOF
[Unit]
Description=QuickLink Backend Service
After=network.target

[Service]
User=$SUDO_USER
WorkingDirectory=$BACKEND_DIR
ExecStart=$BACKEND_DIR/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 重载并启动服务
systemctl daemon-reload
systemctl enable quicklink
systemctl restart quicklink

echo ">>> 后端服务已启动!"

# 6. 生成 Nginx 配置建议
echo ""
echo "========================================================"
echo ">>> 部署完成! 请手动更新 Nginx 配置"
echo "========================================================"
echo "请将以下内容添加到你的 Nginx 配置文件中 (例如 /etc/nginx/sites-available/default):"
echo "注意: 请确保放在 server { ... } 块内部"
echo ""
echo "    # QuickLink 前端静态文件"
echo "    location /quicklink/ {"
echo "        alias $FRONTEND_DIST/;"
echo "        try_files \$uri \$uri/ /quicklink/index.html;"
echo "    }"
echo ""
echo "    # QuickLink 后端 API 代理"
echo "    location /api/ {"
echo "        proxy_pass http://127.0.0.1:8000/;"
echo "        proxy_set_header Host \$host;"
echo "        proxy_set_header X-Real-IP \$remote_addr;"
echo "        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
echo "        proxy_set_header X-Forwarded-Proto \$scheme;"
echo "    }"
echo ""
echo "    # QuickLink WebSocket 代理"
echo "    location /api/ws/ {"
echo "        proxy_pass http://127.0.0.1:8000/ws/;"
echo "        proxy_http_version 1.1;"
echo "        proxy_set_header Upgrade \$http_upgrade;"
echo "        proxy_set_header Connection \"upgrade\";"
echo "        proxy_set_header Host \$host;"
echo "    }"
echo "========================================================"
echo "修改完成后，请运行: sudo nginx -t && sudo systemctl restart nginx"
