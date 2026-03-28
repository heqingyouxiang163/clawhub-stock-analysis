#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 涨停股分时图收紧线分析

功能:
- 分析分时图价格收敛程度
- 识别主力控盘强度
- 判断涨停质量
- 评分推荐

收紧线含义:
- 分时价格线越贴近涨停价，收紧越好
- 收紧线越平直，主力控盘越强
- 收紧时间越早，涨停质量越高

使用:
    python3 涨停股收紧线分析.py
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def get_intraday_data(code: str, date: str = None) -> List[Dict]:
    """
    获取个股分时图数据
    
    Args:
        code: 股票代码 (如 sh600773)
        date: 日期
    
    Returns:
        分时数据列表
    """
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    url = f'http://data.gtimg.cn/flashdata/hushen/minute/{code}.js?maxcnt=32000&date={date}'
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            data_points = []
            
            for line in lines:
                if 'data' in line:
                    content = line.split('=')[1].strip().strip('";')
                    points = content.strip('["').strip('"]').split('","')
                    
                    for point in points:
                        parts = point.split(',')
                        if len(parts) >= 3:
                            data_points.append({
                                'time': parts[0],
                                'price': float(parts[1]),
                                'volume': int(parts[2]),
                                'avg_price': float(parts[3]) if len(parts) > 3 else 0,
                            })
            
            return data_points
    except Exception as e:
        print(f'⚠️ 获取 {code} 分时数据失败：{e}')
    
    return []


def analyze_tightening_line(intraday_data: List[Dict], limit_up_price: float) -> Dict:
    """
    分析收紧线形态
    
    Args:
        intraday_data: 分时数据
        limit_up_price: 涨停价
    
    Returns:
        收紧线分析结果
    """
    if not intraday_data:
        return None
    
    # 提取价格数据
    prices = [d['price'] for d in intraday_data]
    avg_prices = [d['avg_price'] for d in intraday_data if d.get('avg_price', 0) > 0]
    times = [d['time'] for d in intraday_data]
    
    # 找到涨停时间
    limit_time_index = None
    for i, price in enumerate(prices):
        if price >= limit_up_price * 0.99:  # 接近涨停
            limit_time_index = i
            break
    
    if limit_time_index is None:
        limit_time_index = len(prices) - 1
    
    # 涨停后的数据
    post_limit_prices = prices[limit_time_index:]
    post_limit_times = times[limit_time_index:]
    
    # 1. 收紧度评分 (0-40 分)
    # 涨停后价格波动越小，收紧度越好
    if len(post_limit_prices) > 1:
        price_range = max(post_limit_prices) - min(post_limit_prices)
        avg_price = sum(post_limit_prices) / len(post_limit_prices)
        tightening_ratio = price_range / avg_price * 100 if avg_price > 0 else 100
        
        if tightening_ratio < 0.5:
            tightening_score = 40
            tightening_level = '极强'
        elif tightening_ratio < 1:
            tightening_score = 35
            tightening_level = '强'
        elif tightening_ratio < 2:
            tightening_score = 25
            tightening_level = '中等'
        elif tightening_ratio < 3:
            tightening_score = 15
            tightening_level = '弱'
        else:
            tightening_score = 5
            tightening_level = '极弱'
    else:
        tightening_score = 40
        tightening_level = '一字板'
    
    # 2. 均线乖离评分 (0-25 分)
    # 价格与均线的乖离率
    if avg_prices and limit_time_index < len(avg_prices):
        post_limit_avg = avg_prices[limit_time_index:]
        if post_limit_avg:
            avg_gap = abs(post_limit_prices[-1] - post_limit_avg[-1]) / post_limit_avg[-1] * 100
            
            if avg_gap < 1:
                avg_score = 25
                avg_level = '强'
            elif avg_gap < 2:
                avg_score = 20
                avg_level = '中等'
            elif avg_gap < 3:
                avg_score = 15
                avg_level = '弱'
            else:
                avg_score = 5
                avg_level = '极弱'
        else:
            avg_score = 20
            avg_level = '中等'
    else:
        avg_score = 20
        avg_level = '中等'
    
    # 3. 涨停时间评分 (0-20 分)
    if limit_time_index < len(times):
        limit_time = times[limit_time_index]
        try:
            hour = int(limit_time[:2])
            minute = int(limit_time[2:4])
            time_minutes = hour * 60 + minute
            
            if time_minutes <= 9 * 60 + 35:  # 9:35 前
                time_score = 20
                time_level = '早盘'
            elif time_minutes <= 10 * 60 + 30:  # 10:30 前
                time_score = 15
                time_level = '盘中'
            elif time_minutes <= 11 * 60 + 30:  # 11:30 前
                time_score = 10
                time_level = '午盘'
            elif time_minutes <= 14 * 60 + 30:  # 14:30 前
                time_score = 5
                time_level = '午后'
            else:
                time_score = 0
                time_level = '尾盘'
        except:
            time_score = 10
            time_level = '未知'
    else:
        time_score = 10
        time_level = '未知'
    
    # 4. 成交量评分 (0-15 分)
    # 涨停后成交量萎缩越好
    if limit_time_index > 0 and limit_time_index < len(intraday_data):
        pre_limit_volume = sum(d['volume'] for d in intraday_data[:limit_time_index])
        post_limit_volume = sum(d['volume'] for d in intraday_data[limit_time_index:])
        
        if pre_limit_volume > 0:
            volume_ratio = post_limit_volume / pre_limit_volume
            
            if volume_ratio < 0.1:
                volume_score = 15
                volume_level = '缩量封板'
            elif volume_ratio < 0.2:
                volume_score = 12
                volume_level = '温和'
            elif volume_ratio < 0.3:
                volume_score = 8
                volume_level = '一般'
            else:
                volume_score = 3
                volume_level = '放量'
        else:
            volume_score = 10
            volume_level = '未知'
    else:
        volume_score = 10
        volume_level = '未知'
    
    # 总分
    total_score = tightening_score + avg_score + time_score + volume_score
    max_score = 100
    
    # 质量评级
    if total_score >= 85:
        quality = '极强'
        recommendation = '✅ 重点参与'
    elif total_score >= 70:
        quality = '强'
        recommendation = '✅ 可参与'
    elif total_score >= 55:
        quality = '中等'
        recommendation = '⚠️ 谨慎参与'
    elif total_score >= 40:
        quality = '弱'
        recommendation = '❌ 建议回避'
    else:
        quality = '极弱'
        recommendation = '❌ 禁止参与'
    
    return {
        'total_score': total_score,
        'quality': quality,
        'recommendation': recommendation,
        'tightening': {
            'score': tightening_score,
            'level': tightening_level,
            'ratio': round(tightening_ratio, 3) if 'tightening_ratio' in dir() else 0
        },
        'avg_price': {
            'score': avg_score,
            'level': avg_level
        },
        'limit_time': {
            'score': time_score,
            'level': time_level,
            'time': times[limit_time_index] if limit_time_index < len(times) else '未知'
        },
        'volume': {
            'score': volume_score,
            'level': volume_level
        }
    }


