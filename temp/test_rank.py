#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/实时 A 股涨幅榜')

from tencent_stock_rank import get_realtime_rank, get_limit_up_stocks, get_main_rising_stocks, get_market_stats

# 1. 获取实时涨幅前 20 只
print('📊 实时涨幅榜 TOP20:')
stocks = get_realtime_rank(limit=20, use_cache=False)
for i, s in enumerate(stocks[:20], 1):
    print(f'{i}. {s["code"]} {s["name"]}: ¥{s["current"]}  +{s["change_pct"]}%')

# 2. 涨停股
print('\n🔥 涨停股:')
limit_up = get_limit_up_stocks()
print(f'共 {len(limit_up)} 只涨停')
for s in limit_up[:5]:
    print(f'  {s["code"]} {s["name"]}: +{s["change_pct"]}%')

# 3. 主升浪 (5-8%)
print('\n📈 主升浪 (5-8%):')
rising = get_main_rising_stocks()
print(f'共 {len(rising)} 只')
for s in rising[:5]:
    print(f'  {s["code"]} {s["name"]}: +{s["change_pct"]}%')

# 4. 市场情绪
print('\n🎯 市场情绪:')
stats = get_market_stats()
total = sum(stats.values())
for k, v in stats.items():
    pct = v/total*100 if total > 0 else 0
    print(f'  {k}: {v}只 ({pct:.1f}%)')
