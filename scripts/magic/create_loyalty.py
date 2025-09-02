#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import math
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

# 添加父目录到系统路径，以便导入父目录中的模块
sys.path.append(str(Path(__file__).parent.parent))
from read_config import read_config

# 设置命名空间
ET.register_namespace('', "http://www.w3.org/2000/svg")
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

# 项目根目录（使用pwd作为当前工作目录）
PROJECT_ROOT = Path(os.getcwd())

BASE_PATH = 'icons/magic'
CONFIG_PATH = 'icons/magic/config.toml'
ICONS_DIR = "icons/magic/components"
LOYALTY_OUTPUT_PATH = 'icons/magic/default'
FONT_PATH = 'fonts/Plantin-Bold.ttf'  # Plantin 字体路径

LOYALTY_NAUGHT_PATH = f'{ICONS_DIR}/_loyalty_naught.svg'
LOYALTY_UP_PATH = f'{ICONS_DIR}/_loyalty_up.svg'
LOYALTY_DOWN_PATH = f'{ICONS_DIR}/_loyalty_down.svg'

NAUGHT_CENTER_Y = 60

def text_to_path(text, font_path, font_size):
    """
    将文本转换为SVG路径

    参数:
        text: 要转换的文本
        font_path: 字体文件路径
        font_size: 字体大小
        bold: 是否加粗

    返回:
        path_data: SVG路径数据
        width: 文本宽度
        height: 文本高度
    """
    try:
        font = TTFont(font_path)

        # 从字体获取unitsPerEm值
        head_table = font.get('head')
        units_per_em = 1000  # 默认值
        if head_table:
            units_per_em = getattr(head_table, 'unitsPerEm', 1000)

        scale = font_size / units_per_em

        # 创建SVG路径收集器
        glyph_set = font.getGlyphSet()
        svg_path_pen = SVGPathPen(glyph_set)

        # 获取文本的总宽度
        total_width = 0
        path_commands = []

        # 处理每个字符
        for char in text:
            # 获取字符的字形名称
            unicode_value = ord(char)
            cmap = font.getBestCmap()
            glyph_name = cmap.get(unicode_value)

            if not glyph_name:
                print(f"警告: 字符 '{char}' (Unicode {hex(unicode_value)}) 在字体中找不到对应的字形")
                continue

            # 获取字形
            glyph = glyph_set[glyph_name]

            # 应用变换和偏移
            transform = (scale, 0, 0, -scale, total_width * scale, 0)
            transform_pen = TransformPen(svg_path_pen, transform)

            # 绘制字形路径
            glyph.draw(transform_pen)

            # 获取当前字符的SVG命令并存储
            current_commands = svg_path_pen.getCommands()
            path_commands.append(current_commands)

            # 重置路径笔以准备下一个字符
            svg_path_pen = SVGPathPen(glyph_set)

            # 累加宽度
            total_width += glyph.width

        # 合并所有路径命令
        all_path_data = " ".join(path_commands)

        # 获取文本总体宽度和高度的估计值
        text_width = total_width * scale
        text_height = font_size * 0.784  # 查询上升部和下降部计算得知

        return all_path_data, text_width, text_height

    except Exception as e:
        print(f"文本转路径时出错: {e}")
        import traceback
        traceback.print_exc()
        return "", 0, 0

def add_text_to_svg(svg_path, text, output_path):
    """
    向SVG添加文本，将文本转换为路径

    参数:
        svg_path: 忠诚度SVG文件路径
        text: 要添加的文本
        output_path: 输出SVG文件路径
    """

    text = text.replace('-', '−')

    try:
        # 解析SVG文件
        tree = ET.parse(svg_path)
        root = tree.getroot()

        # 获取SVG尺寸
        viewbox: str = root.get("viewBox", '')
        width = int(viewbox.split()[2])
        height = int(viewbox.split()[3])

        # 将文本转换为路径
        font_path = os.path.join(PROJECT_ROOT, FONT_PATH)
        path_data, text_width, text_height = text_to_path(text, font_path, font_size=60)

        if not path_data:
            raise ValueError("无法将文本转换为路径")

        # 创建路径元素
        path_elem = ET.SubElement(root, "path")
        path_elem.set("d", path_data)
        path_elem.set("fill", "black")

        # 计算居中位置
        x_offset = (width - text_width) / 2

        # 获取text基线到中心的偏移量
        # 使用字体高度的一半作为基准，再微调以达到视觉居中效果
        y_offset = height / 2 + text_height * 0.35

        print(f"文本宽度: {text_width}, 文本高度: {text_height}, x偏移: {x_offset}, y偏移: {y_offset}")

        # 应用变换以使文本完全居中
        path_elem.set("transform", f"translate({x_offset}, {y_offset})")

        # 保存修改后的SVG
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"SVG文件已成功创建（带路径文本）：{output_path}")

    except Exception as e:
        print(f"处理SVG时出错：{e}")
        sys.exit(1)

def main():
    config = read_config(Path(CONFIG_PATH))

    symbols = config['symbols']

    for symbol in symbols:
        if symbol['create_loyalty']:
            file = symbol['file']

            output_path = os.path.join(LOYALTY_OUTPUT_PATH, file)

            text = re.sub(r'^\[|\]$', '', symbol['ligature'][0])

            if text == '0':
                svg_path = LOYALTY_NAUGHT_PATH
            elif text.startswith('+'):
                svg_path = LOYALTY_UP_PATH
            elif text.startswith('-'):
                svg_path = LOYALTY_DOWN_PATH
            else:
                raise ValueError(f"Invalid loyalty text: {text} in {file}")

            add_text_to_svg(svg_path, text, output_path)

if __name__ == "__main__":
    main()
