#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试「实时 A 股涨幅榜」技能集成
"""

import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/实时 A 股涨幅榜/tools')
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')

from 获取涨幅榜 import get_realtime_gainers, display_gainers

# 使用 importlib 导入带连字符的模块
import importlib.util
spec = importlib.util.spec_from_file_location("高确定性推荐", "/home/admin/openclaw/workspace/tools/高确定性推荐 - 定时任务.py")
高确定性推荐 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(高确定性推荐)
HighProbRecommender = 高确定性推荐.HighProbRecommender

print("=" * 70)
print("🧪 测试「实时 A 股涨幅榜」技能集成")
print("=" * 70)

# 测试 1：直接调用技能
print("\n【测试 1】直接调用技能获取沪深主板涨幅榜\n")
stocks = get_realtime_gainers(limit=30)
display_gainers(stocks)

# 测试 2：验证是否全是主板股票
print("\n【测试 2】验证股票代码\n")
main_board_count = 0
gem_count = 0
star_count = 0

for s in stocks:
    code = s['code']
    if code.startswith('300') or code.startswith('301'):
        gem_count += 1
        print(f"❌ 发现创业板：{code} {s['name']}")
    elif code.startswith('688'):
        star_count += 1
        print(f"❌ 发现科创板：{code} {s['name']}")
    elif code.startswith(('000', '001', '002', '003', '600', '601', '603', '605')):
        main_board_count += 1

print(f"\n✅ 统计结果:")
print(f"  沪深主板：{main_board_count}只")
print(f"  创业板：{gem_count}只")
print(f"  科创板：{star_count}只")
print(f"  总计：{len(stocks)}只")

if gem_count == 0 and star_count == 0:
    print("\n✅ 验证通过：全部是沪深主板股票！")
else:
    print("\n❌ 验证失败：包含创业板或科创板股票！")

# 测试 3：集成到高确定性推荐
print("\n【测试 3】集成到高确定性推荐系统\n")
recommender = HighProbRecommender()
watchlist = recommender.fetch_realtime_watchlist()
print(f"✅ 观察池：{len(watchlist)}只股票")
print(f"   持仓股：{recommender.holdings_codes}")

print("\n" + "=" * 70)
print("🎉 测试完成！")
print("=" * 70)
