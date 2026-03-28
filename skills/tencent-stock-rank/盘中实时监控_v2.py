#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 炒股龙虾 - 盘中实时监控 v2.0 (分时均线增强版)

功能:
- 实时获取涨幅榜前 200
- 分时图形态分析
- 分时均线支撑分析 (权重 40%)
- 涨停潜力评分
- 高确定性推荐 (≥70 分)

更新:
- 分时均线权重提升到 40%
- 收紧线分析权重 25%
- 涨幅位置权重 20%
- 量能配合权重 15%

使用:
    python3 盘中实时监控_v2.py
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
                                    if change_pct > 3:
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
    
    all_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    return all_stocks[:limit]


def get_intraday_data(code: str) -> List[Dict]:
    """获取分时数据 (含均线)"""
    date = datetime.now().strftime('%Y%m%d')
    url = f'http://data.gtimg.cn/flashdata/hushen/minute/{code}.js?maxcnt=32000&date={date}'
    
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            data_points = []
            
            for line in lines:
                if 'data' in line:
                    content = line.split('=')[1].strip().strip('";')
                    points = content.strip('["').strip('"]').split('","')
                    
                    for point in points:
                        parts = point.split(',')
                        if len(parts) >= 4:
                            data_points.append({
                                'time': parts[0],
                                'price': float(parts[1]),
                                'volume': int(parts[2]),
                                'avg_price': float(parts[3]),
                            })
            
            return data_points
    except:
        pass
    
    return []


def analyze_avg_line(data_points: List[Dict]) -> Dict:
    """
    分时均线分析 (权重 40%)
    
    评分维度:
    1. 均线上方运行时间占比 (15 分)
    2. 均线支撑次数 (15 分)
    3. 均线乖离率 (10 分)
    """
    if not data_points or len(data_points) < 10:
        return {'score': 0, 'level': '无数据'}
    
    prices = [d['price'] for d in data_points]
    avg_prices = [d['avg_price'] for d in data_points if d.get('avg_price', 0) > 0]
    
    if not avg_prices:
        return {'score': 0, 'level': '无数据'}
    
    score = 0
    
    # 1. 均线上方运行时间占比 (15 分)
    above_avg_count = sum(1 for p in prices if p > avg_prices[0])
    above_avg_ratio = above_avg_count / len(prices) * 100
    
    if above_avg_ratio > 80:
        score += 15
        avg_level = '极强'
    elif above_avg_ratio > 60:
        score += 12
        avg_level = '强'
    elif above_avg_ratio > 40:
        score += 8
        avg_level = '中等'
    else:
        score += 3
        avg_level = '弱'
    
    # 2. 均线支撑次数 (15 分)
    support_count = 0
    for i in range(10, len(prices)):
        if prices[i-1] < avg_prices[0] and prices[i] > avg_prices[0]:
            support_count += 1
    
    if support_count >= 3:
        score += 15
    elif support_count >= 2:
        score += 12
    elif support_count >= 1:
        score += 8
    else:
        score += 3
    
    # 3. 均线乖离率 (10 分)
    avg_gap = sum(abs(p - avg_prices[0]) / avg_prices[0] * 100 for p in prices) / len(prices)
    
    if avg_gap < 1:
        score += 10
    elif avg_gap < 2:
        score += 8
    elif avg_gap < 3:
        score += 5
    else:
        score += 2
    
    return {
        'score': score,
        'level': avg_level,
        'above_avg_ratio': round(above_avg_ratio, 1),
        'support_count': support_count,
        'avg_gap': round(avg_gap, 2)
    }


