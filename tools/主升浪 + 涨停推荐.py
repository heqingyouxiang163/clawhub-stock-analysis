#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主升浪 + 短线涨停股推荐
用途：同时推荐主升浪股票和短线涨停潜力股
"""

from 多数据源修复版 import get_realtime_data
from 主板票筛选 import is_main_board
from datetime import datetime

# 扩大观察池 (连板股 + 活跃股 + 蓝筹 + 热点)
watch_pool = [
    # 连板股 (优先)
    '600370', '000890', '600227', '600683', '603929', '603248',
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
print("🦞 主升浪 + 短线涨停股推荐")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 75)
print()

# 获取所有股票数据
all_stocks = []
stats = {'total': 0, 'limit_up': 0, 'main_wave': 0, 'hot': 0, 'decline': 0}

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
    turnover = float(data.get('turnover', 0) or 0)
    
    # 分类
    stock_type = 'other'
    score = 0
    
    # 已涨停 (9.5%+) - 排除
    if change_pct >= 9.5:
        stock_type = 'limit_up'
        stats['limit_up'] += 1
        score = 100
    # 主升浪 (3-9%，有量能)
    elif change_pct >= 3 and (volume_ratio > 1.5 or amount > 300000000):
        stock_type = 'main_wave'
        stats['main_wave'] += 1
        score = 60 + change_pct * 5
        if volume_ratio > 3:
            score += 15
        if 5 <= change_pct <= 8:
            score += 15  # 加速段
    # 涨停潜力股 (3-9%，有量能，可能涨停)
    # 特征：涨幅 3-9% + 量比>1.5 + 成交>3 亿
    elif change_pct >= 3 and change_pct < 9.5 and volume_ratio > 1.5 and amount > 300000000:
        stock_type = 'limit_potential'
        stats['hot'] += 1
        score = 70 + change_pct * 3
        if volume_ratio > 3:
            score += 15
        if 5 <= change_pct <= 8:
            score += 15  # 最佳涨停区间
        if turnover and 5 <= turnover <= 15:
            score += 10  # 健康换手
        if amount > 1000000000:
            score += 10  # 大成交
    # 短线热点 (1-5%，有量能)
    elif change_pct >= 1 and (volume_ratio > 1.5 or amount > 300000000):
        stock_type = 'hot'
        stats['hot'] += 1
        score = 40 + change_pct * 10
        if amount > 1000000000:
            score += 20
        if volume_ratio > 3:
            score += 15
    # 下跌/平盘
    elif change_pct <= 0:
        stock_type = 'decline'
        stats['decline'] += 1
    else:
        stock_type = 'other'
    
    data['stock_type'] = stock_type
    data['score'] = min(score, 100)
    data['source'] = result.get('source_name', 'Unknown')
    all_stocks.append(data)

# 分类筛选
limit_up_stocks = [s for s in all_stocks if s['stock_type'] == 'limit_up']
main_wave_stocks = [s for s in all_stocks if s['stock_type'] == 'main_wave']
limit_potential_stocks = [s for s in all_stocks if s['stock_type'] == 'limit_potential']
hot_stocks = [s for s in all_stocks if s['stock_type'] == 'hot']

# 排序
main_wave_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
limit_potential_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
hot_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
limit_up_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)

# 推荐组合：1 只主升浪 + 2 只涨停潜力股 (优先)
recommendations = []

# 优先涨停潜力股 (最可能涨停)
recommendations.extend(limit_potential_stocks[:2])

# 加 1 只主升浪
if main_wave_stocks:
    recommendations.append(main_wave_stocks[0])

# 不足 3 只用热点补充
while len(recommendations) < 3:
    added = False
    for stock in hot_stocks:
        if stock not in recommendations:
            recommendations.append(stock)
            added = True
            break
    if not added:
        break

# 排序推荐
recommendations.sort(key=lambda x: x.get('score', 0), reverse=True)
recommendations = recommendations[:3]

print("📊 市场统计:")
print(f"  观察池：{stats['total']}只 (主板)")
print(f"  🔴 已涨停：{stats['limit_up']}只 (买不进，可观察)")
print(f"  🟢 主升浪：{stats['main_wave']}只 (重点)")
print(f"  🟡 短线热点：{stats['hot']}只 (备选)")
print(f"  📉 下跌/平盘：{stats['decline']}只")
print()

print("=" * 75)
print("🎯 推荐组合 (2 只主升浪 + 1 只短线热点)")
print("=" * 75)
print()

for i, stock in enumerate(recommendations[:3], 1):
    change_pct = float(stock.get('change_pct', 0) or 0)
    amount = float(stock.get('amount', 0) or 0)
    volume_ratio = float(stock.get('volume_ratio', 0) or 0)
    turnover = float(stock.get('turnover', 0) or 0)
    
    # 类型标签
    if stock['stock_type'] == 'main_wave':
        type_label = "【主升浪】"
        type_emoji = "🟢"
    elif stock['stock_type'] == 'limit_potential':
        type_label = "【涨停潜力】"
        type_emoji = "🔥"
    elif stock['stock_type'] == 'hot':
        type_label = "【短线热点】"
        type_emoji = "🟡"
    else:
        type_label = "【观察】"
        type_emoji = "⚪"
    
    print(f"{i}. {stock['code']} {stock['name']} {type_label}")
    print(f"   {type_emoji} 得分：{stock['score']:.0f}/100")
    print(f"   💰 现价：¥{stock['current']} ({change_pct:+.1f}%)")
    print(f"   💵 成交额：{amount/100000000:.2f}亿元")
    if volume_ratio:
        print(f"   📈 量比：{volume_ratio:.2f}")
    if turnover:
        print(f"   🔄 换手率：{turnover:.2f}%")
    print(f"   🎯 涨停价：¥{stock['pre_close']*1.1:.2f}")
    
    # 操作建议
    if stock['stock_type'] == 'limit_potential':
        if change_pct >= 7:
            print(f"   👉 操作：🔥 涨停概率高，可积极介入")
        else:
            print(f"   👉 操作：🔥 涨停潜力，可建仓")
    elif change_pct >= 7:
        print(f"   👉 操作：🟡 强势，可轻仓试错")
    elif change_pct >= 4:
        print(f"   👉 操作：🟢 主升浪加速，可介入")
    else:
        print(f"   👉 操作：🔵 主升浪初期，可建仓")
    
    print(f"   🛑 止损：-5% | 🎯 止盈：+10%")
    print()

# 已涨停观察列表
if limit_up_stocks:
    print("=" * 75)
    print("🔴 已涨停观察列表 (买不进，可关注明日机会)")
    print("=" * 75)
    for stock in limit_up_stocks[:5]:
        change_pct = float(stock.get('change_pct', 0) or 0)
        amount = float(stock.get('amount', 0) or 0)
        print(f"  • {stock['code']} {stock['name']} +{change_pct:.1f}% ({amount/100000000:.1f}亿)")
    print()

print("=" * 75)
print("⚠️ 风险提示：仅供参考，不构成投资建议")
print("    仓位：单只≤20% | 总仓≤60% | 止损：-5%")
print("=" * 75)
