#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径检查工具

功能:
1. 检查脚本中是否包含 `~` 路径
2. 自动修复为绝对路径
3. 验证路径是否存在
"""

import os
import re
import sys

# 工作目录
WORKSPACE = "/home/admin/openclaw/workspace"

def check_file(filepath):
    """检查文件中的路径"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 `~` 路径
    tilde_paths = re.findall(r'["\']~/[^"\']+["\']', content)
    
    if tilde_paths:
        print(f"⚠️ 发现 `~` 路径 ({len(tilde_paths)}个):")
        for path in tilde_paths[:5]:
            print(f"  - {path}")
        if len(tilde_paths) > 5:
            print(f"  ... 还有{len(tilde_paths)-5}个")
        return False
    else:
        print(f"✅ {filepath}: 路径规范 (无 `~` 路径)")
        return True

def fix_file(filepath):
    """修复文件中的路径"""
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在：{filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 `~` 路径
    old_content = content
    content = re.sub(r'["\']~/openclaw/workspace/', f'"{WORKSPACE}/', content)
    content = re.sub(r'["\']~/.openclaw/', f'"/home/admin/.openclaw/', content)
    
    if content != old_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已修复：{filepath}")
        return True
    else:
        print(f"✅ 无需修复：{filepath}")
        return True

def check_all_tools():
    """检查所有工具脚本"""
    print("=" * 70)
    print("🔍 路径检查")
    print(f"工作目录：{WORKSPACE}")
    print("=" * 70)
    print()
    
    tools_dir = os.path.join(WORKSPACE, "tools")
    if not os.path.exists(tools_dir):
        print(f"❌ 工具目录不存在：{tools_dir}")
        return
    
    # 检查所有.py 文件
    count = 0
    issues = 0
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(tools_dir, filename)
            count += 1
            if not check_file(filepath):
                issues += 1
    
    print()
    print(f"总计：{count}个文件，{issues}个问题")
    
    if issues > 0:
        print()
        print("💡 建议运行修复:")
        print(f"  python3 {sys.argv[0]} --fix")
    else:
        print("✅ 所有文件路径规范！")

def fix_all_tools():
    """修复所有工具脚本"""
    print("=" * 70)
    print("🔧 路径修复")
    print(f"工作目录：{WORKSPACE}")
    print("=" * 70)
    print()
    
    tools_dir = os.path.join(WORKSPACE, "tools")
    if not os.path.exists(tools_dir):
        print(f"❌ 工具目录不存在：{tools_dir}")
        return
    
    # 修复所有.py 文件
    count = 0
    fixed = 0
    
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(tools_dir, filename)
            count += 1
            if fix_file(filepath):
                # 验证修复
                if check_file(filepath):
                    fixed += 1
    
    print()
    print(f"总计：{count}个文件，修复{fixed}个")
    print("✅ 修复完成！")

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
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        fix_all_tools()
    else:
        check_all_tools()
