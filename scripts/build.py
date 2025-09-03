#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import subprocess
import glob
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from read_config import Style, read_config, Symbol
from typing import Dict, List, Tuple, Optional, TypedDict

# ANSI Color Code
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 亮色版本
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

# Symbols
class Symbols:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    BUILDING = "🔧"
    CLEANING = "🧹"
    FOUND = "📁"
    GENERATED = "📝"
    ARROW = "➤"
    BULLET = "•"
    CHECK = "✓"
    CROSS = "✗"

def print_colored(message, color=Colors.RESET, symbol="", bold=False):
    """Print colored message with symbol"""
    style = Colors.BOLD if bold else ""
    symbol_part = f"{symbol} " if symbol else ""
    print(f"{color}{style}{symbol_part}{message}{Colors.RESET}")

def print_success(message, symbol=Symbols.SUCCESS):
    """Print success message"""
    print_colored(message, Colors.BRIGHT_GREEN, symbol, bold=True)

def print_error(message, symbol=Symbols.ERROR):
    """Print error message"""
    print_colored(message, Colors.BRIGHT_RED, symbol, bold=True)

def print_warning(message, symbol=Symbols.WARNING):
    """Print warning message"""
    print_colored(message, Colors.BRIGHT_YELLOW, symbol, bold=True)

def print_info(message, symbol=Symbols.INFO):
    """Print info message"""
    print_colored(message, Colors.BRIGHT_BLUE, symbol)

def print_building(message, symbol=Symbols.BUILDING):
    """Print building message"""
    print_colored(message, Colors.BRIGHT_CYAN, symbol, bold=True)

def print_step(message, symbol=Symbols.ARROW):
    """Print step message"""
    print_colored(message, Colors.BRIGHT_MAGENTA, symbol, bold=True)

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

