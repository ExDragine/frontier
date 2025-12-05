#!/bin/bash

set -e  # 任何命令失败时立即退出
export PYTHON_JIT=1
export PYTHON_GIL=0

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检测并安装 uv
if ! command -v uv &> /dev/null; then
    echo "检测到未安装 uv，正在安装..."
    if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
        echo "❌ uv 安装失败"
        exit 1
    fi
    # 添加 uv 到 PATH
    export PATH="$HOME/.local/bin:$PATH"
    # 刷新 shell 路径缓存
    hash -r
    echo "✓ uv 安装完成"
else
    echo "✓ uv 已安装"
fi

# 尝试更新 uv 自身并升级 uv 管理的 Python（容错处理）
echo "尝试执行: uv self update 和 uv python upgrade（若支持）..."
if command -v uv &> /dev/null; then
    if ! uv self update; then
        echo "⚠️ uv self update 失败或不支持该命令，继续执行..."
    else
        echo "✓ uv 已自更新"
    fi

    if ! uv python upgrade; then
        echo "⚠️ uv python upgrade 失败或不支持该命令，继续执行..."
    else
        echo "✓ uv 管理的 Python 升级完成"
    fi
fi

# 检测并创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "检测到不存在 .venv，正在执行 uv sync..."
    if ! uv sync; then
        echo "❌ uv sync 失败"
        exit 1
    fi
    echo "✓ .venv 创建完成"
else
    echo "✓ .venv 已存在"
fi

# 激活虚拟环境
source .venv/bin/activate

echo "✓ 环境准备完成，启动主程序..."
echo ""

# loop to restart
while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始新一轮同步和运行..."
    
    if ! uv sync --upgrade --no-install-project; then
        echo "⚠️ uv sync 警告，继续执行..."
    fi
    
    if ! playwright install chromium; then
        echo "⚠️ playwright install 警告，继续执行..."
    fi
    
    if ! nb run; then
        echo "❌ nb run 失败，5秒后重试..."
    fi
    
    echo "等待 5 秒后重新启动..."
    sleep 5
done
