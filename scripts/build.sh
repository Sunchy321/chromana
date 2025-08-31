#!/usr/bin/env bash

# 项目根目录
PROJECT_DIR=$(dirname "$(dirname "$0")")
VENV_DIR="$PROJECT_DIR/.venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_DIR" ]; then
    echo "虚拟环境不存在，请先运行 ./scripts/install_dependencies.sh"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 运行Python脚本
echo "运行字体构建脚本..."
python "$PROJECT_DIR/scripts/build.py" "$@"

# 输出完成信息
echo "字体构建完成！"
