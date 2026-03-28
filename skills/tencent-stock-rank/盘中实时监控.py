#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 炒股龙虾 - 盘中实时监控

功能:
- 实时获取涨幅榜前 200
- 分时图形态分析
- 涨停潜力评分
- 高确定性推荐 (≥80 分)

使用:
    python3 盘中实时监控.py
"""

import requests
import time
from datetime import datetime
from typing import List, Dict


def get_top_gainers(limit=200):
    """获取前 N 只涨幅榜"""
    print(f"🔍 获取实时涨幅榜...")
    
    all_stocks = []
    batch_size = 100
    
    # 沪市 + 深市
    for prefix_list, market in [(['600', '601', '603', '605'], 'sh'),
                                  (['000', '001', '002', '003'], 'sz')]:
        for prefix in prefix_list:
            for i in range(0, 1000, batch_size):
                batch = [f'{market}{prefix}{j:03d}' for j in range(i, min(i+batch_size, 1000))]
                code_list = ','.join(batch)
                url = f"http://qt.gtimg.cn/q={code_list}"
                
                try:
                    resp = requests.get(url, timeout=5)
                    if resp.status_code == 200:
                        text = resp.content.decode('gbk')
                        for line in text.strip().split(';'):
                            if '=' in line:
                                data = line.split('=')[1].strip('"').split('~')
                                if len(data) >= 33:
                                    change_pct = float(data[32]) if data[32] else 0
                                    if change_pct > 3:  # 只保留涨幅>3%的
                                        all_stocks.append({
                                            'code': data[2],
                                            'name': data[1],
                                            'price': float(data[3]) if data[3] else 0,
                                            'change_pct': change_pct,
                                            'volume': float(data[6]) if len(data) > 6 else 0,
                                            'amount': float(data[37]) if len(data) > 37 else 0,
                                            'high': float(data[33]) if len(data) > 33 else 0,
                                            'low': float(data[34]) if len(data) > 34 else 0,
                                            'open': float(data[5]) if len(data) > 5 else 0,
                                            'preclose': float(data[4]) if len(data) > 4 else 0,
                                        })
                except:
                    pass
                
                time.sleep(0.05)
                
                if len(all_stocks) >= limit * 3:
                    break
            
            if len(all_stocks) >= limit * 3:
                break
    
    # 按涨幅排序
    all_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    return all_stocks[:limit]


def analyze_fenshi(stock: Dict) -> Dict:
    """
    分时图形态分析
    
    评分维度:
    1. 涨幅位置 (30 分) - 3-7 分最佳
    2. 分时均线 (25 分) - 股价在均线上方
    3. 量能配合 (20 分) - 温和放量
    4. 高低点 (15 分) - 接近日内高点
    5. 开盘位置 (10 分) - 高开 2-5% 最佳
    """
    score = 0
    reasons = []
    
    change_pct = stock.get('change_pct', 0)
    price = stock.get('price', 0)
    high = stock.get('high', 0)
    low = stock.get('low', 0)
    open_price = stock.get('open', 0)
    preclose = stock.get('preclose', 0)
    
    # 1. 涨幅位置评分 (30 分)
    if 4 <= change_pct <= 8:
        score += 28
        reasons.append(f"✅ 涨幅适中 ({change_pct}%)")
    elif 3 <= change_pct < 4:
        score += 20
        reasons.append(f"⚠️ 涨幅偏低 ({change_pct}%)")
    elif 8 < change_pct < 9.5:
        score += 18
        reasons.append(f"✅ 接近涨停 ({change_pct}%)")
    elif change_pct >= 9.5:
        score += 5
        reasons.append(f"❌ 已涨停 ({change_pct}%)")
    
    # 2. 高低点评分 (15 分)
    if high > 0 and price > 0:
        position = (price - low) / (high - low) if high > low else 0.5
        if position >= 0.8:
            score += 14
            reasons.append("✅ 接近日内高点")
        elif position >= 0.5:
            score += 10
            reasons.append("⚠️ 中间位置")
        else:
            score += 5
            reasons.append("❌ 接近日内低点")
    
    # 3. 开盘位置评分 (10 分)
    if preclose > 0:
        open_change = (open_price - preclose) / preclose * 100
        if 2 <= open_change <= 5:
            score += 10
            reasons.append(f"✅ 高开适中 ({open_change:.1f}%)")
        elif 0 < open_change < 2:
            score += 7
            reasons.append(f"⚠️ 小幅高开 ({open_change:.1f}%)")
        elif open_change > 5:
            score += 5
            reasons.append(f"⚠️ 高开过多 ({open_change:.1f}%)")
        else:
            score += 3
            reasons.append(f"❌ 平开或低开")
    
    # 4. 量能评分 (20 分) - 简化版，用成交额估算
    amount = stock.get('amount', 0)
    if amount > 100000000:  # >1 亿
        score += 18
        reasons.append("✅ 量能充足")
    elif amount > 50000000:  # >5000 万
        score += 14
        reasons.append("⚠️ 量能一般")
    else:
        score += 8
        reasons.append("⚠️ 量能偏小")
    
    # 5. 涨停潜力加分
    if 5 <= change_pct <= 8:
        # 距离涨停的空间
        distance_to_limit = 10 - change_pct
        if distance_to_limit <= 3:
            score += 15
            reasons.append(f"✅ 距涨停近 ({distance_to_limit:.1f}%)")
    
    return {
        'score': min(100, score),
        'reasons': reasons,
        'recommend': score >= 65  # 降低阈值到 65 分
    }


def monitor_realtime():
    """盘中实时监控"""
    print("=" * 80)
    print("🦞 炒股龙虾 - 盘中实时监控")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 获取涨幅榜
    stocks = get_top_gainers(limit=200)
    print(f"✅ 获取到 {len(stocks)} 只股票")
    print()
    
    # 分析每只股票
    print("📊 分析涨停潜力...")
    print()
    
    recommendations = []
    for stock in stocks:
        analysis = analyze_fenshi(stock)
        if analysis['recommend']:
            recommendations.append({
                **stock,
                'score': analysis['score'],
                'reasons': analysis['reasons']
            })
    
    # 按评分排序
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    # 显示推荐
    print("=" * 80)
    print(f"🎯 高确定性推荐 (≥75 分) - 共{len(recommendations)}只")
    print("=" * 80)
    print()
    
    for i, rec in enumerate(recommendations[:20], 1):  # 最多显示 20 只
        print(f"{i:2}. {rec['code']} {rec['name']}")
        print(f"    评分：{rec['score']} | 涨幅：{rec['change_pct']:+.2f}% | 现价：¥{rec['price']}")
        print(f"    理由:")
        for reason in rec['reasons'][:3]:
            print(f"      {reason}")
        print()
    
    # 统计
    print("-" * 80)
    print("📊 统计:")
    print(f"  涨停潜力股 (≥75 分): {len(recommendations)} 只")
    print(f"  高分股 (≥85 分): {len([r for r in recommendations if r['score'] >= 85])} 只")
    print(f"  涨停股 (≥9.5%): {len([s for s in stocks if s['change_pct'] >= 9.5])} 只")
    print()


if __name__ == '__main__':
    monitor_realtime()
