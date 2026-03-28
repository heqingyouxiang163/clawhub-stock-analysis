#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""快速推荐 3 只主升浪股票"""

from 多数据源修复版 import get_realtime_data
from 主板票筛选 import is_main_board
from datetime import datetime

# 扩大观察池
watch_pool = [
    # 连板股
    '600370',  '600227', '600683', '603929', '603248',
    '600545', '600302', '002427', '002278', '002724', '001278',
    '603738', '002020', '000639', '603421', '000620',
    
    # 蓝筹/权重
    '600519', '000858', '002594', '601318', '600036', '000001',
    '600278', '002466', '002460', '002469', '600751', '600152',
    
    # 热点活跃
    '600569', '600643', '600396', '002256', '600383', '600048',
    '601166', '600030', '601398', '601288', '601988', '600585',
    '000333', '600887', '000002', '600900', '601088', '601857',
]

print("=" * 75)
print("🦞 主升浪潜力股推荐 (3 只)")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 75)
print()

qualified = []
stats = {'total': 0, 'main_wave': 0, 'limit_up': 0, 'decline': 0}

for code in watch_pool:
    if not is_main_board(code):
        continue
    
    stats['total'] += 1
    result = get_realtime_data(code)
    
    if not result.get('success'):
        continue
    
    data = result['data']
    change_pct = float(data.get('change_pct', 0) or 0)
    amount = float(data.get('amount', 0) or 0)
    volume_ratio = float(data.get('volume_ratio', 0) or 0)
    
    # 统计
    if change_pct >= 9.8:
        stats['limit_up'] += 1
    elif change_pct <= 0:
        stats['decline'] += 1
    
    # 主升浪标准 (放宽)
    # 1. 上涨
    # 2. 有量能 (量比>1 或 成交>2 亿)
    # 3. 涨幅>1%
    if change_pct > 1 and (volume_ratio > 1 or amount > 200000000):
        # 计算得分
        score = change_pct * 10
        if volume_ratio > 2:
            score += 20
        if amount > 500000000:
            score += 20
        if 5 <= change_pct <= 8:
            score += 30  # 主升浪加速段
        
        data['score'] = min(score, 100)
        data['source'] = result.get('source_name', 'Unknown')
        qualified.append(data)
        
        if change_pct >= 3 and change_pct < 9.8:
            stats['main_wave'] += 1

# 排序
qualified.sort(key=lambda x: x.get('score', 0), reverse=True)

# 排除已涨停
filtered = [s for s in qualified if float(s.get('change_pct', 0) or 0) < 9.5]

# 取前 3
top3 = filtered[:3]

for i, stock in enumerate(top3, 1):
    change_pct = float(stock.get('change_pct', 0) or 0)
    amount = float(stock.get('amount', 0) or 0)
    volume_ratio = float(stock.get('volume_ratio', 0) or 0)
    
    print(f"{i}. {stock['code']} {stock['name']} 【主升浪】")
    print(f"   得分：{stock['score']:.0f}/100")
    print(f"   现价：¥{stock['current']} ({change_pct:+.1f}%)")
    print(f"   成交额：{amount/100000000:.2f}亿元")
    if volume_ratio:
        print(f"   量比：{volume_ratio:.2f}")
    print(f"   涨停价：¥{stock['pre_close']*1.1:.2f}")
    
    # 操作建议
    if change_pct >= 7:
        print(f"   操作：🟡 强势，可轻仓试错")
    elif change_pct >= 4:
        print(f"   操作：🟢 主升浪加速，可介入")
    else:
        print(f"   操作：🔵 主升浪初期，可建仓")
    
    print(f"   止损：-5% | 止盈：+10%")
    print()

print("=" * 75)
print(f"📊 筛选统计：总计{stats['total']}只 | 主升浪{stats['main_wave']}只 | 涨停{stats['limit_up']}只 | 下跌{stats['decline']}只")
print("⚠️ 风险提示：仅供参考，不构成投资建议")
print("    仓位：单只≤20% | 总仓≤60% | 止损：-5%")
print("=" * 75)
