# Chromana

A font representing TCG (Trading Card Game) symbols with ligature support.

## 特性

- 将SVG图标转换为带有连字(ligature)功能的彩色字体(COLR格式)
- 支持多种字体格式输出(TTF, WOFF, WOFF2)
- 为每个图标集生成独立的字体和演示页面
- 可以合并多个图标集为一个统一的字体
- 提供标准CSS类和简洁的使用方法
- 使用Bun作为高性能JavaScript/TypeScript运行时

## 目录结构

```
/
├── data/               # 图标数据
│   └── magic/          # 魔法风云会数据
│       └── symbology.json
├── icons/              # SVG图标文件
│   └── magic/          # 魔法风云会图标
│       ├── config.toml # 图标配置文件
│       └── scryfall/   # SVG文件
├── scripts/            # 构建脚本
│   ├── build.py        # 字体构建脚本
│   ├── build.sh        # 构建脚本封装
│   ├── install.sh      # 安装依赖
│   └── serve.ts        # 开发服务器
└── dist/               # 构建输出
    ├── chromana.ttf    # 合并字体
    ├── chromana.woff
    ├── chromana.woff2
    ├── chromana.css    # 合并字体CSS
    ├── chromana.html   # 合并字体演示
    └── magic/          # 魔法风云会字体
        ├── Magic-0.1.0.ttf
        ├── Magic-0.1.0.woff
        ├── Magic-0.1.0.woff2
        ├── magic.css   # CSS
        └── magic.html  # 演示页面
```

## 配置文件格式

每个图标集在`icons/[图标集名称]`目录下都需要有一个`config.toml`文件，格式如下：

```toml
name = "图标集显示名称"
code = "图标集代码"
version = "版本号"

[[symbols]]
name = "符号名称"
path = "SVG文件相对路径"
ligature = "{连字字符串}"

# 更多符号...
```

例如：
```toml
name = "Magic: The Gathering"
code = "magic"
version = "0.1.0"

[[symbols]]
name="white"
path="scryfall/W.svg"
ligature="{W}"

[[symbols]]
name="blue"
path="scryfall/U.svg"
ligature="{U}"
```

## 字体生成工具

### 安装依赖

```bash
# 安装Python依赖
npm run establish
# 或直接运行
bash scripts/install.sh
```

这将安装以下依赖：
- fonttools
- toml
- brotli
- nanoemoji

### 构建字体

```bash
# 构建所有字体
npm run build:fonts
# 或
python3 scripts/build.py

# 构建特定图标集的字体
npm run build:fonts:magic
# 或
python3 scripts/build.py magic
```

### 查看演示

```bash
# 启动演示服务器
npm run serve:fonts
# 或
bun scripts/serve.ts
```

然后在浏览器中访问 `http://localhost:4213`

## 添加新的图标集

1. 创建图标集目录和配置文件：

```bash
mkdir -p icons/your_icon_set
touch icons/your_icon_set/config.toml
```

2. 添加SVG图标到目录中：

```bash
mkdir -p icons/your_icon_set/svgs
# 复制SVG文件到此目录
```

3. 编辑配置文件，添加符号定义：

```toml
name = "Your Icon Set"
code = "your_icon_set"
version = "0.1.0"

[[symbols]]
name="icon1"
path="svgs/icon1.svg"
ligature="{ICON1}"

[[symbols]]
name="icon2"
path="svgs/icon2.svg"
ligature="{ICON2}"
```

4. 构建字体：

```bash
npm run build:fonts
```

## 使用生成的字体

### 1. 引入CSS

```html
<link rel="stylesheet" href="path/to/your_icon_set.css">
```

### 2. 使用图标

```html
<!-- 使用连字功能 -->
<i class="your_icon_set-icon">{ICON1}</i>
<i class="your_icon_set-icon">{ICON2}</i>
```

## 技术细节

- 使用nanoemoji将SVG转换为COLR格式的彩色字体
  - 通过glyphmap文件定义图标和连字的映射
  - 支持彩色字体格式(COLR v1)
- 使用fonttools进行字体格式转换和处理
  - 转换为多种网页字体格式(TTF、WOFF、WOFF2)
- 通过Bun提供演示服务器
  - 实时预览所有字体和图标
  - 自动生成CSS和演示页面
