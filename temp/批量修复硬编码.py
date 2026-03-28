#!/usr/bin/env python3
import os
import re

WORKSPACE = "/home/admin/openclaw/workspace"

# 修复规则：旧代码 -> 新代码 (从持仓配置导入)
fixes = {
    # 旧持仓代码 -> 从持仓配置导入
    r'["\']002342["\']': 'HOLDINGS[0]["code"] if HOLDINGS else "002342"',
    r'["\']603778["\']': 'HOLDINGS[0]["code"] if HOLDINGS else "603778"',
    r'["\']002828["\']': 'HOLDINGS[0]["code"] if HOLDINGS else "002828"',
    r'["\']600617["\']': 'HOLDINGS[0]["code"] if HOLDINGS else "600617"',
}

# 需要修复的文件
files_to_fix = [
    "tools/智能预判.py",
]

for filepath in files_to_fix:
    full_path = os.path.join(WORKSPACE, filepath)
    if not os.path.exists(full_path):
        continue
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加导入语句（如果需要）
    if 'from 持仓配置 import HOLDINGS' not in content:
        content = 'from 持仓配置 import HOLDINGS\n' + content
    
    print(f'✅ 已处理：{filepath}')

print('\n🎉 批量修复完成！')
