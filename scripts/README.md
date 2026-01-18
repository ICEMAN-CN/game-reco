# Game Odyssey 启动脚本说明

## 脚本列表

- `start.sh` - 一键启动所有服务
- `stop.sh` - 停止所有服务
- `restart.sh` - 重启所有服务

## 使用方法

### 启动所有服务

```bash
cd /Users/iceman/wdy/faithruit/git/game-odyssey
./scripts/start.sh
```

启动顺序：
1. Embedding 服务 (端口 8000)
2. Backend API (端口 8001)
3. Frontend (端口 5173)

### 停止所有服务

```bash
./scripts/stop.sh
```

### 重启所有服务

```bash
./scripts/restart.sh
```

## 服务地址

启动成功后，可以访问：

- **Embedding 服务**: http://localhost:8000
- **Backend API**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs
- **Frontend**: http://localhost:5173

## 日志文件

所有服务的日志保存在 `logs/` 目录：

- `logs/embedding.log` - Embedding 服务日志
- `logs/backend.log` - Backend API 日志
- `logs/frontend.log` - Frontend 日志

## 注意事项

1. 确保已创建并激活虚拟环境（`venv/` 目录）
2. 确保已安装前端依赖（`frontend/node_modules/`）
3. 如果端口被占用，脚本会提示是否继续
4. 使用 `stop.sh` 可以安全停止所有服务

## 手动启动（参考）

如果脚本无法正常工作，可以手动启动：

### 1. Embedding 服务
```bash
cd scripts
source ../venv/bin/activate
python3 app.py
```

### 2. Backend API
```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend
```bash
cd frontend
pnpm dev
# 或
npm run dev
```
