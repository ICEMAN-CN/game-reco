#!/bin/bash

# Game Odyssey 一键启动脚本
# 启动顺序: Embedding 服务 -> Backend API -> Frontend

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Game Odyssey 启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查端口占用
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}警告: 端口 $port ($service) 已被占用${NC}"
        read -p "是否继续? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查端口
check_port 8000 "Embedding 服务"
check_port 8001 "Backend API"
check_port 5173 "Frontend"

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# 1. 启动 Embedding 服务 (端口 8000)
echo -e "\n${GREEN}[1/3] 启动 Embedding 服务 (端口 8000)...${NC}"
cd "$PROJECT_ROOT/scripts"
if [ ! -d "../venv" ]; then
    echo -e "${RED}错误: 未找到虚拟环境，请先创建虚拟环境${NC}"
    exit 1
fi

# 激活虚拟环境并启动 embedding 服务
source ../venv/bin/activate
nohup python3 app.py > "$PROJECT_ROOT/logs/embedding.log" 2>&1 &
EMBEDDING_PID=$!
echo $EMBEDDING_PID > "$PROJECT_ROOT/logs/embedding.pid"
echo -e "${GREEN}Embedding 服务已启动 (PID: $EMBEDDING_PID)${NC}"

# 等待服务启动
sleep 3
if ! curl -s http://127.0.0.1:8000/embed > /dev/null 2>&1; then
    echo -e "${YELLOW}等待 Embedding 服务启动...${NC}"
    sleep 2
fi

# 2. 启动 Backend API (端口 8001)
echo -e "\n${GREEN}[2/3] 启动 Backend API (端口 8001)...${NC}"
cd "$PROJECT_ROOT/backend"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PROJECT_ROOT/logs/backend.pid"
echo -e "${GREEN}Backend API 已启动 (PID: $BACKEND_PID)${NC}"

# 等待服务启动
sleep 3
if ! curl -s http://127.0.0.1:8001/health > /dev/null 2>&1; then
    echo -e "${YELLOW}等待 Backend API 启动...${NC}"
    sleep 2
fi

# 3. 启动 Frontend (端口 5173)
echo -e "\n${GREEN}[3/3] 启动 Frontend (端口 5173)...${NC}"
cd "$PROJECT_ROOT/frontend"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}检测到未安装依赖，正在安装...${NC}"
    if command -v pnpm &> /dev/null; then
        pnpm install
    elif command -v npm &> /dev/null; then
        npm install
    else
        echo -e "${RED}错误: 未找到 pnpm 或 npm${NC}"
        exit 1
    fi
fi

# 启动前端
if command -v pnpm &> /dev/null; then
    nohup pnpm dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
else
    nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
fi
echo $FRONTEND_PID > "$PROJECT_ROOT/logs/frontend.pid"
echo -e "${GREEN}Frontend 已启动 (PID: $FRONTEND_PID)${NC}"

# 等待前端启动
sleep 3

# 保存所有 PID 到总文件
echo "$EMBEDDING_PID" > "$PROJECT_ROOT/logs/pids.txt"
echo "$BACKEND_PID" >> "$PROJECT_ROOT/logs/pids.txt"
echo "$FRONTEND_PID" >> "$PROJECT_ROOT/logs/pids.txt"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}所有服务已启动!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Embedding 服务: ${GREEN}http://localhost:8000${NC}"
echo -e "Backend API:    ${GREEN}http://localhost:8001${NC}"
echo -e "API 文档:       ${GREEN}http://localhost:8001/docs${NC}"
echo -e "Frontend:       ${GREEN}http://localhost:5173${NC}"
echo -e "\n日志文件:"
echo -e "  - Embedding:  ${YELLOW}logs/embedding.log${NC}"
echo -e "  - Backend:    ${YELLOW}logs/backend.log${NC}"
echo -e "  - Frontend:   ${YELLOW}logs/frontend.log${NC}"
echo -e "\n使用 ${YELLOW}./scripts/stop.sh${NC} 停止所有服务"
echo -e "使用 ${YELLOW}./scripts/restart.sh${NC} 重启所有服务"
echo -e "${GREEN}========================================${NC}"
