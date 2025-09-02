#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import svgutils.transform as sg
from pathlib import Path

# 添加父目录到系统路径，以便导入父目录中的模块
sys.path.append(str(Path(__file__).parent.parent))
from read_config import read_config

BASE_PATH = 'icons/magic'
CONFIG_PATH = 'icons/magic/config.toml'
SHADOW_PATH = 'icons/magic/_shadow.svg'
SHADOW_OUTPUT_PATH = 'icons/magic/shadow'

os.makedirs(SHADOW_OUTPUT_PATH, exist_ok=True)

def create_shadow(svg_path, output_path):
    fig = sg.SVGFigure(100, 100)

    fig1 = sg.fromfile(svg_path)
    fig2 = sg.fromfile(SHADOW_PATH)

    plot1 = fig1.getroot()
    plot2 = fig2.getroot()

    plot1.moveto(8, 0)
    plot2.moveto(0, 8)

    fig.append([plot1, plot2])

    fig.root.set("viewBox", "0 0 108 100")

    fig.save(output_path)

    print(f"Created shadow for {svg_path} at {output_path}")

def main():
    config = read_config(Path(CONFIG_PATH))

    symbols = config['symbols']

    for symbol in symbols:
        if symbol['add_shadow']:
            file = symbol['file']

            input_path = os.path.join(BASE_PATH, "default", file)
            output_path = os.path.join(SHADOW_OUTPUT_PATH, file)

            create_shadow(input_path, output_path)


if __name__ == "__main__":
    main()
