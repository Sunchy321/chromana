import { join, resolve } from 'path';
import { statSync, readdirSync } from 'fs';
import chalk from 'chalk';

const port = 4213;
const rootDir = resolve(import.meta.dir, '..');
const distDir = join(rootDir, 'dist');
const demoDir = join(rootDir, 'demo');

// 检查dist目录是否存在
try {
    const distStat = statSync(distDir);
    if (!distStat.isDirectory()) {
        console.error(chalk.red('Error: dist is not a directory'));
        process.exit(1);
    }
} catch (err) {
    console.error(chalk.red('Error: dist directory does not exist. Please run `bun run build` first.'));
    process.exit(1);
}

console.log(chalk.cyan('Starting development server...'));
console.log(chalk.green('Server directories:'));
console.log(chalk.green(`- dist: ${distDir}`));
console.log(chalk.green(`- demo: ${demoDir}`));

// 构建可用字体集列表
const fontSets = [];
try {
    // 查找所有HTML演示文件
    const distFiles = readdirSync(distDir);
    for (const file of distFiles) {
        if (file.endsWith('.html')) {
            const fontCode = file.replace('.html', '');
            fontSets.push({
                code:    fontCode,
                demoUrl: `/fonts/${fontCode}`,
            });
        }
    }

    // 检查子目录
    for (const item of readdirSync(distDir)) {
        const itemPath = join(distDir, item);
        const itemStat = statSync(itemPath);
        if (itemStat.isDirectory()) {
            fontSets.push({
                code:    item,
                demoUrl: `/fonts/${item}`,
            });
        }
    }
} catch (err) {
    console.log(chalk.yellow('Warning: Failed to build font sets list.'), err);
}

// 生成字体索引页面
function generateFontIndexHtml() {
    let fontListHtml = '';

    for (const font of fontSets) {
        fontListHtml += `
            <li>
                <a href="${font.demoUrl}" class="font-link">
                    <span class="font-code">${font.code}</span>
                </a>
            </li>`;
    }

    return `<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chromana Font Collection</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                margin: 0;
                padding: 40px 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            h1 {
                text-align: center;
                margin-bottom: 40px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            .font-list {
                list-style: none;
                padding: 0;
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 16px;
            }
            .font-link {
                display: block;
                text-decoration: none;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                transition: all 0.3s ease;
            }
            .font-link:hover {
                transform: translateY(-3px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .font-code {
                font-size: 18px;
                font-weight: 500;
                color: #2c5282;
            }
            .note {
                margin-top: 40px;
                padding: 15px;
                background-color: #e6fffa;
                border-left: 4px solid #38b2ac;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Chromana Font Collection</h1>

            <ul class="font-list">
                ${fontListHtml}
            </ul>

            <div class="note">
                <p><strong>注意：</strong> 点击上方链接查看各个字体的演示页面。每个字体都提供了TTF、WOFF和WOFF2格式。</p>
            </div>
        </div>
    </body>
    </html>`;
}

Bun.serve({
    port,
    async fetch(req) {
        const url = new URL(req.url);
        const path = url.pathname;

        // 默认路径
        if (path === '/') {
            // 如果是根路径，首先尝试提供演示目录的index.html
            try {
                const demoIndex = join(demoDir, 'index.html');
                const stat = statSync(demoIndex);
                if (stat.isFile()) {
                    const file = Bun.file(demoIndex);
                    return new Response(file);
                }
            } catch (err) {
                // 如果demo目录的index.html不存在，提供字体索引页面
                return new Response(generateFontIndexHtml(), {
                    headers: { 'Content-Type': 'text/html' },
                });
            }
        }

        // 字体演示路径
        if (path.startsWith('/fonts/')) {
            const fontCode = path.slice(7); // 去掉'/fonts/'

            // 尝试找到相应的HTML文件
            let htmlPath;

            if (fontCode.includes('/')) {
                // 如果是子目录路径，如/fonts/magic/W.svg
                const relativePath = fontCode;
                htmlPath = join(distDir, relativePath);
            } else {
                // 如果是字体代码，如/fonts/magic
                htmlPath = join(distDir, `${fontCode}.html`);
                if (!statSync(htmlPath, { throwIfNoEntry: false })) {
                    // 如果根目录没有对应的HTML，检查是否是子目录
                    const fontDir = join(distDir, fontCode);
                    if (statSync(fontDir, { throwIfNoEntry: false })?.isDirectory()) {
                        // 如果是子目录，查找子目录中的HTML文件
                        try {
                            const dirFiles = readdirSync(fontDir);
                            const htmlFile = dirFiles.find(f => f.endsWith('.html'));
                            if (htmlFile) {
                                htmlPath = join(fontDir, htmlFile);
                            }
                        } catch (err) {
                            // 忽略错误
                        }
                    }
                }
            }

            if (htmlPath && statSync(htmlPath, { throwIfNoEntry: false })?.isFile()) {
                const file = Bun.file(htmlPath);
                return new Response(file);
            }
        }

        let filePath;

        // 如果路径以/dist开头，则从dist目录中提供文件
        if (path.startsWith('/dist/')) {
            filePath = join(rootDir, path);
        } else if (path.startsWith('/fonts/')) {
            // 字体资源路径 /fonts/magic.ttf -> /dist/magic.ttf
            const fontPath = path.slice(7); // 去掉'/fonts/'
            filePath = join(distDir, fontPath);
        } else {
            // 否则从demo目录提供文件
            filePath = join(demoDir, path);
        }

        try {
            const stat = statSync(filePath);
            if (stat.isFile()) {
                const file = Bun.file(filePath);
                return new Response(file);
            }
        } catch (err) {
            // 文件不存在
            console.log(chalk.yellow(`404: ${path}`));
            return new Response('Not Found', { status: 404 });
        }

        return new Response('Not Found', { status: 404 });
    },
});

console.log(chalk.green(`Server running at http://localhost:${port}`));
console.log(chalk.green('Press Ctrl+C to stop'));
