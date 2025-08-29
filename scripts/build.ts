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
import { Icon, IconsData, GameConfig } from '../src/types';
import * as toml from '@iarna/toml';

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

// Ensure target directory exists
fs.ensureDirSync(distDir);

// Get all games (directories with config.toml)
console.log(chalk.blue('👀 Looking for game directories...'));
const gameDirs = await glob('**/config.toml', { cwd: iconDir })
    .then(files => files.map(file => path.dirname(file)));

if (gameDirs.length === 0) {
    console.log(chalk.yellow('⚠️ No game directories found with config.toml'));
}

// Include root SVGs as "default" game
gameDirs.push(''); // Empty string for root directory

console.log(chalk.green(`✓ Found ${gameDirs.length} game directories (including root)`));

// Get all SVG icons
console.log(chalk.blue('👀 Searching for SVG icon files...'));
const svgFiles = await glob('**/*.svg', { cwd: iconDir });

if (svgFiles.length === 0) {
    console.log(chalk.yellow('⚠️ No SVG icons found, please add SVG icons to src/icons directory'));
    process.exit(0);
}

console.log(chalk.green(`✓ Found ${svgFiles.length} SVG icons`));
console.log(chalk.blue('🛠 Starting font generation...'));

// Group SVGs by game directory
const gameIcons = new Map<string, string[]>();
svgFiles.forEach(file => {
    const dirName = path.dirname(file);
    if (dirName === '.') {
        // Root directory SVGs
        if (!gameIcons.has('')) {
            gameIcons.set('', []);
        }
        gameIcons.get('')!.push(file);
    } else {
        // Game directory SVGs
        const gameDir = gameDirs.find(dir => dir !== '' && dirName.startsWith(dir));
        if (gameDir) {
            if (!gameIcons.has(gameDir)) {
                gameIcons.set(gameDir, []);
            }
            gameIcons.get(gameDir)!.push(file);
        }
    }
});

// Load game configs
const gameConfigs = new Map<string, GameConfig>();

for (const gameDir of gameDirs) {
    if (gameDir === '') {
        // Default game
        gameConfigs.set('', {
            name:            fontFamily,
            ligature_prefix: cssPrefix,
        });
    } else {
        // Read config.toml
        try {
            const configPath = path.join(iconDir, gameDir, 'config.toml');
            const configContent = fs.readFileSync(configPath, 'utf8');
            const config = toml.parse(configContent) as unknown as GameConfig;
            gameConfigs.set(gameDir, config);
        } catch (_err) {
            console.warn(chalk.yellow(`⚠️ Failed to parse config.toml for ${gameDir}, using defaults`));
            gameConfigs.set(gameDir, {
                name:            gameDir,
                ligature_prefix: gameDir.toLowerCase().replace(/[^a-z0-9]/g, ''),
            });
        }
    }
}

// Generate SVG font for a specific game or all games
const generateSVGFont = (gameDir = '', files = svgFiles): Promise<string> => {
    return new Promise((resolve, reject) => {
        const gameConfig = gameConfigs.get(gameDir)!;
        const outputName = gameDir ? `${fontName}-${path.basename(gameDir)}` : fontName;

        console.log(chalk.blue(`→ Generating SVG font for ${gameConfig.name || outputName}...`));

        const fontStream = new SVGIcons2SVGFontStream({
            fontName:           outputName,
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
                fs.writeFileSync(path.join(distDir, `${outputName}.svg`), svgFontContent);
                console.log(chalk.green(`✓ SVG font generation complete for ${gameConfig.name || outputName}`));
                resolve(svgFontContent);
            })
            .on('error', (err: Error) => {
                console.error(chalk.red(`× SVG font generation failed for ${gameConfig.name || outputName}`), err);
                reject(err);
            });

        // 添加图标到字体
        files.forEach((filePath, index) => {
            const glyph: GlyphStream = fs.createReadStream(path.join(iconDir, filePath));
            const name = path.basename(filePath, '.svg');
            const ligature = gameConfig.ligature_prefix ? `${gameConfig.ligature_prefix}-${name}` : name;

            // Set font Unicode and ligatures
            glyph.metadata = {
                unicode:   [String.fromCharCode(0xE000 + index)],
                name:      name,
                ligatures: ligature, // Use prefix + filename as ligature
            };

            fontStream.write(glyph);
        });

        fontStream.end();
    });
};// 转换为TTF
const generateTTF = (svgFontContent: string, outputName: string = fontName): Buffer => {
    console.log(chalk.blue(`→ Generating TTF font for ${outputName}...`));

    const ttf = svg2ttf(svgFontContent, {});
    const ttfBuf = Buffer.from(ttf.buffer);

    fs.writeFileSync(path.join(distDir, `${outputName}.ttf`), ttfBuf);
    console.log(chalk.green(`✓ TTF font generation complete for ${outputName}`));

    return ttfBuf;
};

