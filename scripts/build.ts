import * as fs from 'fs-extra';
import * as path from 'path';
import { glob } from 'glob';
import chalk from 'chalk';
import { SVGIcons2SVGFontStream } from 'svgicons2svgfont';
import svg2ttf from 'svg2ttf';
import ttf2eot from 'ttf2eot';
import ttf2woff from 'ttf2woff';
import ttf2woff2 from 'ttf2woff2';
import { Readable } from 'stream';
import { Icon, IconsData } from '../src/types';

// 字体配置
const fontName = 'chromana';
const fontId = 'chromana';
const fontFamily = 'Chromana';
const fontWeight = 'normal';
const fontStyle = 'normal';
const cssPrefix = 'cm';

// 路径配置
const srcDir = path.resolve(process.cwd(), 'src');
const distDir = path.resolve(process.cwd(), 'dist');
const iconDir = path.resolve(srcDir, 'icons');

interface GlyphMetadata {
    unicode:   string[];
    name:      string;
    ligatures: string;
}

interface GlyphStream extends Readable {
    metadata?: GlyphMetadata;
}

// 确保目标目录存在
fs.ensureDirSync(distDir);

// Get all SVG icons
console.log(chalk.blue('👀 Searching for SVG icon files...'));
const svgFiles = await glob('**/*.svg', { cwd: iconDir });

if (svgFiles.length === 0) {
    console.log(chalk.yellow('⚠️ No SVG icons found, please add SVG icons to src/icons directory'));
    process.exit(0);
}

console.log(chalk.green(`✓ Found ${svgFiles.length} SVG icons`));
console.log(chalk.blue('🛠 Starting font generation...'));

// Generate SVG font
const generateSVGFont = (): Promise<string> => {
    return new Promise((resolve, reject) => {
        console.log(chalk.blue('→ Generating SVG font...'));

        const fontStream = new SVGIcons2SVGFontStream({
            fontName,
            fontHeight:         1000,
            normalize:          true,
            centerHorizontally: true,
        });

        let svgFontContent = '';

        fontStream
            .on('data', (data: Buffer) => {
                svgFontContent += data.toString();
            })
            .on('end', () => {
                fs.writeFileSync(path.join(distDir, `${fontName}.svg`), svgFontContent);
                console.log(chalk.green('✓ SVG font generation complete'));
                resolve(svgFontContent);
            })
            .on('error', (err: Error) => {
                console.error(chalk.red('× SVG font generation failed'), err);
                reject(err);
            }); // 添加图标到字体
        svgFiles.forEach((filePath, index) => {
            const glyph: GlyphStream = fs.createReadStream(path.join(iconDir, filePath));
            const name = path.basename(filePath, '.svg');

            // Set font Unicode and ligatures
            glyph.metadata = {
                unicode:   [String.fromCharCode(0xE000 + index)],
                name:      name,
                ligatures: name, // Use filename as ligature
            };

            fontStream.write(glyph);
        });

        fontStream.end();
    });
};// 转换为TTF
const generateTTF = (svgFontContent: string): Buffer => {
    console.log(chalk.blue('→ 生成TTF字体...'));

    const ttf = svg2ttf(svgFontContent, {});
    const ttfBuf = Buffer.from(ttf.buffer);

    fs.writeFileSync(path.join(distDir, `${fontName}.ttf`), ttfBuf);
    console.log(chalk.green('✓ TTF font generation complete'));

    return ttfBuf;
};

// Convert to WOFF
const generateWOFF = (ttfBuf: Buffer): void => {
    console.log(chalk.blue('→ Generating WOFF font...'));

    const woffBuf = ttf2woff(new Uint8Array(ttfBuf));
    fs.writeFileSync(path.join(distDir, `${fontName}.woff`), Buffer.from(woffBuf.buffer));

    console.log(chalk.green('✓ WOFF font generation complete'));
};

// Convert to WOFF2
const generateWOFF2 = (ttfBuf: Buffer): void => {
    console.log(chalk.blue('→ Generating WOFF2 font...'));

    try {
        const woff2Buf = ttf2woff2(ttfBuf);
        fs.writeFileSync(path.join(distDir, `${fontName}.woff2`), woff2Buf);
        console.log(chalk.green('✓ WOFF2 font generation complete'));
    } catch (err) {
        console.warn(chalk.yellow('⚠️ WOFF2 font generation failed, may be incompatible with Bun runtime'), err);
        console.log(chalk.blue('Trying to use WOFF format as alternative...'));
    }
};

// Convert to EOT (for compatibility with older IE browsers)
const generateEOT = (ttfBuf: Buffer): void => {
    console.log(chalk.blue('→ Generating EOT font...'));

    const eotBuf = ttf2eot(new Uint8Array(ttfBuf));
    fs.writeFileSync(path.join(distDir, `${fontName}.eot`), Buffer.from(eotBuf.buffer));

    console.log(chalk.green('✓ EOT font generation complete'));
};

// Generate CSS file
const generateCSS = (): void => {
    console.log(chalk.blue('→ Generating CSS file...'));

    const cssContent = `@font-face {
  font-family: '${fontFamily}';
  src: url('./${fontName}.eot');
  src: url('./${fontName}.eot?#iefix') format('embedded-opentype'),
       url('./${fontName}.woff2') format('woff2'),
       url('./${fontName}.woff') format('woff'),
       url('./${fontName}.ttf') format('truetype'),
       url('./${fontName}.svg#${fontId}') format('svg');
  font-weight: ${fontWeight};
  font-style: ${fontStyle};
}

.${cssPrefix} {
  font-family: '${fontFamily}';
  font-weight: ${fontWeight};
  font-style: ${fontStyle};
  display: inline-block;
  line-height: 1;
  text-rendering: auto;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-variant-ligatures: common-ligatures;
  text-transform: none;
}

/* Icon class list */
${svgFiles.map(file => {
    const name = path.basename(file, '.svg');
    return `.${cssPrefix}-${name}::before { content: "${name}"; }`;
}).join('\n')}
`;

    fs.writeFileSync(path.join(distDir, `${fontName}.css`), cssContent);
    console.log(chalk.green('✓ CSS file generation complete'));
};

// Generate icon mapping JSON file
const generateIconsJSON = (): void => {
    console.log(chalk.blue('→ Generating icon mapping JSON file...'));

    const icons: Icon[] = svgFiles.map(file => {
        const name = path.basename(file, '.svg');
        return {
            name,
            class:    `${cssPrefix}-${name}`,
            ligature: name,
        };
    });

    const iconsData: IconsData = { icons };

    fs.writeFileSync(
        path.join(distDir, 'icons.json'),
        JSON.stringify(iconsData, null, 2),
    );

    console.log(chalk.green('✓ Icon mapping JSON file generation complete'));
};

// Main execution function
async function build(): Promise<void> {
    try {
        console.time('Generation complete, total time');

        // Generate various font formats
        const svgFontContent = await generateSVGFont();
        const ttfBuf = generateTTF(svgFontContent);

        generateWOFF(ttfBuf);
        generateWOFF2(ttfBuf);
        generateEOT(ttfBuf);

        // Generate CSS and JSON
        generateCSS();
        generateIconsJSON();

        console.timeEnd('Generation complete, total time');
        console.log(chalk.green('🎉 All font files generated successfully!'));
    } catch (err) {
        console.error(chalk.red('Error occurred during build:'), err);
        process.exit(1);
    }
}

// 执行构建
build();
