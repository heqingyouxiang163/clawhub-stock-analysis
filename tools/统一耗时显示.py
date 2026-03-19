#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一耗时显示工具

功能:
为所有定时任务脚本添加统一的耗时显示逻辑
确保显示真实总耗时
"""

import os
import re

TOOLS_DIR = "/home/admin/openclaw/workspace/tools"

def add_timing_to_script(filepath):
    """为脚本添加统一耗时显示"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    
    # 1. 添加总开始时间记录
    if 'if __name__ == "__main__":' in content:
        # 在 main 入口添加总开始时间
        if 'total_start' not in content:
            content = content.replace(
                'if __name__ == "__main__":',
                'if __name__ == "__main__":\n    total_start = time.time()  # 记录总开始时间'
            )
            modified = True
            print(f"  ✅ 已添加总开始时间记录")
    
    # 2. 添加耗时计算和显示
    if '__main__' in content and 'total_start' in content:
        # 在脚本末尾添加耗时显示
        if '总耗时' not in content and 'total_elapsed' not in content:
            timing_code = '''
    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"\\n✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"\\n✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"\\n✅ **总耗时**: {total_elapsed/60:.1f}分钟")
'''
            # 在最后一个 print 后添加
            content = re.sub(
                r'(print\(.+\)\s*)(\nif __name__|$)',
                r'\1' + timing_code + r'\2',
                content,
                count=1
            )
            modified = True
            print(f"  ✅ 已添加总耗时显示")
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def check_all_scripts():
    """检查所有脚本"""
    print("=" * 70)
    print("🔍 检查所有定时任务脚本的耗时显示")
    print("=" * 70)
    print()
    
    scripts = [f for f in os.listdir(TOOLS_DIR) if f.endswith('.py')]
    
    fixed_count = 0
    for script in scripts:
        filepath = os.path.join(TOOLS_DIR, script)
        print(f"📋 {script}")
        if add_timing_to_script(filepath):
            fixed_count += 1
        else:
            print(f"  ✅ 无需修改")
    
    print()
    print(f"总计：{len(scripts)}个脚本，修复{fixed_count}个")
    print("=" * 70)

if __name__ == "__main__":
    import time
    check_all_scripts()