def analyze_all_limit_up_stocks(date: str = None):
    """
    分析所有涨停股的收紧线
    
    Args:
        date: 日期
    """
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    print('=' * 80)
    print(f'🦞 涨停股分时图收紧线分析')
    print(f'日期：{date}')
    print('=' * 80)
    print()
    
    # 先获取涨停股列表
    import sys
    sys.path.insert(0, '/home/admin/openclaw/workspace/clawhub-stock-analysis/skills/tencent-stock-rank')
    from 盘中实时监控 import get_top_gainers
    
    stocks = get_top_gainers(limit=200)
    limit_up_stocks = [s for s in stocks if s['change_pct'] >= 9.5]
    
    print(f'✅ 找到 {len(limit_up_stocks)} 只涨停股')
    print()
    
    # 分析每只股票
    results = []
    
    for i, stock in enumerate(limit_up_stocks, 1):
        code = stock['code']
        prefix = 'sh' if code.startswith('6') else 'sz'
        full_code = f'{prefix}{code}'
        
        print(f'[{i}/{len(limit_up_stocks)}] 分析 {full_code} {stock["name"]}...')
        
        # 获取分时数据
        intraday = get_intraday_data(full_code, date)
        
        if intraday:
            # 计算涨停价
            preclose = stock.get('preclose', stock['price'] / (1 + stock['change_pct']/100))
            limit_up_price = round(preclose * 1.1, 2)
            
            # 分析收紧线
            analysis = analyze_tightening_line(intraday, limit_up_price)
            
            if analysis:
                results.append({
                    'stock': stock,
                    'code': full_code,
                    'analysis': analysis
                })
                print(f'  评分：{analysis["total_score"]} | 质量：{analysis["quality"]} | {analysis["recommendation"]}')
        
        # 避免请求过快
        time.sleep(0.2)
    
    # 按评分排序
    results.sort(key=lambda x: x['analysis']['total_score'], reverse=True)
    
    print()
    print('=' * 80)
    print('📊 收紧线分析结果')
    print('=' * 80)
    print()
    
    # 统计
    quality_stats = {}
    for r in results:
        q = r['analysis']['quality']
        quality_stats[q] = quality_stats.get(q, 0) + 1
    
    print('质量分布:')
    for q, count in sorted(quality_stats.items(), key=lambda x: x[1], reverse=True):
        ratio = count / len(results) * 100 if results else 0
        print(f'  {q}: {count}只 ({ratio:.1f}%)')
    
    print()
    print('=' * 80)
    print('🎯 重点推荐 (评分≥85)')
    print('=' * 80)
    print()
    
    # 显示高分股票
    high_score = [r for r in results if r['analysis']['total_score'] >= 85]
    
    if high_score:
        for i, r in enumerate(high_score[:10], 1):
            stock = r['stock']
            analysis = r['analysis']
            print(f'{i}. {r["code"]} {stock["name"]}')
            print(f'   评分：{analysis["total_score"]} | 质量：{analysis["quality"]}')
            print(f'   收紧度：{analysis["tightening"]["score"]}分 ({analysis["tightening"]["level"]})')
            print(f'   涨停时间：{analysis["limit_time"]["time"]} ({analysis["limit_time"]["level"]})')
            print(f'   {analysis["recommendation"]}')
            print()
    else:
        print('⚠️ 今日无极强势涨停股')
        print()
    
    # 保存结果
    save_dir = Path('data_cache/limit_up_tightening')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    save_file = save_dir / f'{date}_收紧线分析.json'
    with open(save_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f'✅ 结果已保存：{save_file}')
    print(f'   共分析 {len(results)} 只涨停股')
    print(f'   重点推荐 {len(high_score)} 只')


if __name__ == '__main__':
    import sys
    date = sys.argv[1] if len(sys.argv) > 1 else None
    analyze_all_limit_up_stocks(date)
