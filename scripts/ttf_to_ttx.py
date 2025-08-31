#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将 TTF 字体文件转换为 TTX (XML) 文件

用法:
    python ttf_to_ttx.py <字体文件.ttf> [输出文件.ttx]

如果不提供输出文件名，将使用与输入文件相同的名称，但扩展名为 .ttx
"""

import sys
import os
import argparse
from pathlib import Path
from fontTools.ttLib import TTFont

def convert_ttf_to_ttx(input_path, output_path=None):
    """
    将 TTF 字体文件转换为 TTX (XML) 格式

    参数:
        input_path: TTF 字体文件的路径
        output_path: 输出 TTX 文件的路径（可选）

    返回:
        输出文件的路径
    """
    try:
        # 如果未指定输出路径，使用输入文件名，但扩展名改为 .ttx
        if output_path is None:
            output_path = os.path.splitext(input_path)[0] + '.ttx'

        print(f"正在加载字体文件: {input_path}")
        font = TTFont(input_path)

        print(f"正在导出为 TTX 格式: {output_path}")
        font.saveXML(output_path)

        print(f"转换完成: {output_path}")
        return output_path
    except Exception as e:
        print(f"转换过程中发生错误: {e}")
        return None

def list_tables(input_path):
    """
    列出 TTF 文件中的所有表

    参数:
        input_path: TTF 字体文件的路径

    返回:
        表名列表
    """
    try:
        font = TTFont(input_path)
        tables = font.keys()
        return sorted(tables)
    except Exception as e:
        print(f"读取字体表过程中发生错误: {e}")
        return []

def main():
    """主函数"""
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='将 TTF 字体文件转换为 TTX (XML) 格式')
    parser.add_argument('input', help='输入的 TTF 字体文件路径')
    parser.add_argument('output', nargs='?', help='输出的 TTX 文件路径 (可选)')
    parser.add_argument('--tables', '-t', action='store_true', help='只列出字体中的表，不进行转换')
    parser.add_argument('--select', '-s', nargs='+', help='只导出指定的表 (例如 "cmap" "glyf")')

    args = parser.parse_args()

    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        print(f"错误: 文件 {args.input} 不存在")
        return 1

    # 如果只需要列出表
    if args.tables:
        tables = list_tables(args.input)
        if tables:
            print(f"字体文件 {args.input} 包含以下表:")
            for table in tables:
                print(f"  - {table}")
        return 0

    # 执行转换
    if args.select:
        # 如果指定了特定的表，我们需要先加载字体
        try:
            font = TTFont(args.input)

            # 确保所有请求的表都存在
            missing_tables = [t for t in args.select if t not in font]
            if missing_tables:
                print(f"警告: 以下请求的表在字体中不存在: {', '.join(missing_tables)}")

            # 设置输出路径
            output_path = args.output if args.output else os.path.splitext(args.input)[0] + '.ttx'

            # 只保存选定的表
            print(f"正在导出选定的表: {', '.join(args.select)}")
            font.saveXML(output_path, tables=args.select)

            print(f"转换完成: {output_path}")
        except Exception as e:
            print(f"转换过程中发生错误: {e}")
            return 1
    else:
        # 正常转换整个字体
        result = convert_ttf_to_ttx(args.input, args.output)
        if result is None:
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
