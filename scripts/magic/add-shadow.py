#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import svgutils.transform as sg

CONFIG_PATH = 'icons/magic/config.toml'
SHADOW_PATH = 'icons/magic/_shadow.svg'
SHADOW_OUTPUT_PATH = 'icons/magic/shadow'

os.makedirs(SHADOW_OUTPUT_PATH, exist_ok=True)

def read_config(config_path):
    import toml
    with open(config_path, "r") as f:
        return toml.load(f)

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
    config = read_config(CONFIG_PATH)

    symbols = config['symbols']

    for symbol in symbols:
        if symbol.get('add-shadow', False):
            path = symbol['path']

            input_path = os.path.join(os.path.dirname(CONFIG_PATH), path)
            output_path = os.path.join(os.path.dirname(CONFIG_PATH), f"shadow/{os.path.basename(path)}")

            create_shadow(input_path, output_path)


if __name__ == "__main__":
    main()
