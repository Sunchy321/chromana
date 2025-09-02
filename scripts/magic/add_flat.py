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
FLAT_PATH = 'icons/magic/_flat.svg'
FLAT_OUTPUT_PATH = 'icons/magic/flat'

os.makedirs(FLAT_OUTPUT_PATH, exist_ok=True)

fill_map = {
    '#CAC5C0': '#000000',
    '#FFFCD5': '#89723E',
    '#ABE1FA': '#0172BB',
    '#CCC2C0': '#281C1C',
    '#F9AA8F': '#FD2302',
    '#9BD3AE': '#027920',

    '#C3BAB9': '#000000',
    
    # phyrexian colors
    '#EAE3B1': '#89723E',
    '#8EBBD0': '#0172BB',
    '#9A8D89': '#281C1C',
    '#DF8065': '#FD2302',
    '#80B092': '#027920',
    '#CCC2C0': '#000000',
}

def create_flat(svg_path: str, output_path: str, flat_type: str):
    fig = sg.SVGFigure(100, 100)

    fig1 = sg.fromfile(svg_path)
    fig2 = sg.fromfile(FLAT_PATH)

    plot1 = fig1.getroot()
    plot2 = fig2.getroot()

    g = plot1[0]

    children = g.root.getchildren()

    g.root.clear()

    basic_fill = ''

    for child in children:
        if child.tag == '{http://www.w3.org/2000/svg}circle':
            basic_fill = child.get('fill')
            continue

        # Split icons
        if child.get('id') == 'Shape':
            basic_fill = '#CAC5C0'
            continue

        child.set('transform', 'translate(50, 50) scale(0.9) translate(-50, -50)')

        if 'fill' in child.keys():
            if flat_type == 'split':
                fill = child.get('fill')

                if fill_map.get(fill) is None:
                    raise ValueError(f"Unknown fill color: {fill} in {svg_path}")

                child.set('fill', fill_map[fill])
            else:
                if fill_map.get(basic_fill) is None:
                    raise ValueError(f"Unknown fill color: {basic_fill} in {svg_path}")
                child.set('fill', fill_map[basic_fill])

        g.root.append(child)

    circle = plot2[0]

    if flat_type == 'split':
        circle.root.set('fill', '#000000')
    else:
        circle.root.set('fill', fill_map[basic_fill])

    fig.append([plot2, plot1])

    fig.root.set("viewBox", "0 0 100 100")

    fig.save(output_path)

    print(f"Created shadow for {svg_path} at {output_path}")

def main():
    config = read_config(Path(CONFIG_PATH))

    symbols = config['symbols']

    for symbol in symbols:
        if symbol['add_flat']:
            file = symbol['file']

            input_path = os.path.join(BASE_PATH, "default", file)
            output_path = os.path.join(FLAT_OUTPUT_PATH, file)

            create_flat(input_path, output_path, symbol['add_flat'])


if __name__ == "__main__":
    main()
