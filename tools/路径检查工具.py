#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径检查工具
扫描所有文件，检查路径是否规范
"""

import os
import re
import sys
from pathlib import Path


# 配置
CHECK_DIRS = [
    'skills/realtime-monitor-3min',
    'tools',
    'memory/自我进化'
]

SKIP_DIRS = ['.git', '__pycache__', 'node_modules', '.venv']

SKIP_FILES = ['.pyc', '.pyo', '.so', '.dll', '.bak']


def check_path_in_file(filepath):
    """检查文件中的路径是否规范"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except:
        return []  # 跳过无法读取的文件
    
    for i, line in enumerate(lines, 1):
        # 跳过注释和字符串中的路径
        if line.strip().startswith('#'):
            continue
        
        # 检查~路径 (代码文件中)
        if filepath.endswith('.py'):
            if re.search(r'["\']~/', line):
                if 'expanduser' not in line and 'pathlib' not in line:
                    issues.append({
                        'line': i,
                        'type': 'tilde_path',
                        'msg': '发现~路径，建议使用 os.path.expanduser() 或 pathlib',
                        'content': line.strip()[:80]
                    })
        
        # 检查硬编码用户路径
        if re.search(r'/home/[a-z]+/openclaw', line):
            # 允许在配置区使用
            if '配置' not in line and 'BASE_DIR' not in line and '示例' not in line:
                issues.append({
                    'line': i,
                    'type': 'hardcoded_path',
                    'msg': '发现硬编码路径，建议使用常量或环境变量',
                    'content': line.strip()[:80]
                })
        
        # 检查相对路径 (可能有问题)
        if filepath.endswith('.py') and 'open(' in line:
            if re.search(r'open\(["\'][^/]+/', line):
                if 'os.path' not in line and 'pathlib' not in line:
                    issues.append({
                        'line': i,
                        'type': 'relative_path',
                        'msg': '发现相对路径，建议使用绝对路径或 os.path.join()',
                        'content': line.strip()[:80]
                    })
    
    return issues


def scan_directory(directory):
    """扫描目录检查所有文件"""
    print(f"🔍 检查目录：{directory}")
    print("=" * 75)
    print()
    
    total_files = 0
    total_issues = 0
    issue_summary = {'tilde_path': 0, 'hardcoded_path': 0, 'relative_path': 0}
    
    for root, dirs, files in os.walk(directory):
        # 跳过隐藏目录和指定目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]
        
        for file in files:
            # 跳过指定类型
            if any(file.endswith(ext) for ext in SKIP_FILES):
                continue
            
            filepath = os.path.join(root, file)
            
            if file.endswith(('.py', '.md')):
                total_files += 1
                issues = check_path_in_file(filepath)
                
                if issues:
                    rel_path = os.path.relpath(filepath, directory)
                    print(f"⚠️ {rel_path}:")
                    
                    for issue in issues:
                        print(f"  第{issue['line']}行：{issue['msg']}")
                        print(f"    {issue['content']}")
                        print()
                        
                        total_issues += 1
                        issue_summary[issue['type']] += 1
    
    print("=" * 75)
    print(f"检查完成:")
    print(f"  总文件数：{total_files}")
    print(f"  发现问题：{total_issues}")
    print()
    print("问题分类:")
    for issue_type, count in issue_summary.items():
        if count > 0:
            print(f"  {issue_type}: {count}")
    
    return total_issues


def main():
    """主函数"""
    print("=" * 75)
    print("🦞 路径规范检查工具 v1.0")
    print("=" * 75)
    print()
    
    # 检查工作目录
    base_dir = "/home/admin/openclaw/workspace"
    
    if not os.path.exists(base_dir):
        print(f"❌ 工作目录不存在：{base_dir}")
        return 1
    
    os.chdir(base_dir)
    print(f"工作目录：{base_dir}")
    print()
    
    total_issues = 0
    
    # 检查指定目录
    for check_dir in CHECK_DIRS:
        if os.path.exists(check_dir):
            issues = scan_directory(check_dir)
            total_issues += issues
            print()
        else:
            print(f"⚠️ 目录不存在：{check_dir}")
            print()
    
    # 总结
    print("=" * 75)
    if total_issues > 0:
        print(f"❌ 发现 {total_issues} 个路径规范问题，请修复")
        print()
        print("修复建议:")
        print("  1. 使用 os.path.expanduser() 展开~路径")
        print("  2. 使用 pathlib.Path 处理路径")
        print("  3. 在配置区集中定义路径常量")
        print("  4. 参考 tools/路径规范指南.md")
        return 1
    else:
        print("✅ 所有路径规范")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