// Convert to WOFF
const generateWOFF = (ttfBuf: Buffer, outputName: string = fontName): void => {
    console.log(chalk.blue(`→ Generating WOFF font for ${outputName}...`));

    const woffBuf = ttf2woff(new Uint8Array(ttfBuf));
    fs.writeFileSync(path.join(distDir, `${outputName}.woff`), Buffer.from(woffBuf.buffer));

    console.log(chalk.green(`✓ WOFF font generation complete for ${outputName}`));
};

// Convert to WOFF2
const generateWOFF2 = (ttfBuf: Buffer, outputName: string = fontName): void => {
    console.log(chalk.blue(`→ Generating WOFF2 font for ${outputName}...`));

    try {
        const woff2Buf = ttf2woff2(ttfBuf);
        fs.writeFileSync(path.join(distDir, `${outputName}.woff2`), woff2Buf);
        console.log(chalk.green(`✓ WOFF2 font generation complete for ${outputName}`));
    } catch (err) {
        console.warn(chalk.yellow(`⚠️ WOFF2 font generation failed for ${outputName}, may be incompatible with Bun runtime`), err);
        console.log(chalk.blue('Trying to use WOFF format as alternative...'));
    }
};

// Convert to EOT (for compatibility with older IE browsers)
const generateEOT = (ttfBuf: Buffer, outputName: string = fontName): void => {
    console.log(chalk.blue(`→ Generating EOT font for ${outputName}...`));

    const eotBuf = ttf2eot(new Uint8Array(ttfBuf));
    fs.writeFileSync(path.join(distDir, `${outputName}.eot`), Buffer.from(eotBuf.buffer));

    console.log(chalk.green(`✓ EOT font generation complete for ${outputName}`));
};

// Generate CSS file for a specific game or all games
const generateCSS = (gameDir = '', files = svgFiles): void => {
    const gameConfig = gameConfigs.get(gameDir)!;
    const outputName = gameDir ? `${fontName}-${path.basename(gameDir)}` : fontName;
    const outputFamily = gameConfig.name ? `${fontFamily} ${gameConfig.name}` : fontFamily;
    const outputId = gameDir ? `${fontId}-${path.basename(gameDir)}` : fontId;
    const outputPrefix = gameConfig.ligature_prefix || cssPrefix;

    console.log(chalk.blue(`→ Generating CSS file for ${outputFamily}...`));

    const cssContent = `@font-face {
  font-family: '${outputFamily}';
  src: url('./${outputName}.eot');
  src: url('./${outputName}.eot?#iefix') format('embedded-opentype'),
       url('./${outputName}.woff2') format('woff2'),
       url('./${outputName}.woff') format('woff'),
       url('./${outputName}.ttf') format('truetype'),
       url('./${outputName}.svg#${outputId}') format('svg');
  font-weight: ${fontWeight};
  font-style: ${fontStyle};
}

.${outputPrefix} {
  font-family: '${outputFamily}';
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
${files.map(file => {
    const name = path.basename(file, '.svg');
    const ligature = gameConfig.ligature_prefix ? `${gameConfig.ligature_prefix}-${name}` : name;
    return `.${outputPrefix}-${name}::before { content: "${ligature}"; }`;
}).join('\n')}
`;

    fs.writeFileSync(path.join(distDir, `${outputName}.css`), cssContent);
    console.log(chalk.green(`✓ CSS file generation complete for ${outputFamily}`));
};

