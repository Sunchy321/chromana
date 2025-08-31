#!/bin/bash

# 删除Bun相关文件和目录
echo "正在删除Bun相关文件..."

# 要删除的文件列表
FILES_TO_REMOVE=(
  "bun.lock"
  "bunfig.toml"
  "package.json"
  "tsconfig.json"
  "scripts/serve.ts"
  "eslint.config.mjs"
  "types/bun-env.d.ts"
)

# 删除文件
for file in "${FILES_TO_REMOVE[@]}"; do
  if [ -f "$file" ]; then
    echo "删除: $file"
    rm "$file"
  else
    echo "文件不存在，跳过: $file"
  fi
done

# 删除types目录（如果为空）
if [ -d "types" ] && [ -z "$(ls -A types)" ]; then
  echo "删除空目录: types"
  rmdir "types"
fi

echo "Bun相关文件清理完成！"
