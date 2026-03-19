#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复路径问题工具

功能:
1. 自动将 `~` 路径转换为绝对路径
2. 验证路径是否存在
3. 修复文件写入问题
"""

import os
import re

# 工作目录
WORKSPACE = "/home/admin/openclaw/workspace"
HOME_DIR = "/home/admin"

def fix_path(path):
    """将 `~` 路径转换为绝对路径"""
    if path.startswith("~/"):
        return os.path.join(HOME_DIR, path[2:])
    elif path.startswith("~/."):
        return os.path.join(HOME_DIR, path[3:])
    return path

def fix_file(filepath):
    """修复文件中的路径"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 `~` 路径
    old_content = content
    content = re.sub(r'~/openclaw/workspace/', f'{WORKSPACE}/', content)
    content = re.sub(r'~/.openclaw/', f'{HOME_DIR}/.openclaw/', content)
    content = re.sub(r'"~/', f'"{HOME_DIR}/', content)
    content = re.sub(r"'~/", f"'{HOME_DIR}/", content)
    
    if content != old_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已修复：{filepath}")
        return True
    else:
        print(f"✅ 无需修复：{filepath}")
        return True

def fix_all_files():
    """修复所有相关文件"""
    print("=" * 70)
    print("🔧 修复路径问题")
    print("=" * 70)
    print()
    
    # 修复记忆文件
    memory_files = [
        f"{WORKSPACE}/memory/自我进化/定时任务心跳日志.md",
        f"{WORKSPACE}/MEMORY.md",
        f"{WORKSPACE}/USER.md",
        f"{WORKSPACE}/HEARTBEAT.md"
    ]
    
    count = 0
    for filepath in memory_files:
        if os.path.exists(filepath):
            if fix_file(filepath):
                count += 1
    
    print()
    print(f"✅ 已检查 {count}个文件")
    print("=" * 70)

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"
✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"
✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"
✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    fix_all_files()
