#!/bin/bash
# 自动更新并推送脚本
# 每天收盘后运行：获取最新数据 -> 推送到GitHub -> Vercel自动部署

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PY="$PROJECT_DIR/venv/bin/python"

cd "$PROJECT_DIR"

echo "=========================================="
echo "开始每日数据更新..."
echo "=========================================="

# 1. 激活虚拟环境并获取最新数据
echo "[1/3] 获取最新数据..."
"$VENV_PY" "$SCRIPT_DIR/update_data.py"
if [ $? -ne 0 ]; then
    echo "获取数据失败，退出"
    exit 1
fi

# 同步数据到public/data/（用于浏览器动态加载）
mkdir -p "$PROJECT_DIR/public/data"
cp "$PROJECT_DIR/src/data/lixinger_indices.json" "$PROJECT_DIR/public/data/"
cp "$PROJECT_DIR/src/data/000922.json" "$PROJECT_DIR/public/data/" 2>/dev/null || true

# 2. 检查是否有数据变化
echo "[2/3] 检查数据变化..."
cd "$PROJECT_DIR"
git status --short

# 如果没有变化，退出
if [ -z "$(git status --short)" ]; then
    echo "数据无变化，跳过推送"
    exit 0
fi

# 3. 推送到GitHub
echo "[3/3] 推送到GitHub..."
DATE=$(date +"%Y-%m-%d %H:%M")
git add src/data/lixinger_indices.json
git add src/data/000922.json 2>/dev/null || true
git add public/data/lixinger_indices.json
git add public/data/000922.json 2>/dev/null || true
git commit -m "更新数据 - $DATE"
git push origin main

echo "=========================================="
echo "推送完成！Vercel将自动部署..."
echo "=========================================="
