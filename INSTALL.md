# Chromana 使用说明

本文档介绍如何使用pyproject.toml安装和使用Chromana。

## 安装指南

### 使用pip安装

```bash
# 从源代码安装
git clone https://github.com/Sunchy321/chromana.git
cd chromana
pip install -e .
```

### 使用虚拟环境（推荐）

```bash
# 克隆仓库
git clone https://github.com/Sunchy321/chromana.git
cd chromana

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或者在Windows上:
# .venv\Scripts\activate

# 安装依赖
pip install -e .
```

也可以使用提供的安装脚本：

```bash
bash scripts/install.sh
```

## 构建字体

激活虚拟环境后，可以使用以下命令构建字体：

```bash
python scripts/build.py
```

## 预览字体

构建完成后，可以启动本地预览服务器：

```bash
python scripts/serve.py
```

然后在浏览器中访问 http://localhost:4213/

## 清理构建文件

如需清理临时文件和构建产物，可以运行：

```bash
python scripts/clean.py
```
