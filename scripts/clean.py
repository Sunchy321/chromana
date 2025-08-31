#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST_DIR = PROJECT_ROOT / "dist"
TEMP_DIR = PROJECT_ROOT / "temp"
BUILD_DIR = PROJECT_ROOT / "build"

def clean_directory(dir_path):
    """清理目录，如果目录存在则删除其中的所有内容"""
    if dir_path.exists():
        print(f"清理目录: {dir_path}")
        shutil.rmtree(dir_path)
        # 重新创建空目录
        dir_path.mkdir(exist_ok=True)
    else:
        print(f"目录不存在，跳过: {dir_path}")

if __name__ == "__main__":
    print("开始清理项目...")
    clean_directory(DIST_DIR)
    clean_directory(TEMP_DIR)
    clean_directory(BUILD_DIR)
    print("清理完成！")
