#!/bin/bash

# Game Odyssey 停止脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS_DIR="$PROJECT_ROOT/logs"

echo -e "${YELLOW}正在停止所有服务...${NC}"

# 停止 Embedding 服务
if [ -f "$LOGS_DIR/embedding.pid" ]; then
    EMBEDDING_PID=$(cat "$LOGS_DIR/embedding.pid")
    if ps -p $EMBEDDING_PID > /dev/null 2>&1; then
        echo -e "停止 Embedding 服务 (PID: $EMBEDDING_PID)..."
        kill $EMBEDDING_PID 2>/dev/null || true
        sleep 1
        # 如果还在运行，强制杀死
        if ps -p $EMBEDDING_PID > /dev/null 2>&1; then
            kill -9 $EMBEDDING_PID 2>/dev/null || true
        fi
        echo -e "${GREEN}Embedding 服务已停止${NC}"
    fi
    rm -f "$LOGS_DIR/embedding.pid"
fi

# 停止 Backend API
if [ -f "$LOGS_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOGS_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "停止 Backend API (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        sleep 1
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi
        echo -e "${GREEN}Backend API 已停止${NC}"
    fi
    rm -f "$LOGS_DIR/backend.pid"
fi

# 停止 Frontend
if [ -f "$LOGS_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOGS_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "停止 Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
        sleep 1
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID 2>/dev/null || true
        fi
        echo -e "${GREEN}Frontend 已停止${NC}"
    fi
    rm -f "$LOGS_DIR/frontend.pid"
fi

# 清理 PID 文件
rm -f "$LOGS_DIR/pids.txt"

# 额外检查：通过端口杀死进程（防止 PID 文件丢失的情况）
for port in 8000 8001 5173; do
    PID=$(lsof -ti :$port 2>/dev/null || true)
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}检测到端口 $port 仍有进程运行 (PID: $PID)，正在停止...${NC}"
        kill $PID 2>/dev/null || true
        sleep 1
        if ps -p $PID > /dev/null 2>&1; then
            kill -9 $PID 2>/dev/null || true
        fi
    fi
done

echo -e "\n${GREEN}所有服务已停止${NC}"
