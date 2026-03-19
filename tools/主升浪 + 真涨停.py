#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主升浪 + 真涨停股推荐
用途：只选真正可能涨停的股票 (排除大市值蓝筹)
"""

from 多数据源修复版 import get_realtime_data
from 主板票筛选 import is_main_board
from datetime import datetime

# 观察池：只选活跃股、连板股、小市值股 (排除大蓝筹)
watch_pool = [
    # 连板股 (核心观察)
    '600370', '000890', '600227', '600683', '603929', '603248',
    '600545', '600302', '002427', '002278', '002724', '001278',
    '603738', '002020', '000639', '603421', '000620',
    
    # 活跃股 (股性好，经常涨停)
    '600569', '600643', '600396', '002256', '600751', '600152',
    '002466', '002460', '002469', '600278', '000858',
    
    # 热点题材 (可能涨停)
    '600383', '600048', '000002', '600887',
]

# 排除的大市值蓝筹 (不可能涨停)
exclude_codes = [
    '600519',  # 贵州茅台
    '601318',  # 中国平安
    '600036',  # 招商银行
    '000001',  # 平安银行
    '601166',  # 兴业银行
    '600030',  # 中信证券
    '601398',  # 工商银行
    '601288',  # 农业银行
    '601988',  # 中国银行
    '600585',  # 海螺水泥
    '000333',  # 美的集团
    '601088',  # 中国神华
    '601857',  # 中国石油
    '600900',  # 长江电力
]

print("=" * 75)
print("🦞 主升浪 + 真涨停股推荐")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("策略：排除大市值蓝筹，只选真正可能涨停的股票")
print("=" * 75)
print()

# 获取所有股票数据
all_stocks = []
stats = {'total': 0, 'limit_up': 0, 'high_prob': 0, 'main_wave': 0, 'decline': 0}

for code in watch_pool:
    # 排除大蓝筹
    if code in exclude_codes:
        continue
    
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
    limit_prob = 0
    
    # 已涨停 (9.5%+) - 观察
    if change_pct >= 9.5:
        stock_type = 'limit_up'
        stats['limit_up'] += 1
        score = 100
        limit_prob = 100
    
    # 高涨停概率 (5-9%，有量能，股性活跃)
    elif change_pct >= 5 and change_pct < 9.5:
        prob = 0
        if change_pct >= 7:
            prob += 40
        elif change_pct >= 5:
            prob += 30
        
        if volume_ratio > 3:
            prob += 25
        elif volume_ratio > 2:
            prob += 15
        
        if amount > 300000000:
            prob += 20
        elif amount > 200000000:
            prob += 10
        
        if turnover and 5 <= turnover <= 20:
            prob += 15
        
        limit_prob = min(prob, 95)
        
        if limit_prob >= 50:
            stock_type = 'high_prob'
            stats['high_prob'] += 1
            score = limit_prob
        else:
            stock_type = 'main_wave'
            stats['main_wave'] += 1
            score = 50 + change_pct * 5
    
    # 主升浪 (1-5%，有量能)
    elif change_pct >= 1 and change_pct < 5:
        if volume_ratio > 1.5 or amount > 150000000:
            stock_type = 'main_wave'
            stats['main_wave'] += 1
            score = 40 + change_pct * 8
            limit_prob = 20 + change_pct * 6
    
    # 下跌/平盘
    elif change_pct <= 0:
        stock_type = 'decline'
        stats['decline'] += 1
    
    data['stock_type'] = stock_type
    data['score'] = min(score, 100)
    data['limit_prob'] = limit_prob
    data['source'] = result.get('source_name', 'Unknown')
    all_stocks.append(data)

# 分类筛选
limit_up_stocks = [s for s in all_stocks if s['stock_type'] == 'limit_up']
high_prob_stocks = [s for s in all_stocks if s['stock_type'] == 'high_prob']
main_wave_stocks = [s for s in all_stocks if s['stock_type'] == 'main_wave']

# 排序
high_prob_stocks.sort(key=lambda x: (x.get('limit_prob', 0), x.get('score', 0)), reverse=True)
main_wave_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)

# 推荐组合：优先高涨停概率，再选主升浪
recommendations = []
recommendations.extend(high_prob_stocks[:2])
for mw in main_wave_stocks:
    if mw not in recommendations:
        recommendations.append(mw)
    if len(recommendations) >= 3:
        break

# 排序
recommendations.sort(key=lambda x: (x.get('limit_prob', 0), x.get('score', 0)), reverse=True)
recommendations = recommendations[:3]

print("📊 市场统计:")
print(f"  观察池：{stats['total']}只 (排除大蓝筹)")
print(f"  🔴 已涨停：{stats['limit_up']}只")
print(f"  🔥 高涨停概率：{stats['high_prob']}只")
print(f"  🟢 主升浪：{stats['main_wave']}只")
print(f"  📉 下跌/平盘：{stats['decline']}只")
print()

print("=" * 75)
print("🎯 推荐组合 (主升浪 + 真涨停潜力)")
print("=" * 75)
print()

for i, stock in enumerate(recommendations, 1):
    change_pct = float(stock.get('change_pct', 0) or 0)
    amount = float(stock.get('amount', 0) or 0)
    volume_ratio = float(stock.get('volume_ratio', 0) or 0)
    turnover = float(stock.get('turnover', 0) or 0)
    limit_prob = stock.get('limit_prob', 0)
    
    if stock['stock_type'] == 'high_prob':
        type_label = "【高涨停概率】"
        type_emoji = "🔥"
    elif stock['stock_type'] == 'main_wave':
        type_label = "【主升浪】"
        type_emoji = "🟢"
    else:
        type_label = "【观察】"
        type_emoji = "⚪"
    
    print(f"{i}. {stock['code']} {stock['name']} {type_label}")
    print(f"   {type_emoji} 得分：{stock['score']:.0f}/100 | 涨停概率：{limit_prob:.0f}%")
    print(f"   💰 现价：¥{stock['current']} ({change_pct:+.1f}%)")
    print(f"   💵 成交额：{amount/100000000:.2f}亿元")
    if volume_ratio:
        print(f"   📈 量比：{volume_ratio:.2f}")
    if turnover:
        print(f"   🔄 换手率：{turnover:.2f}%")
    print(f"   🎯 涨停价：¥{stock['pre_close']*1.1:.2f}")
    
    if stock['stock_type'] == 'high_prob':
        if limit_prob >= 70:
            print(f"   👉 操作：🔥 涨停概率高，积极介入")
        else:
            print(f"   👉 操作：🔥 有涨停潜力，可建仓")
    else:
        print(f"   👉 操作：🟢 主升浪，可建仓")
    
    print(f"   🛑 止损：-5% | 🎯 止盈：+10%")
    print()

if limit_up_stocks:
    print("=" * 75)
    print("🔴 已涨停观察 (明日连板机会)")
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
