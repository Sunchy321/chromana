#!/usr/bin/env bash

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "Python 3 未安装，请先安装Python 3"
    exit 1
fi

# 项目根目录
PROJECT_DIR=$(dirname "$(dirname "$0")")
VENV_DIR="$PROJECT_DIR/.venv"

# 创建虚拟环境
echo "正在创建Python虚拟环境..."
python3 -m venv "$VENV_DIR"

# 激活虚拟环境
echo "正在激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 安装必要的依赖
echo "正在安装必要的Python依赖..."
pip install --upgrade pip
pip install fonttools nanoemoji toml brotli

echo "依赖安装完成！"
echo "虚拟环境已创建在 $VENV_DIR"
echo "要使用此环境，请运行:"
echo "npm run build      # 构建所有字体"
echo "npm run serve      # 启动预览服务器"
echo ""
echo "或者直接使用以下命令:"
echo "source $VENV_DIR/bin/activate"
echo "python scripts/build.py  # 构建所有字体"
echo "bun scripts/serve.ts     # 启动预览服务器"
