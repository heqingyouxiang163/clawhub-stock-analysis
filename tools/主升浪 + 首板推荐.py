#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主升浪 + 首板潜力股推荐
用途：推荐主升浪股票 + 首板潜力股 + 连板股
"""

from 多数据源修复版 import get_realtime_data
from 主板票筛选 import is_main_board
from datetime import datetime

# 观察池：活跃股 + 连板股 + 热点股 (排除大蓝筹)
watch_pool = [
    # 连板股 (核心观察)
    '600370',  '600227', '600683', '603929', '603248',
    '600545', '600302', '002427', '002278', '002724', '001278',
    '603738', '002020', '000639', '603421', '000620',
    
    # 活跃股 (股性好)
    '600569', '600643', '600396', '002256', '600751', '600152',
    '002466', '002460', '002469', '600278', '000858',
    
    # 热点题材
    '600383', '600048', '000002', '600887', '600519',
]

# 排除的大市值蓝筹
exclude_codes = [
    '601318', '600036', '000001', '601166', '600030',
    '601398', '601288', '601988', '600585', '000333',
    '601088', '601857', '600900',
]

print("=" * 75)
print("🦞 主升浪 + 首板潜力股推荐")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("策略：主升浪/首板/连板都可以，排除大蓝筹")
print("=" * 75)
print()

# 获取所有股票数据
all_stocks = []
stats = {'total': 0, 'limit_up': 0, 'first_board': 0, 'main_wave': 0, 'decline': 0}

for code in watch_pool:
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
    board_prob = 0  # 涨停/连板概率
    
    # 已涨停 (9.5%+)
    if change_pct >= 9.5:
        stock_type = 'limit_up'
        stats['limit_up'] += 1
        score = 100
        board_prob = 100
        data['board_type'] = '已涨停'
    
    # 首板潜力 (5-9%，高量比，大成交)
    # 今天可能首次涨停
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
        elif amount > 150000000:
            prob += 10
        
        if turnover and 5 <= turnover <= 20:
            prob += 15
        
        board_prob = min(prob, 95)
        
        if board_prob >= 50:
            stock_type = 'first_board'  # 首板潜力
            stats['first_board'] += 1
            score = board_prob
            data['board_type'] = '首板潜力'
        else:
            stock_type = 'main_wave'
            stats['main_wave'] += 1
            score = 50 + change_pct * 5
            data['board_type'] = '主升浪'
    
    # 主升浪 (1-5%，有量能)
    elif change_pct >= 1 and change_pct < 5:
        if volume_ratio > 1.2 or amount > 80000000:
            stock_type = 'main_wave'
            stats['main_wave'] += 1
            score = 35 + change_pct * 10
            board_prob = 15 + change_pct * 6
            data['board_type'] = '主升浪'
    
    # 下跌/平盘 (但有大成交，可能反转)
    elif change_pct < 1:
        if amount > 200000000:  # 大成交，可能企稳
            stock_type = 'main_wave'
            stats['main_wave'] += 1
            score = 20 + amount / 100000000
            board_prob = 10
            data['board_type'] = '企稳观察'
        else:
            stock_type = 'decline'
            stats['decline'] += 1
            data['board_type'] = '弱势'
    
    data['stock_type'] = stock_type
    data['score'] = min(score, 100)
    data['board_prob'] = board_prob
    data['source'] = result.get('source_name', 'Unknown')
    all_stocks.append(data)

# 分类筛选
limit_up_stocks = [s for s in all_stocks if s['stock_type'] == 'limit_up']
first_board_stocks = [s for s in all_stocks if s['stock_type'] == 'first_board']
main_wave_stocks = [s for s in all_stocks if s['stock_type'] == 'main_wave']

# 排序
first_board_stocks.sort(key=lambda x: (x.get('board_prob', 0), x.get('score', 0)), reverse=True)
main_wave_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)
limit_up_stocks.sort(key=lambda x: x.get('score', 0), reverse=True)

# 推荐组合：优先首板潜力，再选主升浪
recommendations = []
recommendations.extend(first_board_stocks[:2])
for mw in main_wave_stocks:
    if mw not in recommendations:
        recommendations.append(mw)
    if len(recommendations) >= 3:
        break

# 排序
recommendations.sort(key=lambda x: (x.get('board_prob', 0), x.get('score', 0)), reverse=True)
recommendations = recommendations[:3]

print("📊 市场统计:")
print(f"  观察池：{stats['total']}只 (排除大蓝筹)")
print(f"  🔴 已涨停：{stats['limit_up']}只")
print(f"  🔥 首板潜力：{stats['first_board']}只")
print(f"  🟢 主升浪：{stats['main_wave']}只")
print(f"  📉 下跌/平盘：{stats['decline']}只")
print()

print("=" * 75)
print("🎯 推荐组合 (主升浪 + 首板潜力)")
print("=" * 75)
print()

for i, stock in enumerate(recommendations, 1):
    change_pct = float(stock.get('change_pct', 0) or 0)
    amount = float(stock.get('amount', 0) or 0)
    volume_ratio = float(stock.get('volume_ratio', 0) or 0)
    turnover = float(stock.get('turnover', 0) or 0)
    board_prob = stock.get('board_prob', 0)
    board_type = stock.get('board_type', '未知')
    
    if stock['stock_type'] == 'first_board':
        type_label = "【首板潜力】"
        type_emoji = "🔥"
    elif stock['stock_type'] == 'main_wave':
        type_label = "【主升浪】"
        type_emoji = "🟢"
    else:
        type_label = "【观察】"
        type_emoji = "⚪"
    
    print(f"{i}. {stock['code']} {stock['name']} {type_label}")
    print(f"   {type_emoji} 得分：{stock['score']:.0f}/100 | 涨停概率：{board_prob:.0f}%")
    print(f"   💰 现价：¥{stock['current']} ({change_pct:+.1f}%)")
    print(f"   💵 成交额：{amount/100000000:.2f}亿元")
    if volume_ratio:
        print(f"   📈 量比：{volume_ratio:.2f}")
    if turnover:
        print(f"   🔄 换手率：{turnover:.2f}%")
    print(f"   🎯 涨停价：¥{stock['pre_close']*1.1:.2f}")
    
    if stock['stock_type'] == 'first_board':
        if board_prob >= 70:
            print(f"   👉 操作：🔥 首板概率高，积极介入")
        else:
            print(f"   👉 操作：🔥 首板潜力，可建仓")
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
