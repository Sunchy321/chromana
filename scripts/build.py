#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import subprocess
import glob
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from read_config import read_config, Symbol
from typing import Dict, List, Tuple, Optional, TypedDict

# 项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ICONS_DIR = PROJECT_ROOT / "icons"
DIST_DIR = PROJECT_ROOT / "dist"
DEMO_DIR = PROJECT_ROOT / "demo"
TEMP_DIR = PROJECT_ROOT / "temp"
BUILD_DIR = PROJECT_ROOT / "build"

# 确保输出目录存在
DIST_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# 检查nanoemoji是否安装
def check_dependencies():
    try:
        subprocess.run(["nanoemoji", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("nanoemoji not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "nanoemoji"], check=True)

    # 检查字体转换工具
    try:
        import fontTools
        print(f"fontTools {fontTools.__version__} found.")
    except ImportError:
        print("fonttools not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "fonttools"], check=True)

    # 检查是否支持WOFF2
    try:
        import brotli
        print("brotli found, WOFF2 conversion will be available.")
    except ImportError:
        print("brotli not found. WOFF2 conversion may not be available.")
        print("To enable WOFF2 support, install brotli: pip install brotli")

class SingleSymbol(TypedDict):
    name: str
    variant: str
    style: str
    path: str
    ligatures: list[str]

# 准备nanoemoji参数
class NanoEmojiParams(TypedDict):
    font_name: str
    output_file: str
    symbols: list[SingleSymbol]

def prepare_nanoemoji_params(
    font_name: str,
    base_dir: Path,
    output_path: Path,
    symbols: List[Symbol]
) -> NanoEmojiParams:
    # 基本信息
    output_file = str(output_path / f"{font_name}.ttf")

    valid_symbols: List[SingleSymbol] = []

    for sym in symbols:
        name = sym["name"]
        ligatures = sym["ligature"]
        base_file = sym["file"]

        valid_symbols.append(SingleSymbol(
            name=name,
            variant="default",
            style="default",
            path=os.path.join(base_dir, "default", base_file),
            ligatures=ligatures
        ))

        for var, file in sym["variant"].items():
            valid_symbols.append(SingleSymbol(
                name=name,
                variant=var,
                style="default",
                path=os.path.join(base_dir, "default", file),
                ligatures=ligatures
            ))

        for style, dir in sym["style"].items():
            valid_symbols.append(SingleSymbol(
                name=name,
                variant="default",
                style=style,
                path=os.path.join(base_dir, style, base_file),
                ligatures=ligatures
            ))

            for var, file in sym["variant"].items():
                valid_symbols.append(SingleSymbol(
                    name=name,
                    variant=var,
                    style=style,
                    path=os.path.join(base_dir, dir, file),
                    ligatures=ligatures
                ))

    return {
        "font_name": font_name,
        "output_file": output_file,
        "symbols": valid_symbols
    }

GlyphMapping = Dict[str, Tuple[str, List[str], str, str]]

# 使用nanoemoji生成基本字体
def build_nanoemoji_font(params: NanoEmojiParams) -> tuple[Optional[Path], Optional[GlyphMapping]]:
    font_name = params["font_name"]
    symbols = params["symbols"]

    if not symbols:
        print(f"Error: No valid symbols found for {font_name}")
        return None, None

    print(f"Building font {font_name} with {len(symbols)} icons")

    # 创建临时目录，用于存放重命名的SVG文件
    temp_svg_dir = TEMP_DIR / "svgs"
    temp_svg_dir.mkdir(exist_ok=True)

    # 用于存放临时SVG文件路径
    temp_svgs = []
    # 用于存储码点与字形名称的映射
    glyph_mappings: GlyphMapping = {}

    # 为每个SVG创建一个临时副本，文件名格式符合nanoemoji的要求
    for i, sym in enumerate(symbols):
        name = sym["name"]
        variant = sym["variant"]
        style = sym["style"]
        svg = sym["path"]
        ligatures = sym["ligatures"]

        # 使用私有区域码点 (Private Use Area)
        codepoint = 0xE000 + i
        hex_codepoint = f"{codepoint:04x}"

        # 创建符合nanoemoji预期的文件名格式: emoji_uXXXX.svg
        temp_filename = f"emoji_u{hex_codepoint}.svg"
        temp_svg_path = temp_svg_dir / temp_filename

        # 预处理SVG文件并复制到临时位置
        preprocess_svg(svg, temp_svg_path)
        temp_svgs.append(str(temp_svg_path))

        # 存储码点与字形名称的映射
        glyph_mappings[hex_codepoint] = (name, ligatures, variant, style)

    print(f"Created {len(temp_svgs)} temporary SVG files with Unicode codepoints")

    # 创建一个临时的配置文件
    build_dir = BUILD_DIR

    # nanoemoji默认输出为build/Font.ttf，我们将记录这个路径
    default_output = build_dir / "Font.ttf"

    # 构建命令行 - 第一阶段：创建基本字体，不包含连字功能
    cmd_basic = [
        "nanoemoji",
        "--family", font_name,
        "--color_format", "glyf_colr_0",
        "--output_file", str(default_output),
        *temp_svgs
    ]

    # 执行命令创建基本字体
    print(f"Step 1: Executing nanoemoji to create basic font:")
    print(f"{' '.join(cmd_basic[:6])}... (and {len(temp_svgs)} SVG files)")

    try:
        subprocess.run(cmd_basic, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running nanoemoji for basic font: {e}")
        try:
            result = subprocess.run(cmd_basic, capture_output=True, text=True)
            print(f"Standard output: {result.stdout[:500]}..." if len(result.stdout) > 500 else result.stdout)
            print(f"Standard error: {result.stderr[:500]}..." if len(result.stderr) > 500 else result.stderr)
        except Exception as e2:
            print(f"Error capturing output: {e2}")
        return None, None

    # 检查基本字体是否创建成功
    if not os.path.exists(default_output):
        print(f"Error: Basic font file not created at expected location: {default_output}")
        return None, None

    print(f"Successfully created basic font: {default_output}")

    return default_output, glyph_mappings

# 创建字符到标准名称的映射字典
char_name_map = {
    # 基本字母保持原样
    # 'a'-'z' 和 'A'-'Z' 不需要映射，直接使用

    # 数字映射到命名
    '0': "zero",
    '1': "one",
    '2': "two",
    '3': "three",
    '4': "four",
    '5': "five",
    '6': "six",
    '7': "seven",
    '8': "eight",
    '9': "nine",

    # 标点符号
    '.': "period",
    ',': "comma",
    ':': "colon",
    ';': "semicolon",
    '!': "exclam",
    '?': "question",

    # 引号和撇号
    "'": "quotesingle",
    '"': "quotedbl",
    '`': "grave",

    # 括号和大括号
    '(': "parenleft",
    ')': "parenright",
    '[': "bracketleft",
    ']': "bracketright",
    '{': "braceleft",
    '}': "braceright",
    '<': "less",
    '>': "greater",

    # 其他常用符号
    '#': "numbersign",
    '$': "dollar",
    '%': "percent",
    '&': "ampersand",
    '*': "asterisk",
    '+': "plus",
    '-': "hyphen",
    '/': "slash",
    '\\': "backslash",
    '=': "equal",
    '@': "at",
    '^': "asciicircum",
    '_': "underscore",
    '|': "bar",
    '~': "asciitilde",
    ' ': "space",

    '½': "onehalf",
    '∞': "uni221E",
}

# 为小写字母和大写字母添加映射（这些通常可以直接使用，但为了统一我们也添加映射）
for c in range(ord('a'), ord('z') + 1):
    char_name_map[chr(c)] = chr(c)
for c in range(ord('A'), ord('Z') + 1):
    char_name_map[chr(c)] = chr(c)

def liga_to_string(ligature: str, glyph_name: str) -> Optional[str]:
    if not ligature or len(ligature) < 1:
        return None

    # 将每个字符转换为FEA中的正确表示
    processed_chars = []

    # 处理每个字符
    for c in ligature:
        # 检查字符是否在映射字典中
        if c in char_name_map:
            processed_chars.append(char_name_map[c])
        # 其他字符使用Unicode命名
        else:
            char_code = ord(c)
            if char_code <= 0xFFFF:
                # BMP字符用4位十六进制表示
                processed_chars.append(f"uni{char_code:04X}")
            else:
                # 非BMP字符用5-6位十六进制表示
                processed_chars.append(f"u{char_code:06X}")

    # 检查是否有成功处理的字符
    if not processed_chars:
        print(f"Warning: No valid characters in ligature for {glyph_name}")
        return None

    # 创建FEA规则字符串，字符之间用空格分隔
    liga_string = " ".join(processed_chars)

    return liga_string

# 为字体添加连字功能
def add_ligatures_to_font(font_file: Path, output_file: str, glyph_mappings: GlyphMapping):
    print(f"Adding ligatures to font: {font_file}")

    # 步骤1：创建连字规则列表
    variants: list[str] = []
    styles: list[str] = []

    liga_list: list[tuple[str, str]] = []
    salt_list: list[tuple[str, list[str]]] = []
    ss0x_lists: list[list[tuple[str, str]]] = []

    # 为每个连字添加替换规则
    added_rules = 0
    skipped_rules = 0

    for (glyph_name, ligatures, variant, style) in glyph_mappings.values():
        if variant != 'default':
            variants.append(variant)

        if style != 'default' and style not in styles:
            styles.append(style)
            ss0x_lists.append([])

    groups: dict[str, tuple[list[str], dict[str, dict[str, str]]]] = {}

    for hex_codepoint, (glyph_name, ligatures, variant, style) in glyph_mappings.items():
        if glyph_name not in groups:
            groups[glyph_name] = (ligatures, {})

        if style not in groups[glyph_name][1]:
            groups[glyph_name][1][style] = { variant : hex_codepoint }
        else:
            groups[glyph_name][1][style][variant] = hex_codepoint

    for glyph_name, (ligatures, var_group) in groups.items():
        # default style
        default_variant_dict = var_group["default"]

        default_hex = default_variant_dict["default"]

        # default variant
        for ligature in ligatures:
            try:
                liga_string = liga_to_string(ligature, glyph_name)

                if not liga_string:
                    continue

                unicode_name = f"uni{int(default_hex, 16):04X}"
                liga_list.append((liga_string, unicode_name))
                added_rules += 1

            except Exception as e:
                print(f"Error processing ligature for {glyph_name}: {e}")
                skipped_rules += 1

        if len(default_variant_dict) > 1:
            variant_hexes = [
                hex_codepoint for variant, hex_codepoint in default_variant_dict.items() if variant != "default"
            ]

            salt_list.append((default_hex, variant_hexes))

        for style, style_variant_dict in var_group.items():
            if style == "default":
                continue

            style_index = styles.index(style)
            ss0x_list = ss0x_lists[style_index]

            for variant, hex_codepoint in style_variant_dict.items():
                original_hex = default_variant_dict[variant]

                ss0x_list.append((original_hex, f"uni{int(hex_codepoint, 16):04X}"))

    # 步骤2：创建FEA文件以支持连字功能
    fea_file = TEMP_DIR / f"{os.path.basename(output_file)}.fea"

    fea_content = [
        "languagesystem DFLT dflt;",
        "",
    ]

    if len(liga_list) > 0:
        fea_content.extend(["feature liga {"])

        for (liga_string, unicode_name) in liga_list:
            fea_content.append(f"  sub {liga_string} by {unicode_name};")

    fea_content.extend(["} liga;", ""])

    if len(salt_list) > 0:
        fea_content.append("feature salt {  # Stylistic Alternates")

        for (base_hex, alt_hexes) in salt_list:
            base_name = f"uni{int(base_hex, 16):04X}"
            alt_names = [f"uni{int(h, 16):04X}" for h in alt_hexes]
            alt_list = ", ".join(alt_names)
            fea_content.append(f"  sub {base_name} by [{alt_list}];")

        fea_content.append("} salt;")
        fea_content.append("")

    for i, ss0x_list in enumerate(ss0x_lists):
        if len(ss0x_list) < 1:
            continue

        fea_content.append(f"feature ss0{i+1} {{  # Stylistic Set {i+1} ({styles[i]})")

        for (original_hex, alt_name) in ss0x_list:
            original_name = f"uni{int(original_hex, 16):04X}"
            fea_content.append(f"  sub {original_name} by {alt_name};")

        fea_content.append(f"}} ss0{i+1};")
        fea_content.append("")

    # 写入FEA文件
    with open(fea_file, "w") as f:
        f.write("\n".join(fea_content))

    print(f"Created feature file: {fea_file}")

    # 步骤3：使用FontTools添加连字功能
    try:
        from fontTools.ttLib import TTFont
        from fontTools.feaLib.builder import addOpenTypeFeatures
        import re

        # 读取基本字体
        print(f"Step 2: Adding ligature features to the font")
        font = TTFont(font_file)

        # 获取字体中所有可用的字形名称
        available_glyphs = set(font.getGlyphOrder())
        print(f"Font contains {len(available_glyphs)} glyphs")

        # 使用TTX临时导出字体，用于后面添加缺失字形
        ttx_temp_file = str(TEMP_DIR / "temp_font.ttx")
        print(f"Exporting font to TTX format: {ttx_temp_file}")
        font.saveXML(ttx_temp_file)

        # 检查并修复FEA文件，找出所有需要添加的缺失字形
        with open(fea_file, "r") as f:
            fea_content = f.read()

        # 使用正则表达式找出所有引用的字形名称
        pattern = r'sub (.*?) by ([^;]+);'
        matches = re.findall(pattern, fea_content)

        # 收集所有需要添加的字形
        missing_glyphs = set()

        INPUT_GLYPHS = {
            "braceleft": 0x007B, "braceright": 0x007D, "slash": 0x002F,
            "onehalf": 0x00BD, "uni221E": 0x221E,
            "zero": 0x30, "one": 0x31, "two": 0x32, "three": 0x33, "four": 0x34,
            "five": 0x35, "six": 0x36, "seven": 0x37, "eight": 0x38, "nine": 0x39,
            # Letters A–Z
            **{ chr(cp): cp for cp in range(0x41, 0x5B) }
        }

        # Prepare input glyphs
        for gname, cp in INPUT_GLYPHS.items():
            def add_empty_input_glyph(font: TTFont, name: str, advance=0):
                if name in font["glyf"].glyphs: return
                from fontTools.ttLib.tables._g_l_y_f import Glyph
                g = Glyph(); g.numberOfContours = 0
                g.xMin = g.yMin = g.xMax = g.yMax = 0
                font["glyf"].glyphs[name] = g
                font["hmtx"].metrics[name] = (advance, 0)
                order = font.getGlyphOrder(); order.append(name); font.setGlyphOrder(order)

            add_empty_input_glyph(font, gname, advance=0)

        def add_mapping_to_unicode_cmaps(font: TTFont, mapping: dict[int,str]):
            cmap = font["cmap"]
            for st in cmap.tables:
                if st.platformID == 0 or (st.platformID == 3 and st.platEncID in (1,10)):
                    for cp, g in mapping.items():
                        if cp not in st.cmap:
                            st.cmap[cp] = g

        add_mapping_to_unicode_cmaps(font, {cp: name for name, cp in INPUT_GLYPHS.items()})

        # 所有字形都应该已经存在，直接使用原始FEA文件
        print(f"Total rules found in original FEA file: {len(matches)}")

        # 添加OpenType特性，使用原始FEA文件
        print(f"Adding OpenType features from {fea_file}")
        addOpenTypeFeatures(font, str(fea_file), tables=["GSUB"])

        # 保存带有连字功能的字体
        font_path = Path(font_file)
        enhanced_output = font_path.with_name(f"{os.path.basename(output_file)}")
        font.save(enhanced_output)
        print(f"Saved enhanced font with ligatures to: {enhanced_output}")

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 复制到指定输出位置
        shutil.copy2(enhanced_output, output_file)
        print(f"Copied font to final location: {output_file}")

        return True
    except Exception as e:
        print(f"Error adding ligature features: {e}")
        return False

def convert_fonts(ttf_path):
    from fontTools.ttLib import TTFont

    base_path = Path(ttf_path).with_suffix("")
    woff_path = f"{base_path}.woff"
    woff2_path = f"{base_path}.woff2"

    print(f"Converting {ttf_path} to WOFF and WOFF2 formats...")

    # 加载TTF字体
    try:
        font = TTFont(ttf_path)

        # 保存为WOFF
        print(f"Saving WOFF format to {woff_path}")
        font.flavor = "woff"
        font.save(woff_path)

        # 尝试保存为WOFF2
        try:
            print(f"Saving WOFF2 format to {woff2_path}")
            font.flavor = "woff2"
            font.save(woff2_path)
            has_woff2 = True
        except Exception as e:
            print(f"Error saving to WOFF2 format: {e}")
            print("This may happen if the woff2 Python module is not installed.")
            print("You can install it with: pip install brotli")
            has_woff2 = False

    except Exception as e:
        print(f"Error converting font: {e}")
        return {"ttf": ttf_path, "woff": None, "woff2": None}

    return {
        "ttf": ttf_path,
        "woff": woff_path,
        "woff2": woff2_path if has_woff2 else None
    }

# 生成CSS
def generate_css(font_name, font_files, font_code):
    css = f"""/* {font_name} Icon Font */
@font-face {{
  font-family: '{font_name}';
  src: url('../dist/{font_code}/{os.path.basename(font_files["woff2"])}') format('woff2'),
       url('../dist/{font_code}/{os.path.basename(font_files["woff"])}') format('woff'),
       url('../dist/{font_code}/{os.path.basename(font_files["ttf"])}') format('truetype');
  font-weight: normal;
  font-style: normal;
}}

.{font_code}-output {{
  font-family: 'Chromana-magic';
  word-break: break-word;
}}

.{font_code}-icon {{
  font-family: '{font_name}';
  font-weight: normal;
  font-style: normal;
  font-size: 24px;  /* 默认图标大小 */
  display: inline-block;
  line-height: 1;
  text-transform: none;
  letter-spacing: normal;
  word-wrap: normal;
  white-space: nowrap;
  direction: ltr;

  /* Support for all WebKit browsers. */
  -webkit-font-smoothing: antialiased;
  /* Support for Safari and Chrome. */
  text-rendering: optimizeLegibility;
  /* Support for Firefox. */
  -moz-osx-font-smoothing: grayscale;
  /* Support for IE. */
  font-feature-settings: 'liga';
}}
"""
    css_path = DEMO_DIR / f"{font_code}.css"
    with open(css_path, "w") as f:
        f.write(css)

    return css_path

# 生成示例HTML
def generate_html(font_name, font_code, symbols, css_path, categories=None):
    # 创建分类名称映射，用于显示友好的分类名称
    category_display_names = {}
    category_order = []  # 用于保持分类的顺序
    if categories:
        for category in categories:
            category_name = category.get("name", "")
            display_name = category.get("display_name", category_name.replace("-", " ").title())
            if category_name:
                category_display_names[category_name] = display_name
                category_order.append(category_name)

    # 分类符号，便于后续按类别展示
    categorized_symbols = {}
    for symbol in symbols:
        name = symbol["name"]
        ligature = symbol["ligature"]
        category = symbol.get("category", "default")
        overflow = symbol.get("overflow", False)

        if category not in categorized_symbols:
            categorized_symbols[category] = []

        categorized_symbols[category].append({
            "name": name,
            "ligature": ligature,
            "overflow": overflow
        })

    # 生成各类别的HTML
    category_sections = ""

    # 处理所有分类
    all_categories = []

    # 首先添加配置中指定顺序的分类
    for category in category_order:
        if category in categorized_symbols:
            all_categories.append(category)

    # 然后添加其他没有在配置中指定的分类
    for category in categorized_symbols.keys():
        if category not in all_categories:
            all_categories.append(category)

    # 根据分类顺序生成HTML
    for category in all_categories:
        category_symbols = categorized_symbols[category]
        symbols_html = ""

        for symbol in category_symbols:
            name = symbol["name"]
            ligature = symbol["ligature"]

            # 处理多个连字的情况
            if isinstance(ligature, list):
                primary_ligature = ligature[0]  # 使用第一个连字作为主显示
                all_ligatures = ", ".join(ligature)  # 所有连字用逗号分隔显示
            else:
                primary_ligature = ligature
                all_ligatures = ligature

            # 检查是否为宽字符（如1000000等）
            wide_char_class = ""

            if symbol["overflow"]:  # 根据名称或字符长度判断
                wide_char_class = " wide-icon"

            symbols_html += f"""
        <div class="icon-item{wide_char_class}">
          <i class="{font_code}-icon icon-display">{primary_ligature}</i>
          <div class="icon-name">{name}</div>
          <div class="icon-code">{all_ligatures}</div>
        </div>"""        # 使用配置中的显示名称，或者格式化为标题格式
        category_title = category_display_names.get(
            category,
            category.replace('_', ' ').replace('-', ' ').title()
        )

        category_sections += f"""
      <div class="symbol-category">
        <h3 class="category-title">{category_title}</h3>
        <div class="icons-grid">
          {symbols_html}
        </div>
      </div>"""

    # 如果没有分类，则直接显示所有符号
    if not categorized_symbols:
        symbols_html = ""
        for symbol in symbols:
            name = symbol["name"]
            ligature = symbol["ligature"]

            # 处理多个连字的情况
            if isinstance(ligature, list):
                primary_ligature = ligature[0]  # 使用第一个连字作为主显示
                all_ligatures = ", ".join(ligature)  # 所有连字用逗号分隔显示
            else:
                primary_ligature = ligature
                all_ligatures = ligature

            symbols_html += f"""
        <div class="icon-item">
          <i class="{font_code}-icon icon-display">{primary_ligature}</i>
          <div class="icon-name">{name}</div>
          <div class="icon-code">{all_ligatures}</div>
        </div>"""

        category_sections = f"""
      <div class="symbol-category">
        <h3 class="category-title">所有符号</h3>
        <div class="icons-grid">
          {symbols_html}
        </div>
      </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{font_name} 符号展示</title>
  <link rel="stylesheet" href="./style.css">
  <link rel="stylesheet" href="./{os.path.basename(css_path)}">
  <script src="./action.js"></script>
</head>
<body>
  <div class="container">
    <h1>{font_name} 符号展示</h1>

    <!-- 连字测试工具 -->
    <section class="section ligature-test">
      <h2>连字可用性测试</h2>
      <div class="test-controls">
        <input type="text" id="testInput" class="test-input" placeholder="输入连字代码以测试">
        <div class="font-size-control">
          <label for="fontSize">字体大小:</label>
          <input type="range" id="fontSize" min="12" max="72" value="24">
          <span id="fontSizeDisplay">24px</span>
        </div>
        <button id="clearButton" class="test-button">清空</button>
      </div>
      <div id="testOutput" class="test-output {font_code}-output"></div>
      <p>提示: 输入符号代码来测试连字功能。</p>
    </section>

    <!-- 符号展示 -->
    <section class="section">
      <h2>符号展示</h2>
      {category_sections}
    </section>
  </div>
</body>
</html>
"""
    html_path = DEMO_DIR / f"{font_code}.html"
    with open(html_path, "w") as f:
        f.write(html)

    return html_path

# 预处理SVG文件，修复ID重复等问题
def preprocess_svg(svg_path, temp_svg_path):
    """
    预处理SVG文件，修复一些常见问题：
    1. 重复的元素ID
    2. 不兼容的元素
    """
    import re
    from xml.dom import minidom

    try:
        # 使用minidom解析SVG文件
        dom = minidom.parse(svg_path)

        # 获取所有带有id属性的元素
        elements_with_ids = {}
        # 遍历所有可能有id属性的元素类型
        for elem_type in ['path', 'g', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon']:
            for elem in dom.getElementsByTagName(elem_type):
                if elem.hasAttribute('id'):
                    elem_id = elem.getAttribute('id')
                    if elem_id not in elements_with_ids:
                        elements_with_ids[elem_id] = []
                    elements_with_ids[elem_id].append(elem)

        # 修复重复ID问题
        for elem_id, elems in elements_with_ids.items():
            if len(elems) > 1:
                for i, elem in enumerate(elems[1:], 1):
                    new_id = f"{elem_id}_{i}"
                    elem.setAttribute('id', new_id)

        # 写入修改后的SVG
        with open(temp_svg_path, 'w', encoding='utf-8') as f:
            # 使用xml.dom.minidom生成的字符串包含XML声明，我们需要手动添加SVG DOCTYPE
            svg_content = dom.toxml()
            # 如果需要添加DOCTYPE（可选）
            svg_content = svg_content.replace('<?xml version="1.0" ?>',
                                             '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
            f.write(svg_content)

        return True
    except Exception as e:
        print(f"Error preprocessing SVG {svg_path}: {e}")
        # 如果出错，直接复制原文件
        shutil.copy2(svg_path, temp_svg_path)
        return False

# 处理单个图标集
def process_icon_set(icon_dir):
    icon_dir_path = Path(icon_dir)
    config_path = icon_dir_path / "config.toml"

    if not config_path.exists():
        print(f"No config.toml found in {icon_dir_path}, skipping...")
        return None

    print(f"Processing icon set: {icon_dir_path.name}")

    # 读取配置
    config = read_config(config_path)
    font_name = f'Chromana-{config["code"]}'
    font_code = config["code"]
    version = config["version"]
    symbols = config["symbols"]
    categories = config.get("categories", [])

    print(f"Found {len(symbols)} symbols in {font_name}")

    # 创建输出目录
    font_dist_dir = DIST_DIR / font_code
    font_dist_dir.mkdir(exist_ok=True)

    # 准备nanoemoji参数
    nanoemoji_params = prepare_nanoemoji_params(
        font_name,
        icon_dir_path,
        font_dist_dir,
        symbols
    )

    # 生成TTF - 内联替代build_font_with_nanoemoji的调用
    # 第一步：生成基本字体
    font_file, glyph_mappings = build_nanoemoji_font(nanoemoji_params)

    success = False

    if font_file is not None and glyph_mappings is not None:
        # 第二步：添加连字功能
        success = add_ligatures_to_font(font_file, nanoemoji_params["output_file"], glyph_mappings)

    # TTF路径
    ttf_path = font_dist_dir / f"{font_name}.ttf"

    # 转换为其他格式
    if success and ttf_path.exists():
        font_files = convert_fonts(str(ttf_path))

        # 生成CSS
        css_path = generate_css(font_name, font_files, font_code)

        # 生成示例HTML
        html_path = generate_html(font_name, font_code, symbols, css_path, categories)

        print(f"Generated font files for {font_name}:")
        for fmt, path in font_files.items():
            if path:
                print(f"  - {fmt}: {path}")
        print(f"  - CSS: {css_path}")
        print(f"  - HTML demo: {html_path}")

        return {
            "name": font_name,
            "code": font_code,
            "version": version,
            "files": font_files,
            "css": css_path,
            "html": html_path,
            "symbols": symbols,
            "categories": categories
        }
    else:
        print(f"Error: Failed to generate TTF font for {font_name}")
        return None

# 合并所有字体
def merge_fonts(font_results):
    if not font_results:
        print("No fonts to merge")
        return

    print("Merging all fonts...")

    # 创建合并字体的配置
    merged_font_name = "Chromana-All"
    merged_font_code = "chromana"

    all_symbols = []
    glyph_index = 0

    # 收集所有图标
    for font in font_results:
        for symbol in font["symbols"]:
            # 复制SVG文件到临时目录
            orig_svg_path = Path(ICONS_DIR) / font["code"] / symbol["path"]
            temp_svg_path = TEMP_DIR / f"{font['code']}_{symbol['name']}.svg"
            shutil.copy2(orig_svg_path, temp_svg_path)

            # 添加到合并列表
            all_symbols.append({
                "name": f"{font['code']}_{symbol['name']}",
                "path": str(temp_svg_path),
                "ligature": symbol["ligature"],
                "original_font": font["code"]
            })
            glyph_index += 1

    # 准备合并字体的nanoemoji参数
    svg_files = {}
    merged_symbols = []

    for idx, symbol in enumerate(all_symbols):
        name = symbol["name"]
        path = symbol["path"]
        ligature = symbol["ligature"]

        # 添加到符号列表
        merged_symbols.append({
            "name": name,
            "path": path,
            "ligature": ligature
        })

        # 收集SVG路径
        svg_files[name] = path

    # 准备nanoemoji参数
    merged_params = prepare_nanoemoji_params(
        merged_font_name,
        ICONS_DIR,  # 不需要图标目录
        DIST_DIR,
        merged_symbols
    )

    # 生成合并字体
    # 第一步：生成基本字体
    font_file, glyph_mappings = build_nanoemoji_font(merged_params)
    success = False

    if font_file is not None and glyph_mappings is not None:
        # 第二步：添加连字功能
        success = add_ligatures_to_font(font_file, merged_params["output_file"], glyph_mappings)

    # 转换为其他格式
    ttf_path = DIST_DIR / f"{merged_font_code}.ttf"
    if success and ttf_path.exists():
        merged_font_files = convert_fonts(str(ttf_path))

        # 创建分类的符号列表，按原始字体分组
        grouped_symbols = {}
        for symbol in all_symbols:
            font_code = symbol["original_font"]
            if font_code not in grouped_symbols:
                grouped_symbols[font_code] = []
            grouped_symbols[font_code].append(symbol)

        # 生成CSS
        merged_css_path = generate_css(merged_font_name, merged_font_files, merged_font_code)

        # 生成示例HTML，按原始字体分组显示
        merged_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{merged_font_name} Icon Demo</title>
  <link rel="stylesheet" href="./{os.path.basename(merged_css_path)}">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      margin: 0;
      padding: 20px;
      background-color: #f5f5f5;
    }}
    h1, h2 {{
      color: #333;
    }}
    h1 {{
      text-align: center;
      margin-bottom: 20px;
    }}
    h2 {{
      margin-top: 40px;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 1px solid #ddd;
    }}
    .icons-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
      gap: 16px;
      max-width: 1200px;
      margin: 0 auto;
    }}
    .icon-item {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: white;
      padding: 16px 8px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      text-align: center;
      transition: all 0.3s ease;
    }}
    .icon-item:hover {{
      transform: translateY(-3px);
      box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }}
    .{merged_font_code}-icon {{
      font-size: 32px;
      margin-bottom: 8px;
      color: #333;
    }}
    .icon-name {{
      font-size: 12px;
      color: #666;
      margin-bottom: 4px;
      word-break: break-word;
    }}
    .icon-code {{
      font-size: 10px;
      color: #999;
      font-family: monospace;
      background-color: #f0f0f0;
      padding: 2px 4px;
      border-radius: 3px;
      word-break: break-all;
    }}
    .font-section {{
      margin-bottom: 40px;
    }}

    /* 宽字符样式，占用两格位置 */
    .wide-icon {{
      grid-column: span 2;
    }}
  </style>
</head>
<body>
  <h1>{merged_font_name} Icons</h1>
"""

        # 为每个原始字体添加一个部分
        for font_code, symbols in grouped_symbols.items():
            # 查找原始字体的名称
            font_name = next((f["name"] for f in font_results if f["code"] == font_code), font_code)

            merged_html += f"""
  <div class="font-section">
    <h2>{font_name}</h2>
    <div class="icons-grid">
"""

            # 添加每个符号
            for symbol in symbols:
                name = symbol["name"].split('_', 1)[1]  # 移除前缀
                ligature = symbol["ligature"]

                # 检查是否为宽字符
                wide_char_class = ""
                if name == "1000000" or (isinstance(ligature, str) and len(ligature) > 5):
                    wide_char_class = " wide-icon"

                merged_html += f"""
      <div class="icon-item{wide_char_class}">
        <i class="{merged_font_code}-icon">{ligature}</i>
        <div class="icon-name">{name}</div>
        <div class="icon-code">{ligature}</div>
      </div>"""

            merged_html += """
    </div>
  </div>
"""

        # 完成HTML
        merged_html += """
</body>
</html>
"""

        merged_html_path = DIST_DIR / f"{merged_font_code}.html"
        with open(merged_html_path, "w") as f:
            f.write(merged_html)

        print(f"Generated merged font {merged_font_name}:")
        for fmt, path in merged_font_files.items():
            if path:
                print(f"  - {fmt}: {path}")
        print(f"  - CSS: {merged_css_path}")
        print(f"  - HTML demo: {merged_html_path}")

def main():
    # 检查依赖
    check_dependencies()

    # 查找图标目录
    icon_dirs = [d for d in ICONS_DIR.iterdir() if d.is_dir() and (d / "config.toml").exists()]

    if not icon_dirs:
        print("No icon sets found with config.toml files")
        return

    print(f"Found {len(icon_dirs)} icon sets")

    # 处理每个图标集
    results = []
    with ThreadPoolExecutor() as executor:
        # 并行处理每个图标集
        futures = [executor.submit(process_icon_set, icon_dir) for icon_dir in icon_dirs]
        for future in futures:
            result = future.result()
            if result:
                results.append(result)

    # 生成合并字体
    if len(results) > 1:
        merge_fonts(results)

    # 清理临时文件
    print("Cleaning up temporary files...")
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    print("Build complete!")

if __name__ == "__main__":
    main()
