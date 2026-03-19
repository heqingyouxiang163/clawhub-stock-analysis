#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
涨停推荐 debug 版 - 查找问题
"""

from 多数据源修复版 import get_realtime_data
from 主板票筛选 import is_main_board

watch_codes = [
    '600370', '000890', '600227', '600683', '603929', '603248',
    '600302', '002427', '002278', '002724', '001278', '603738',
]

print(f"测试 {len(watch_codes)} 只股票...")
print()

success = 0
fail = 0

for i, code in enumerate(watch_codes, 1):
    # 检查主板
    if not is_main_board(code):
        print(f"[{i}/{len(watch_codes)}] {code} - 不是主板，跳过")
        continue
    
    # 获取数据
    result = get_realtime_data(code)
    
    if result.get('success'):
        data = result['data']
        print(f"[{i}/{len(watch_codes)}] {code} {data.get('name', 'N/A')} - ✅ 成功 - ¥{data.get('current', 0):.2f} ({data.get('change_pct', 0):+.1f}%)")
        success += 1
    else:
        print(f"[{i}/{len(watch_codes)}] {code} - ❌ 失败 - {result.get('error', 'Unknown')}")
        fail += 1

print()
print(f"成功：{success} 只 | 失败：{fail} 只")
