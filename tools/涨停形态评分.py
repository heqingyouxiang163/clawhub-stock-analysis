#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
涨停形态评分 - 基于分时图战法
用途：根据涨停分时形态特征，筛选最可能涨停的股票
"""

from 多数据源修复版 import get_realtime_data
from 主板票筛选 import is_main_board
from datetime import datetime

# 观察池：活跃股 + 连板股 (排除大蓝筹)
watch_pool = [
    # 连板股
    '600370',  '600227', '600683', '603929', '603248',
    '600545', '600302', '002427', '002278', '002724', '001278',
    '603738', '002020', '000639', '603421', '000620',
    
    # 活跃股
    '600569', '600643', '600396', '002256', '600751', '600152',
    '002466', '002460', '002469', '600278', '000858',
    
    # 热点题材
    '600383', '600048', '000002', '600887',
]

# 排除的大蓝筹
exclude_codes = [
    '601318', '600036', '000001', '601166', '600030',
    '601398', '601288', '601988', '600585', '000333',
    '601088', '601857', '600900', '600519',
]

print("=" * 75)
print("🦞 涨停形态评分 (分时图战法)")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("策略：基于涨停分时形态特征筛选")
print("=" * 75)
print()

# 获取所有股票数据
all_stocks = []

for code in watch_pool:
    if code in exclude_codes:
        continue
    
    if not is_main_board(code):
        continue
    
    result = get_realtime_data(code)
    
    if not result.get('success'):
        continue
    
    data = result['data']
    change_pct = float(data.get('change_pct', 0) or 0)
    amount = float(data.get('amount', 0) or 0)
    volume_ratio = float(data.get('volume_ratio', 0) or 0)
    turnover = float(data.get('turnover', 0) or 0)
    
    # 计算开盘涨幅
    open_pct = (float(data.get('open', 0) or 0) - float(data.get('pre_close', 1) or 1)) / float(data.get('pre_close', 1) or 1) * 100
    
    # 已涨停的排除
    if change_pct >= 9.5:
        continue
    
    # 计算涨停形态评分 (100 分)
    # 基于分时图战法标准
    
    score = 0
    details = {}
    
    # 1. 涨幅得分 (10 分) - 3-8% 最佳 (主升浪加速段)
    if 5 <= change_pct <= 8:
        score += 10
        details['change'] = '10/10 (最佳区间)'
    elif 3 <= change_pct < 5:
        score += 8
        details['change'] = '8/10 (主升浪)'
    elif 7 <= change_pct < 9.5:
        score += 9
        details['change'] = '9/10 (接近涨停)'
    elif 2 <= change_pct < 3:
        score += 6
        details['change'] = '6/10 (启动初期)'
    elif 1 <= change_pct < 2:
        score += 4
        details['change'] = '4/10 (弱势上涨)'
    else:
        score += 2
        details['change'] = '2/10 (太弱)'
    
    # 2. 量比得分 (25 分) - 量比>2 最佳
    if volume_ratio > 3:
        score += 25
        details['volume_ratio'] = '25/25 (极强)'
    elif volume_ratio > 2:
        score += 20
        details['volume_ratio'] = '20/25 (强势)'
    elif volume_ratio > 1.5:
        score += 15
        details['volume_ratio'] = '15/25 (温和)'
    elif volume_ratio > 1:
        score += 10
        details['volume_ratio'] = '10/25 (偏弱)'
    else:
        # 无量比数据，用成交额估算
        if amount > 500000000:
            score += 15
            details['volume_ratio'] = '15/25 (大成交)'
        elif amount > 200000000:
            score += 10
            details['volume_ratio'] = '10/25 (中成交)'
        else:
            score += 5
            details['volume_ratio'] = '5/25 (无量)'
    
    # 3. 成交得分 (20 分) - 成交>3 亿最佳
    if amount > 500000000:
        score += 20
        details['amount'] = '20/20 (超活跃)'
    elif amount > 300000000:
        score += 18
        details['amount'] = '18/20 (很活跃)'
    elif amount > 150000000:
        score += 15
        details['amount'] = '15/20 (活跃)'
    elif amount > 100000000:
        score += 12
        details['amount'] = '12/20 (尚可)'
    else:
        score += 8
        details['amount'] = '8/20 (偏弱)'
    
    # 4. 换手得分 (15 分) - 5-15% 最佳 (健康换手)
    if turnover and 5 <= turnover <= 15:
        score += 15
        details['turnover'] = '15/15 (健康)'
    elif turnover and 3 <= turnover <= 20:
        score += 12
        details['turnover'] = '12/15 (可接受)'
    elif turnover and turnover > 20:
        score += 8
        details['turnover'] = '8/15 (过高)'
    elif turnover and turnover > 0:
        score += 6
        details['turnover'] = '6/15 (偏低)'
    else:
        score += 5
        details['turnover'] = '5/15 (无数据)'
    
    # 5. 开盘得分 (15 分) - 高开 2-5% 最佳
    if 2 <= open_pct <= 5:
        score += 15
        details['open'] = '15/15 (完美高开)'
    elif 1 <= open_pct < 2:
        score += 12
        details['open'] = '12/15 (小幅高开)'
    elif 5 < open_pct <= 7:
        score += 10
        details['open'] = '10/15 (高开较多)'
    elif 0 <= open_pct < 1:
        score += 8
        details['open'] = '8/15 (平开)'
    elif -2 <= open_pct < 0:
        score += 5
        details['open'] = '5/15 (小幅低开)'
    else:
        score += 3
        details['open'] = '3/15 (大幅低开)'
    
    # 6. 股性加分 (15 分) - 连板股/活跃股加分
    # 连板股 (从观察池前部分判断)
    if code in ['600370',  '600227', '600683', '603929', '603248', '600545']:
        score += 15
        details['stock_type'] = '15/15 (连板股)'
    elif code in ['600302', '002427', '002278', '002724', '001278', '603738']:
        score += 12
        details['stock_type'] = '12/15 (活跃股)'
    else:
        score += 8
        details['stock_type'] = '8/15 (普通)'
    
    # 总分 100 分
    data['total_score'] = min(score, 100)
    data['details'] = details
    data['change_pct'] = change_pct
    data['amount'] = amount
    data['volume_ratio'] = volume_ratio
    data['turnover'] = turnover
    data['open_pct'] = open_pct
    
    all_stocks.append(data)

# 排序
all_stocks.sort(key=lambda x: x.get('total_score', 0), reverse=True)

# 取前 10 名展示
top10 = all_stocks[:10]

print("📊 涨停形态评分 Top 10")
print("=" * 75)
print()

for i, stock in enumerate(top10, 1):
    code = stock['code']
    name = stock.get('name', 'N/A')
    score = stock.get('total_score', 0)
    change_pct = stock.get('change_pct', 0)
    amount = stock.get('amount', 0)
    details = stock.get('details', {})
    
    # 评级
    if score >= 85:
        rating = "🟢🟢🟢 极强"
        action = "积极买入"
    elif score >= 70:
        rating = "🟢🟢 强势"
        action = "可建仓"
    elif score >= 55:
        rating = "🟡 中性"
        action = "轻仓试错"
    else:
        rating = "🔴 弱势"
        action = "观望"
    
    print(f"{i}. {code} {name}")
    print(f"   总分：{score}/100 [{rating}]")
    print(f"   现价：¥{stock['current']} ({change_pct:+.1f}%)")
    print(f"   成交：{amount/100000000:.2f}亿")
    print(f"   评分详情:")
    for key, val in details.items():
        print(f"     • {val}")
    print(f"   👉 操作：{action}")
    print()

print("=" * 75)
print("📈 涨停形态评分标准 (100 分)")
print("=" * 75)
print("""
  1. 涨幅 (10 分): 5-8% 最佳 (主升浪加速段)
  2. 量比 (25 分): >3 最佳 (强势放量)
  3. 成交 (20 分): >5 亿最佳 (超活跃)
  4. 换手 (15 分): 5-15% 最佳 (健康换手)
  5. 开盘 (15 分): 高开 2-5% 最佳
  6. 股性 (15 分): 连板股>活跃股>普通

评级:
  ≥85 分：🟢🟢🟢 极强 - 积极买入
  70-84 分：🟢🟢 强势 - 可建仓
  55-69 分：🟡 中性 - 轻仓试错
  <55 分：🔴 弱势 - 观望
""")
print("=" * 75)