// Generate icon mapping JSON file for a specific game or all games
const generateIconsJSON = (gameDir = '', files: string[] = svgFiles): void => {
    const gameConfig = gameConfigs.get(gameDir)!;
    const outputName = gameDir ? `${fontName}-${path.basename(gameDir)}` : fontName;
    const outputPrefix = gameConfig.ligature_prefix || cssPrefix;
    const gameName = gameConfig.name || path.basename(gameDir) || fontFamily;

    console.log(chalk.blue(`→ Generating icon mapping JSON file for ${gameName}...`));

    const icons: Icon[] = files.map(file => {
        const name = path.basename(file, '.svg');
        const ligature = gameConfig.ligature_prefix ? `${gameConfig.ligature_prefix}-${name}` : name;
        return {
            name,
            class: `${outputPrefix}-${name}`,
            ligature,
            game:  gameDir ? gameName : undefined,
        };
    });

    const iconsData: IconsData = { icons };

    fs.writeFileSync(
        path.join(distDir, `${outputName}-icons.json`),
        JSON.stringify(iconsData, null, 2),
    );

    console.log(chalk.green(`✓ Icon mapping JSON file generation complete for ${gameName}`));
};

// Generate all font formats for a specific game
async function buildGameFont(gameDir: string, files: string[]): Promise<void> {
    try {
        const outputName = gameDir ? `${fontName}-${path.basename(gameDir)}` : fontName;
        const gameName = gameConfigs.get(gameDir)!.name || path.basename(gameDir) || fontFamily;

        console.log(chalk.blue(`🎮 Building font for ${gameName}...`));

        // Generate various font formats
        const svgFontContent = await generateSVGFont(gameDir, files);
        const ttfBuf = generateTTF(svgFontContent, outputName);

        generateWOFF(ttfBuf, outputName);
        generateWOFF2(ttfBuf, outputName);
        generateEOT(ttfBuf, outputName);

        // Generate CSS and JSON
        generateCSS(gameDir, files);
        generateIconsJSON(gameDir, files);

        console.log(chalk.green(`✅ Font for ${gameName} generated successfully!`));
    } catch (err) {
        console.error(chalk.red(`Error occurred during build for ${gameDir || 'default game'}:`), err);
    }
}

// Generate a combined font with all icons
async function buildCombinedFont(): Promise<void> {
    try {
        console.log(chalk.blue('🔄 Building combined font with all icons...'));

        // Generate various font formats
        const svgFontContent = await generateSVGFont('', svgFiles);
        const ttfBuf = generateTTF(svgFontContent);

        generateWOFF(ttfBuf);
        generateWOFF2(ttfBuf);
        generateEOT(ttfBuf);

        // Generate CSS and JSON
        generateCSS('', svgFiles);
        generateIconsJSON('', svgFiles);

        console.log(chalk.green('✅ Combined font generated successfully!'));
    } catch (err) {
        console.error(chalk.red('Error occurred during combined build:'), err);
        process.exit(1);
    }
}

// Main execution function
async function build(): Promise<void> {
    try {
        console.time('Generation complete, total time');

        // Build font for each game directory
        for (const [gameDir, files] of gameIcons.entries()) {
            if (files.length > 0) {
                await buildGameFont(gameDir, files);
            }
        }

        // Build combined font with all icons
        await buildCombinedFont();

        console.timeEnd('Generation complete, total time');
        console.log(chalk.green('🎉 All font files generated successfully!'));
    } catch (err) {
        console.error(chalk.red('Error occurred during build:'), err);
        process.exit(1);
    }
}

// 执行构建
build();