def analyze_fenshi_v2(stock: Dict, data_points: List[Dict]) -> Dict:
    """
    分时图分析 v2.0 (均线权重 40%)
    
    评分维度:
    1. 分时均线 (40 分) - 权重最高
    2. 收紧线 (25 分) - 涨停后收敛
    3. 涨幅位置 (20 分) - 4-8% 最佳
    4. 量能配合 (15 分) - 成交额>1 亿
    """
    score = 0
    reasons = []
    
    change_pct = stock.get('change_pct', 0)
    price = stock.get('price', 0)
    high = stock.get('high', 0)
    low = stock.get('low', 0)
    amount = stock.get('amount', 0)
    
    # ========== 1. 分时均线分析 (40 分) ==========
    avg_analysis = analyze_avg_line(data_points)
    avg_score = avg_analysis['score']
    score += avg_score
    reasons.append(f"均线：{avg_analysis['level']} ({avg_score}/40)")
    
    # ========== 2. 收紧线分析 (25 分) ==========
    if high > 0 and price > 0:
        position = (price - low) / (high - low) if high > low else 0.5
        if position >= 0.8:
            score += 23
            reasons.append(f"收紧线：强 (23/25)")
        elif position >= 0.5:
            score += 18
            reasons.append(f"收紧线：中等 (18/25)")
        else:
            score += 10
            reasons.append(f"收紧线：弱 (10/25)")
    
    # ========== 3. 涨幅位置 (20 分) ==========
    if 4 <= change_pct <= 8:
        score += 18
        reasons.append(f"涨幅：适中 ({change_pct}%)")
    elif 8 < change_pct < 9.5:
        score += 15
        reasons.append(f"涨幅：接近涨停 ({change_pct}%)")
    elif 3 <= change_pct < 4:
        score += 12
        reasons.append(f"涨幅：偏低 ({change_pct}%)")
    else:
        score += 5
    
    # ========== 4. 量能配合 (15 分) ==========
    if amount > 100000000:
        score += 14
        reasons.append(f"量能：充足")
    elif amount > 50000000:
        score += 10
        reasons.append(f"量能：一般")
    else:
        score += 6
        reasons.append(f"量能：偏小")
    
    # 总分 (满分 100)
    score = min(100, score)
    
    # 推荐阈值
    if score >= 85:
        recommend = True
        level = '极强'
    elif score >= 70:
        recommend = True
        level = '强'
    elif score >= 60:
        recommend = False
        level = '中等'
    else:
        recommend = False
        level = '弱'
    
    return {
        'score': score,
        'level': level,
        'recommend': recommend,
        'reasons': reasons,
        'avg_line_score': avg_score
    }


def monitor_realtime_v2():
    """盘中实时监控 v2.0 (分时均线增强)"""
    print("=" * 80)
    print("🦞 炒股龙虾 - 盘中实时监控 v2.0 (分时均线增强)")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 获取涨幅榜
    stocks = get_top_gainers(limit=200)
    print(f"✅ 获取到 {len(stocks)} 只股票")
    print()
    
    # 分析每只股票
    print("📊 分析分时均线 + 涨停潜力...")
    print()
    
    recommendations = []
    
    for stock in stocks:
        code = stock['code']
        prefix = 'sh' if code.startswith('6') else 'sz'
        full_code = f'{prefix}{code}'
        
        # 获取分时数据
        data_points = get_intraday_data(full_code)
        
        # 分析
        analysis = analyze_fenshi_v2(stock, data_points)
        
        if analysis['recommend']:
            recommendations.append({
                **stock,
                'score': analysis['score'],
                'level': analysis['level'],
                'reasons': analysis['reasons'],
                'avg_line_score': analysis['avg_line_score']
            })
    
    # 按评分排序
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    # 显示推荐
    print("=" * 80)
    print(f"🎯 高确定性推荐 (≥70 分) - 共{len(recommendations)}只")
    print("=" * 80)
    print()
    
    for i, rec in enumerate(recommendations[:20], 1):
        print(f"{i:2}. {rec['code']} {rec['name']}")
        print(f"    评分：{rec['score']} | 等级：{rec['level']} | 涨幅：{rec['change_pct']:+.2f}% | 现价：¥{rec['price']}")
        print(f"    分时均线：{rec['avg_line_score']}/40")
        print(f"    理由:")
        for reason in rec['reasons'][:4]:
            print(f"      • {reason}")
        print()
    
    # 统计
    print("-" * 80)
    print("📊 统计:")
    print(f"  推荐股数：{len(recommendations)}只")
    print(f"  极强 (≥85 分): {len([r for r in recommendations if r['score'] >= 85])}只")
    print(f"  强 (70-84 分): {len([r for r in recommendations if 70 <= r['score'] < 85])}只")
    print(f"  涨停股 (≥9.5%): {len([s for s in stocks if s['change_pct'] >= 9.5])}只")
    print()
    
    # 均线质量统计
    avg_scores = [r['avg_line_score'] for r in recommendations]
    if avg_scores:
        print(f"  平均均线评分：{sum(avg_scores)/len(avg_scores):.1f}/40")
        print(f"  均线极强 (>35 分): {len([s for s in avg_scores if s > 35])}只")
        print(f"  均线强 (28-35 分): {len([s for s in avg_scores if 28 <= s <= 35])}只")


if __name__ == '__main__':
    monitor_realtime_v2()
