# Chromana

A font representing TCG (Trading Card Game) symbols with ligature support.

## Features

- Generate multiple font formats (SVG, TTF, WOFF, WOFF2, EOT) from SVG icons
- Support ligature functionality to display icons directly using their names
- Written in TypeScript with complete type definitions
- Using Bun as a high-performance JavaScript/TypeScript runtime
- Provides standard CSS classes for easy web usage
- Clean and intuitive API with demo interface

## 安装

### 使用npm

```bash
npm install chromana --save
```

### 或者直接下载

下载本项目的 `dist` 文件夹中的文件。

## 使用方法

### 1. 引入CSS

```html
<link rel="stylesheet" href="path/to/chromana.css">
```

### 2. 使用CSS类

```html
<i class="cm cm-circle"></i>
<i class="cm cm-square"></i>
<i class="cm cm-triangle"></i>
```

### 3. 使用连字(Ligature)

```html
<span class="cm">circle</span>
<span class="cm">square</span>
<span class="cm">triangle</span>
```

## 自定义图标

1. 将SVG图标放到 `src/icons` 目录下（文件名将作为图标名称和连字）
2. 运行构建命令：

```bash
npm run build
```

## 开发

### 环境要求

- [Bun](https://bun.sh/) - 高性能 JavaScript 运行时

### 安装依赖

```bash
bun install
```

### 构建字体

```bash
bun run build
```

### 启动演示服务器

```bash
bun run start
```

### 开发模式（热重载）

```bash
bun run dev
```

访问 http://localhost:3000 查看演示页面。

### 类型检查

```bash
bun run type-check
```

## 支持的图标

目前支持以下图标：

- circle - 圆形
- square - 方形
- triangle - 三角形
- diamond - 钻石形
- cross - 十字
- hourglass - 沙漏

## 许可证

MIT
