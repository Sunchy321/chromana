#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import http.server
import socketserver
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST_DIR = PROJECT_ROOT / "dist"
DEMO_DIR = PROJECT_ROOT / "demo"

# 默认端口
PORT = 4213

# 检查dist目录是否存在
if not DIST_DIR.exists() or not DIST_DIR.is_dir():
    print("Error: dist directory does not exist. Please run `python scripts/build.py` first.")
    sys.exit(1)

print("Starting development server...")
print(f"Server directories:")
print(f"- dist: {DIST_DIR}")
print(f"- demo: {DEMO_DIR}")

# 自定义请求处理器，用于提供来自不同目录的文件
class ChromanaRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # 默认路径处理
        path = super().translate_path(path)

        # 处理根路径 - 显示索引页面
        rel_path = os.path.relpath(path, os.getcwd())
        if rel_path == '.' or rel_path == './':
            # 提供演示根目录的索引
            return str(DEMO_DIR / "index.html")

        # 检查demo目录
        demo_path = DEMO_DIR / os.path.relpath(path, os.getcwd())
        if demo_path.exists():
            return str(demo_path)

        # 检查dist目录
        dist_path = DIST_DIR / os.path.relpath(path, os.getcwd())
        if dist_path.exists():
            return str(dist_path)

        return path

    def log_message(self, format, *args):
        # 彩色日志输出
        if args[1].startswith('2'): # 2xx状态码为成功
            status = f"\033[92m{args[1]}\033[0m" # 绿色
        elif args[1].startswith('3'): # 3xx状态码为重定向
            status = f"\033[94m{args[1]}\033[0m" # 蓝色
        elif args[1].startswith('4') or args[1].startswith('5'): # 4xx, 5xx为错误
            status = f"\033[91m{args[1]}\033[0m" # 红色
        else:
            status = args[1]

        print(f"{self.address_string()} - {status} {args[0] % args[1:]}")

# 启动服务器
handler = ChromanaRequestHandler
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"\nServer running at http://localhost:{PORT}/")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()