# Check if nanoemoji is installed
def check_dependencies():
    print_info("Checking dependencies...", Symbols.INFO)

    try:
        subprocess.run(["nanoemoji", "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print_success("nanoemoji is installed", Symbols.CHECK)
    except FileNotFoundError:
        print_warning("nanoemoji not found, installing...", Symbols.WARNING)
        subprocess.run([sys.executable, "-m", "pip", "install", "nanoemoji"], check=True)
        print_success("nanoemoji installation complete", Symbols.SUCCESS)

    # Check font conversion tools
    try:
        import fontTools
        print_success(f"fontTools {fontTools.__version__} found", Symbols.CHECK)
    except ImportError:
        print_warning("fonttools not found, installing...", Symbols.WARNING)
        subprocess.run([sys.executable, "-m", "pip", "install", "fonttools"], check=True)
        print_success("fonttools installation complete", Symbols.SUCCESS)

    # Check WOFF2 support
    try:
        import brotli
        print_success("brotli found, WOFF2 conversion available", Symbols.CHECK)
    except ImportError:
        print_warning("brotli not found, WOFF2 conversion may not be available", Symbols.WARNING)
        print_info("To enable WOFF2 support, install brotli: pip install brotli", Symbols.INFO)

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

GlyphMapping = Dict[str, SingleSymbol]

# 使用nanoemoji生成基本字体
def build_nanoemoji_font(params: NanoEmojiParams) -> tuple[Optional[Path], Optional[GlyphMapping]]:
    font_name = params["font_name"]
    symbols = params["symbols"]

    if not symbols:
        print_error(f"No valid symbols found for {font_name}")
        return None, None

    print_building(f"Building font {font_name} with {len(symbols)} icons")

    # Create temporary directory for renamed SVG files
    temp_svg_dir = TEMP_DIR / "svgs"
    temp_svg_dir.mkdir(exist_ok=True)

    # Store temporary SVG file paths
    temp_svgs = []
    # Store mapping between codepoints and glyph names
    glyph_mappings: GlyphMapping = {}

    # Create a temporary copy for each SVG with filename format expected by nanoemoji
    for i, sym in enumerate(symbols):
        svg = sym["path"]

        # Use Private Use Area codepoints
        codepoint = 0xE000 + i
        hex_codepoint = f"{codepoint:04x}"

        # Create filename format expected by nanoemoji: emoji_uXXXX.svg
        temp_filename = f"emoji_u{hex_codepoint}.svg"
        temp_svg_path = temp_svg_dir / temp_filename

        # Preprocess SVG file and copy to temporary location
        preprocess_svg(svg, temp_svg_path)
        temp_svgs.append(str(temp_svg_path))

        # Store mapping between codepoint and glyph name
        glyph_mappings[hex_codepoint] = sym

    print_success(f"Created {len(temp_svgs)} temporary SVG files using Unicode codepoints")

    # Create a temporary configuration file
    build_dir = BUILD_DIR

    # nanoemoji outputs to build/Font.ttf by default, we'll record this path
    default_output = build_dir / "Font.ttf"

    # Build command line - Phase 1: Create basic font without ligature functionality
    cmd_basic = [
        "nanoemoji",
        "--family", font_name,
        "--color_format", "glyf_colr_0",
        "--output_file", str(default_output),
        "--width", "0",
        "--ascender", "850",
        "--descender", "-150",
        "--noclip_to_viewbox",
        *temp_svgs
    ]

    # Execute command to create basic font
    print_step("Executing nanoemoji to create basic font")
    print_info(f"{' '.join(cmd_basic[:6])}... (plus {len(temp_svgs)} SVG files)")

    try:
        subprocess.run(cmd_basic, check=True)
    except subprocess.CalledProcessError as e:
        print_error(f"Error running nanoemoji to create basic font: {e}")
        try:
            result = subprocess.run(cmd_basic, capture_output=True, text=True)
            print_error(f"Stdout: {result.stdout[:500]}..." if len(result.stdout) > 500 else result.stdout)
            print_error(f"Stderr: {result.stderr[:500]}..." if len(result.stderr) > 500 else result.stderr)
        except Exception as e2:
            print_error(f"Error capturing output: {e2}")
        return None, None

    # Check if basic font was created successfully
    if not os.path.exists(default_output):
        print_error(f"Basic font file not created at expected location: {default_output}")
        return None, None

    print_success(f"Successfully created basic font: {default_output}")

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
        print_warning(f"No valid characters in ligature for {glyph_name}", Symbols.WARNING)
        return None

    # 创建FEA规则字符串，字符之间用空格分隔
    liga_string = " ".join(processed_chars)

    return liga_string

# Add ligature functionality to font
def add_ligatures_to_font(font_file: Path, output_file: str, glyph_mappings: GlyphMapping):
    print_step(f"Adding ligature functionality to font: {font_file}")

    # Step 1: Create ligature rules list
    variants: list[str] = []
    styles: list[str] = []

    liga_list: list[tuple[str, str]] = []
    salt_list: list[tuple[str, list[str]]] = []
    ss0x_lists: list[list[tuple[str, str]]] = []

    # Add replacement rules for each ligature
    added_rules = 0
    skipped_rules = 0

    for sym in glyph_mappings.values():
        variant = sym["variant"]
        style = sym["style"]

        if variant != 'default':
            variants.append(variant)

        if style != 'default' and style not in styles:
            styles.append(style)
            ss0x_lists.append([])

    groups: dict[str, tuple[list[str], dict[str, dict[str, str]]]] = {}

    for hex_codepoint, sym in glyph_mappings.items():
        glyph_name = sym["name"]
        ligatures = sym["ligatures"]
        variant = sym["variant"]
        style = sym["style"]

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
                print_error(f"Error processing ligature for {glyph_name}: {e}")
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

    # Step 2: Create FEA file to support ligature functionality
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
            fea_content.append(f"  sub {base_name} from [{alt_list}];")

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

    # Write FEA file
    with open(fea_file, "w") as f:
        f.write("\n".join(fea_content))

    print_success(f"Created feature file: {fea_file}")

    # Step 3: Use FontTools to add ligature functionality
    try:
        from fontTools.ttLib import TTFont
        from fontTools.feaLib.builder import addOpenTypeFeatures
        import re

        # Read basic font
        print_info("Adding ligature features to font...")
        font = TTFont(font_file)

        # Get all available glyph names in font
        available_glyphs = set(font.getGlyphOrder())
        print_info(f"Font contains {len(available_glyphs)} glyphs")

        # Use TTX to temporarily export font for adding missing glyphs later
        ttx_temp_file = str(TEMP_DIR / "temp_font.ttx")
        print_info(f"Exporting font to TTX format: {ttx_temp_file}")
        font.saveXML(ttx_temp_file)

        # Check and fix FEA file, find all missing glyphs that need to be added
        with open(fea_file, "r") as f:
            fea_content = f.read()

        # Use regex to find all referenced glyph names
        pattern = r'sub (.*?) by ([^;]+);'
        matches = re.findall(pattern, fea_content)

        # Collect all glyphs that need to be added
        missing_glyphs = set()

        INPUT_GLYPHS = {
            "braceleft": 0x007B, "braceright": 0x007D, "slash": 0x002F,
            "onehalf": 0x00BD, "uni221E": 0x221E,
            "zero": 0x30, "one": 0x31, "two": 0x32, "three": 0x33, "four": 0x34,
            "five": 0x35, "six": 0x36, "seven": 0x37, "eight": 0x38, "nine": 0x39,
            "bracketleft": 0x005B, "bracketright": 0x005D,
            "plus": 0x002B, "hyphen": 0x002D,
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

        # All glyphs should already exist, directly use original FEA file
        print_info(f"Found {len(matches)} rules in original FEA file")

        # Add OpenType features using original FEA file
        print_info(f"Adding OpenType features from {fea_file}")
        addOpenTypeFeatures(font, str(fea_file), tables=["GSUB"])

        # Save font with ligature functionality
        font_path = Path(font_file)
        enhanced_output = font_path.with_name(f"{os.path.basename(output_file)}")
        font.save(enhanced_output)
        print_success(f"Saved enhanced font (with ligatures) to: {enhanced_output}")

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Copy to specified output location
        shutil.copy2(enhanced_output, output_file)
        print_success(f"Copied font to final location: {output_file}")

        return True
    except Exception as e:
        print_error(f"Error adding ligature features: {e}")
        return False

def convert_fonts(ttf_path):
    from fontTools.ttLib import TTFont

    base_path = Path(ttf_path).with_suffix("")
    woff_path = f"{base_path}.woff"
    woff2_path = f"{base_path}.woff2"

    print_info(f"Converting {ttf_path} to WOFF and WOFF2 formats...")

    # Load TTF font
    try:
        font = TTFont(ttf_path)

        # Save as WOFF
        print_info(f"Saving WOFF format to {woff_path}")
        font.flavor = "woff"
        font.save(woff_path)
        print_success("WOFF format saved successfully", Symbols.CHECK)

        # Try to save as WOFF2
        try:
            print_info(f"Saving WOFF2 format to {woff2_path}")
            font.flavor = "woff2"
            font.save(woff2_path)
            print_success("WOFF2 format saved successfully", Symbols.CHECK)
            has_woff2 = True
        except Exception as e:
            print_warning(f"Error saving WOFF2 format: {e}")
            print_info("This may be because the woff2 Python module is not installed")
            print_info("You can install it with: pip install brotli")
            has_woff2 = False

    except Exception as e:
        print_error(f"Font conversion error: {e}")
        return {"ttf": ttf_path, "woff": None, "woff2": None}

    return {
        "ttf": ttf_path,
        "woff": woff_path,
        "woff2": woff2_path if has_woff2 else None
    }

# Generate CSS
def generate_css(font_name, font_files, font_code, version):
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
  font-family: 'Chromana-{font_code}';
  word-break: break-word;
}}

.{font_code}-icon {{
  font-family: '{font_name}';
  font-weight: normal;
  font-style: normal;
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

/* Different mode styles */
/* Normal mode (default) */
.normal {{
  font-feature-settings: 'liga';
}}

/* Shadow mode */
.shadow {{
  font-feature-settings: 'liga', 'ss01';
}}

/* Flat mode */
.flat {{
  font-feature-settings: 'liga', 'ss02';
}}
"""
    css_path = DEMO_DIR / f"{font_code}-{version}.css"
    with open(css_path, "w") as f:
        f.write(css)

    return css_path

# Generate example HTML
def generate_html(
    font_name, font_code, symbols: List[Symbol], css_path,
    categories=None, styles: Optional[List[Style]]=None, examples=None
):
    # Create category name mapping for friendly display names
    category_display_names = {}
    category_order = []  # Used to maintain category order
    if categories:
        for category in categories:
            category_name = category.get("name", "")
            display_name = category.get("display_name", category_name.replace("-", " ").title())
            if category_name:
                category_display_names[category_name] = display_name
                category_order.append(category_name)

    # Categorize symbols for display by category
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

    # Generate HTML for various categories
    category_sections = ""

    # Process all categories
    all_categories = []

    # First add categories in configuration order
    for category in category_order:
        if category in categorized_symbols:
            all_categories.append(category)

    # Then add other categories not specified in configuration
    for category in categorized_symbols.keys():
        if category not in all_categories:
            all_categories.append(category)

    # Generate HTML based on category order
    for category in all_categories:
        category_symbols = categorized_symbols[category]
        symbols_html = ""

        for symbol in category_symbols:
            name = symbol["name"]
            ligature = symbol["ligature"]

            # Handle multiple ligatures
            if isinstance(ligature, list):
                primary_ligature = ligature[0]  # Use first ligature as primary display
                all_ligatures = ", ".join(ligature)  # Show all ligatures separated by commas
            else:
                primary_ligature = ligature
                all_ligatures = ligature

            # Check for wide characters (like 1000000, etc.)
            wide_char_class = ""

            if symbol["overflow"]:  # Judge by name or character length
                wide_char_class = " wide-icon"

            symbols_html += f"""
        <div class="icon-item{wide_char_class}">
          <i class="{font_code}-icon icon-display">{primary_ligature}</i>
          <div class="icon-name">{name}</div>
          <div class="icon-code">{all_ligatures}</div>
        </div>"""

        # Use display name from configuration, or format as title
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

    # If no categories, display all symbols directly
    if not categorized_symbols:
        symbols_html = ""
        for symbol in symbols:
            name = symbol["name"]
            ligature = symbol["ligature"]

            # Handle multiple ligatures
            if isinstance(ligature, list):
                primary_ligature = ligature[0]  # Use first ligature as primary display
                all_ligatures = ", ".join(ligature)  # Show all ligatures separated by commas
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
        <h3 class="category-title">All Symbols</h3>
        <div class="icons-grid">
          {symbols_html}
        </div>
      </div>"""

    styles_html = ""

    if styles and len(styles) > 0:
        for style in styles:
            styles_html += f"<button class='mode-button' data-mode='{style.get('name')}'>{style.get('display_name', style.get('name'))}</button>\n"

    examples_html = generate_examples_html(font_code, examples)

    if examples_html is None:
        example_full_html = ''
    else:
        example_full_html = f"""
            <h3>文本示例</h3>
            <div class="text-examples">{examples_html}
            </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{font_name}</title>
  <link rel="stylesheet" href="./style.css">
  <link rel="stylesheet" href="./{os.path.basename(css_path)}">
  <script src="./{font_code}-action.js"></script>
</head>
<body>
  <!-- 浮空模式切换按钮 -->
  <div class="mode-switcher">
    <div class="mode-switcher-title">模式切换</div>
    <div class="mode-options">
      <button class="mode-button active" data-mode="normal">普通</button>
      {styles_html}
    </div>
  </div>

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
      <p>提示: 输入符号代码来测试连字功能。启用"阴影模式"可以切换显示带阴影的符号。</p>
    </section>

    <!-- 示例部分 -->
    <section class="section examples">
      <h2>使用示例</h2>
      <div class="example-container">
        <h3>在HTML中使用</h3>
        <div class="example-code">
          <pre><code>&lt;!-- 在CSS中引入字体 --&gt;
&lt;link rel="stylesheet" href="path/to/{font_code}.css"&gt;

&lt;!-- 使用图标 --&gt;
&lt;i class="{font_code}-icon"&gt;图标代码&lt;/i&gt;

&lt;!-- 使用带阴影效果的图标 --&gt;
&lt;i class="{font_code}-icon shadow"&gt;图标代码&lt;/i&gt;</code></pre>
        </div>

        <h3>在CSS中使用</h3>
        <div class="example-code">
          <pre><code>.my-icon::before {{
  font-family: '{font_name}';
  content: '图标代码';
  /* 其他样式 */
  font-size: 24px;
  color: #333;
}}</code></pre>
        </div>

       {example_full_html}
      </div>
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

def generate_examples_html(font_code, examples=None):
    """
    Generate HTML code based on examples from configuration file, optimized for long text display
    """
    if not examples or len(examples) == 0:
        # If no configured examples, use default examples
        return None

    # Use examples from configuration
    examples_html = ""
    for i, example in enumerate(examples):
        text = example.get("text", "这是一个示例文本")
        desc = example.get("desc", f"示例 {i+1}")

        # Handle optional style attributes
        font_size = example.get("font_size", "14px")
        line_height = example.get("line_height", "1.6")
        color = example.get("color", "")
        is_shadow = example.get("shadow", False)
        width = example.get("width", "100%")

        # Build style string
        style = f'font-size: {font_size}; line-height: {line_height};'
        if color:
            style += f' color: {color};'

        # Handle shadow mode
        shadow_class = " shadow" if is_shadow else ""

        examples_html += f"""
          <div class="example-text-container" style="width: {width};">
            <div class="example-text-content">
              <div style="{style}">
                {text}
              </div>
            </div>
            <div class="example-desc">{desc}</div>
          </div>
        """

    return examples_html

# Preprocess SVG files, fix duplicate IDs and other issues
def preprocess_svg(svg_path, temp_svg_path):
    """
    Preprocess SVG files, fix common issues:
    1. Duplicate element IDs
    2. Incompatible elements
    """
    import re
    from xml.dom import minidom

    try:
        # Parse SVG file using minidom
        dom = minidom.parse(svg_path)

        # Get all elements with id attributes
        elements_with_ids = {}
        # Traverse all possible element types that might have id attributes
        for elem_type in ['path', 'g', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon']:
            for elem in dom.getElementsByTagName(elem_type):
                if elem.hasAttribute('id'):
                    elem_id = elem.getAttribute('id')
                    if elem_id not in elements_with_ids:
                        elements_with_ids[elem_id] = []
                    elements_with_ids[elem_id].append(elem)

        # Fix duplicate ID issues
        for elem_id, elems in elements_with_ids.items():
            if len(elems) > 1:
                for i, elem in enumerate(elems[1:], 1):
                    new_id = f"{elem_id}_{i}"
                    elem.setAttribute('id', new_id)

        # Write modified SVG
        with open(temp_svg_path, 'w', encoding='utf-8') as f:
            # String generated by xml.dom.minidom includes XML declaration, we need to manually add SVG DOCTYPE
            svg_content = dom.toxml()
            # Add DOCTYPE if needed (optional)
            svg_content = svg_content.replace('<?xml version="1.0" ?>',
                                             '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">')
            f.write(svg_content)

        return True
    except Exception as e:
        print_error(f"Error preprocessing SVG file {svg_path}: {e}")
        # If error occurs, directly copy original file
        shutil.copy2(svg_path, temp_svg_path)
        return False

# Process individual icon set
def process_icon_set(icon_dir):
    icon_dir_path = Path(icon_dir)
    config_path = icon_dir_path / "config.toml"

    if not config_path.exists():
        print_warning(f"config.toml not found in {icon_dir_path}, skipping...")
        return None

    print_building(f"Processing icon set: {icon_dir_path.name}", Symbols.BUILDING)

    # Read configuration
    config = read_config(config_path)
    font_name = f'Chromana-{config["code"]}'
    font_code = config["code"]
    version = config["version"]
    symbols = config["symbols"]
    categories = config.get("categories")
    styles = config.get("styles")

    print_info(f"Found {len(symbols)} symbols in {font_name}")

    # Create output directory
    font_dist_dir = DIST_DIR / font_code
    font_dist_dir.mkdir(exist_ok=True)

    # Clean up old font files
    print_info(f"Cleaning old font files in {font_dist_dir}...", Symbols.CLEANING)
    for old_font in font_dist_dir.glob("*.ttf"):
        print_colored(f"  Removing old font file: {old_font.name}", Colors.DIM, Symbols.BULLET)
        old_font.unlink(missing_ok=True)
    for old_font in font_dist_dir.glob("*.woff"):
        print_colored(f"  Removing old font file: {old_font.name}", Colors.DIM, Symbols.BULLET)
        old_font.unlink(missing_ok=True)
    for old_font in font_dist_dir.glob("*.woff2"):
        print_colored(f"  Removing old font file: {old_font.name}", Colors.DIM, Symbols.BULLET)
        old_font.unlink(missing_ok=True)
    for old_font in font_dist_dir.glob("*.css"):
        print_colored(f"  Removing old CSS file: {old_font.name}", Colors.DIM, Symbols.BULLET)
        old_font.unlink(missing_ok=True)

    # Clean up old CSS files
    print_info(f"Cleaning old CSS files in {DEMO_DIR}...", Symbols.CLEANING)
    for old_css in DEMO_DIR.glob(f"{font_code}-*.css"):
        print_colored(f"  Removing old CSS file: {old_css.name}", Colors.DIM, Symbols.BULLET)
        old_css.unlink(missing_ok=True)

    # Prepare nanoemoji parameters
    nanoemoji_params = prepare_nanoemoji_params(
        f"{font_name}-{version}",
        icon_dir_path,
        font_dist_dir,
        symbols
    )

    # Generate TTF - inline replacement for build_font_with_nanoemoji call
    # Step 1: Generate basic font
    font_file, glyph_mappings = build_nanoemoji_font(nanoemoji_params)

    success = False

    if font_file is not None and glyph_mappings is not None:
        # Step 2: Add ligature functionality
        success = add_ligatures_to_font(font_file, nanoemoji_params["output_file"], glyph_mappings)

    # TTF path
    ttf_path = font_dist_dir / f"{font_name}-{version}.ttf"

    # Convert to other formats
    if success and ttf_path.exists():
        font_files = convert_fonts(str(ttf_path))

        # Generate CSS
        css_path = generate_css(font_name, font_files, font_code, version)

        # Generate example HTML
        examples = config.get("example", [])
        html_path = generate_html(font_name, font_code, symbols, css_path, categories, styles, examples)

        print_success(f"Generated font files for {font_name}:", Symbols.GENERATED)
        for fmt, path in font_files.items():
            if path:
                print_colored(f"  - {fmt.upper()}: {Path(path).name}", Colors.BRIGHT_GREEN, Symbols.CHECK)
        print_colored(f"  - CSS: {css_path.name}", Colors.BRIGHT_GREEN, Symbols.CHECK)
        print_colored(f"  - HTML demo: {html_path.name}", Colors.BRIGHT_GREEN, Symbols.CHECK)

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
        print_error(f"Failed to generate TTF font for {font_name}")
        return None

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Build Chromana icon fonts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build.py                    # Build all icon sets
  python build.py --icons magic      # Build only magic icon set
  python build.py --icons magic lorcana  # Build magic and lorcana icon sets
  python build.py -i magic           # Short form for --icons
        """
    )

    parser.add_argument(
        '--icons', '-i',
        nargs='*',
        metavar='ICON_SET',
        help='Specify which icon sets to build (e.g., magic, lorcana). If not specified, all icon sets will be built.'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available icon sets and exit'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()

def list_available_icon_sets():
    """List all available icon sets"""
    print_info("Available icon sets:", Symbols.INFO)

    icon_dirs = [d for d in ICONS_DIR.iterdir() if d.is_dir() and (d / "config.toml").exists()]

    if not icon_dirs:
        print_warning("No icon sets found with config.toml files", Symbols.WARNING)
        return []

    icon_sets = []
    for icon_dir in icon_dirs:
        try:
            config = read_config(icon_dir / "config.toml")
            name = config.get("name", icon_dir.name)
            code = config.get("code", icon_dir.name)
            version = config.get("version", "unknown")
            symbol_count = len(config.get("symbols", []))

            print_colored(f"  • {code} - {name} (v{version}) - {symbol_count} symbols", Colors.BRIGHT_CYAN, Symbols.BULLET)
            icon_sets.append(code)
        except Exception as e:
            print_warning(f"Error reading config for {icon_dir.name}: {e}", Symbols.WARNING)

    return icon_sets

def main():
    # Parse command line arguments
    args = parse_arguments()

    # If list flag is set, list available icon sets and exit
    if args.list:
        list_available_icon_sets()
        return

    # Check dependencies
    print_step("Starting Chromana font build", Symbols.BUILDING)
    if args.verbose:
        print_info("Verbose mode enabled", Symbols.INFO)

    check_dependencies()

    # Find icon directories
    all_icon_dirs = [d for d in ICONS_DIR.iterdir() if d.is_dir() and (d / "config.toml").exists()]

    if not all_icon_dirs:
        print_error("No icon sets found with config.toml files", Symbols.ERROR)
        return

    # Filter icon directories based on command line arguments
    if args.icons is not None:
        if len(args.icons) == 0:
            print_error("--icons flag specified but no icon sets provided", Symbols.ERROR)
            print_info("Use --list to see available icon sets", Symbols.INFO)
            return

        # Filter directories based on specified icon sets
        specified_icons = set(args.icons)
        icon_dirs = []

        for icon_dir in all_icon_dirs:
            try:
                config = read_config(icon_dir / "config.toml")
                code = config.get("code", icon_dir.name)
                if code in specified_icons:
                    icon_dirs.append(icon_dir)
                    specified_icons.remove(code)
            except Exception as e:
                print_warning(f"Error reading config for {icon_dir.name}: {e}", Symbols.WARNING)

        # Check if any specified icon sets were not found
        if specified_icons:
            print_warning(f"The following icon sets were not found: {', '.join(specified_icons)}", Symbols.WARNING)
            print_info("Use --list to see available icon sets", Symbols.INFO)

        if not icon_dirs:
            print_error("No valid icon sets found matching the specified criteria", Symbols.ERROR)
            return

        print_info(f"Building {len(icon_dirs)} specified icon sets", Symbols.FOUND)
    else:
        icon_dirs = all_icon_dirs
        print_info(f"Found {len(icon_dirs)} icon sets", Symbols.FOUND)

    # Process each icon set
    successful_builds = 0
    for icon_dir in icon_dirs:
        result = process_icon_set(icon_dir)
        if result:
            successful_builds += 1

    # Clean up temporary files
    print_step("Cleaning up temporary files...", Symbols.CLEANING)
    try:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        print_success("Temporary files cleaned", Symbols.CHECK)
    except Exception as e:
        print_warning(f"Issue occurred while cleaning temporary files: {e}")

    print_success(f"Build complete! Successfully built {successful_builds}/{len(icon_dirs)} fonts", Symbols.SUCCESS)

if __name__ == "__main__":
    main()
