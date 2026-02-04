# QuickLink - 仿 Discord 文字聊天应用

本项目是一个基于 Python (FastAPI) 和 Vue 3 的纯文字聊天 Web 应用，实现了类似于 Discord 的三栏式布局和实时通信功能。

## 目录结构

```
QuickLink/
├── backend/            # Python 后端
│   ├── main.py         # 入口文件 & API & WebSocket
│   ├── models.py       # 数据库模型
│   ├── schemas.py      # 数据校验模型
│   ├── crud.py         # 数据库操作
│   ├── database.py     # 数据库连接
│   ├── auth.py         # 认证逻辑
│   └── requirements.txt
├── frontend/           # Vue3 前端
│   ├── src/
│   │   ├── components/ # 组件 (ServerList, ChannelList, ChatArea)
│   │   ├── stores/     # Pinia 状态管理 (Auth, Chat)
│   │   ├── views/      # 页面 (Login, Layout)
│   │   └── ...
│   └── ...
└── README.md
```

## 环境要求

- **Python**: 3.8+
- **Node.js**: 16+
- **npm**: 8+

## 快速启动指南

### 1. 启动后端 (Backend)

1. 进入 `backend` 目录：
   ```bash
   cd backend
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动服务器：
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
   后端将在 `http://localhost:8000` 运行。API 文档可在 `http://localhost:8000/docs` 查看。

### 2. 启动前端 (Frontend)

1. 打开新的终端窗口，进入 `frontend` 目录：
   ```bash
   cd frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
   通常会运行在 `http://localhost:5173`。请按控制台提示访问。

## 功能使用说明

1. **注册/登录**：打开前端页面，点击 "Register" 注册账号，然后登录。
2. **创建服务器**：点击左侧栏底部的绿色 "+" 号，输入名称创建服务器。
3. **创建频道**：选择一个服务器后，点击中间栏 "TEXT CHANNELS" 旁边的 "+" 号创建频道。
4. **发送消息**：在右侧聊天框输入消息并回车。
5. **实时通信**：打开两个浏览器窗口登录不同账号，在同一频道发送消息，可看到实时推送。

## 核心技术点

- **后端**：FastAPI, WebSocket, SQLAlchemy (SQLite), JWT Auth
- **前端**：Vue 3, Pinia, Vue Router, Element Plus, Native WebSocket
- **设计**：Flexbox 三栏布局，参考 Discord 配色

## 注意事项

- 数据库使用 SQLite (`quicklink.db`)，文件会自动生成在 `backend` 目录下。
- WebSocket 连接需要用户登录后获取 Token (当前简化为 User ID 绑定)。
