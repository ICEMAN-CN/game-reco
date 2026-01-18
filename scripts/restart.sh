#!/bin/bash

# Game Odyssey 重启脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}正在重启所有服务...${NC}"

# 先停止
"$SCRIPT_DIR/stop.sh"

# 等待一下确保端口释放
sleep 2

# 再启动
"$SCRIPT_DIR/start.sh"
