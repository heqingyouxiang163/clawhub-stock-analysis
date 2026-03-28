#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 涨停股分时均线数据收集

功能:
- 收集涨停股的分时均线数据
- 分析均线支撑强度
- 保存均线形态特征
- 用于推荐系统

使用:
    python3 涨停股分时均线收集.py 20260317 20260328
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


def get_intraday_data(code: str, date: str) -> List[Dict]:
    """
    获取个股分时图数据 (含均线)
    
    Args:
        code: 股票代码 (如 sh600773)
        date: 日期 (如 20260321)
    
    Returns:
        分时数据列表 (含均线)
    """
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
                                'time': parts[0],  # 时间 (093000)
                                'price': float(parts[1]),  # 价格
                                'volume': int(parts[2]),  # 成交量
                                'avg_price': float(parts[3]),  # 分时均价
                            })
            
            return data_points
    except Exception as e:
        pass
    
    return []


def analyze_avg_line_support(data_points: List[Dict]) -> Dict:
    """
    分析分时均线支撑强度
    
    Args:
        data_points: 分时数据
    
    Returns:
        均线支撑分析结果
    """
    if not data_points or len(data_points) < 10:
        return None
    
    # 提取价格和均线
    prices = [d['price'] for d in data_points]
    avg_prices = [d['avg_price'] for d in data_points if d.get('avg_price', 0) > 0]
    
    if not avg_prices:
        return None
    
    # 1. 均线上方运行时间占比
    above_avg_count = sum(1 for p in prices if p > avg_prices[0])
    above_avg_ratio = above_avg_count / len(prices) * 100
    
    # 2. 均线支撑次数 (价格回踩均线后反弹)
    support_count = 0
    for i in range(10, len(prices)):
        if prices[i-1] < avg_prices[0] and prices[i] > avg_prices[0]:
            support_count += 1
    
    # 3. 均线乖离率
    max_gap = max(abs(p - avg_prices[0]) / avg_prices[0] * 100 for p in prices)
    avg_gap = sum(abs(p - avg_prices[0]) / avg_prices[0] * 100 for p in prices) / len(prices)
    
    # 4. 均线方向
    if len(avg_prices) >= 2:
        avg_trend = '向上' if avg_prices[-1] > avg_prices[0] else '向下' if avg_prices[-1] < avg_prices[0] else '走平'
    else:
        avg_trend = '未知'
    
    # 5. 均线评分 (0-100)
    score = 50  # 基础分
    
    # 均线上方运行加分
    if above_avg_ratio > 80:
        score += 30
    elif above_avg_ratio > 60:
        score += 20
    elif above_avg_ratio > 40:
        score += 10
    
    # 均线支撑加分
    if support_count >= 3:
        score += 20
    elif support_count >= 2:
        score += 15
    elif support_count >= 1:
        score += 10
    
    # 乖离率加分 (越小越好)
    if avg_gap < 1:
        score += 20
    elif avg_gap < 2:
        score += 15
    elif avg_gap < 3:
        score += 10
    
    # 均线方向加分
    if avg_trend == '向上':
        score += 10
    
    score = min(100, score)
    
    # 质量评级
    if score >= 85:
        quality = '极强'
        recommendation = '✅ 重点参与'
    elif score >= 70:
        quality = '强'
        recommendation = '✅ 可参与'
    elif score >= 55:
        quality = '中等'
        recommendation = '⚠️ 谨慎'
    else:
        quality = '弱'
        recommendation = '❌ 回避'
    
    return {
        'score': score,
        'quality': quality,
        'recommendation': recommendation,
        'above_avg_ratio': round(above_avg_ratio, 1),
        'support_count': support_count,
        'max_gap': round(max_gap, 2),
        'avg_gap': round(avg_gap, 2),
        'avg_trend': avg_trend
    }


def collect_limit_up_intraday(start_date: str, end_date: str):
    """
    收集涨停股的分时均线数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    """
    print('=' * 80)
    print('🦞 涨停股分时均线数据收集')
    print(f'日期范围：{start_date} 至 {end_date}')
    print('=' * 80)
    
    # 生成日期列表 (排除周末)
    dates = []
    current = datetime.strptime(start_date, '%Y%m%d')
    end = datetime.strptime(end_date, '%Y%m%d')
    
    while current <= end:
        if current.weekday() < 5:
            dates.append(current.strftime('%Y%m%d'))
        current += timedelta(days=1)
    
    print(f'\n📅 交易日：{len(dates)}天')
    
    # 保存目录
    save_dir = Path('data_cache/limit_up_avg_line')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取涨停股列表 (从已有数据)
    import sys
    sys.path.insert(0, '/home/admin/openclaw/workspace/clawhub-stock-analysis/skills/tencent-stock-rank')
    from 盘中实时监控 import get_top_gainers
    
    total_stocks = 0
    total_analyzed = 0
    
    for date in dates:
        print(f'\n[{dates.index(date)+1}/{len(dates)}] {date}')
        
        # 获取涨停股
        stocks = get_top_gainers(limit=200)
        limit_up_stocks = [s for s in stocks if s['change_pct'] >= 9.5]
        
        print(f'  找到 {len(limit_up_stocks)} 只涨停股')
        
        if not limit_up_stocks:
            continue
        
        # 分析每只涨停股
        date_results = []
        
        for i, stock in enumerate(limit_up_stocks, 1):
            code = stock['code']
            prefix = 'sh' if code.startswith('6') else 'sz'
            full_code = f'{prefix}{code}'
            
            # 获取分时数据
            data_points = get_intraday_data(full_code, date)
            
            if data_points:
                # 分析均线支撑
                avg_analysis = analyze_avg_line_support(data_points)
                
                if avg_analysis:
                    date_results.append({
                        'stock': stock,
                        'code': full_code,
                        'avg_line_analysis': avg_analysis,
                        'data_points_count': len(data_points)
                    })
                    total_analyzed += 1
        
        # 保存当日数据
        if date_results:
            date_file = save_dir / f'{date}_分时均线.json'
            with open(date_file, 'w', encoding='utf-8') as f:
                json.dump(date_results, f, ensure_ascii=False, indent=2)
            
            print(f'  ✅ 已保存 {len(date_results)} 只涨停股分时均线数据')
            total_stocks += len(date_results)
        
        # 间隔
        time.sleep(1)
    
    # 汇总统计
    print('\n' + '=' * 80)
    print('📊 汇总统计')
    print('=' * 80)
    
    print(f'\n总涨停股数：{total_stocks}只')
    print(f'已分析：{total_analyzed}只')
    
    # 质量分布
    quality_stats = {}
    score_list = []
    
    # 读取所有分析结果
    all_results = []
    for date_file in save_dir.glob('*_分时均线.json'):
        with open(date_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_results.extend(data)
    
    for r in all_results:
        q = r['avg_line_analysis']['quality']
        quality_stats[q] = quality_stats.get(q, 0) + 1
        score_list.append(r['avg_line_analysis']['score'])
    
    print('\n均线质量分布:')
    for q, count in sorted(quality_stats.items(), key=lambda x: x[1], reverse=True):
        ratio = count / len(all_results) * 100 if all_results else 0
        print(f'  {q}: {count}只 ({ratio:.1f}%)')
    
    if score_list:
        print(f'\n平均评分：{sum(score_list)/len(score_list):.1f}分')
        print(f'最高评分：{max(score_list)}分')
        print(f'最低评分：{min(score_list)}分')
    
    # 保存汇总
    summary = {
        'period': f'{start_date} 至 {end_date}',
        'total_days': len(dates),
        'total_stocks': total_stocks,
        'analyzed': total_analyzed,
        'quality_stats': quality_stats,
        'avg_score': sum(score_list)/len(score_list) if score_list else 0,
        'max_score': max(score_list) if score_list else 0,
        'min_score': min(score_list) if score_list else 0
    }
    
    summary_file = save_dir / '汇总统计.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ 汇总统计已保存：{summary_file}')


if __name__ == '__main__':
    import sys
    
    start_date = sys.argv[1] if len(sys.argv) > 1 else '20260317'
    end_date = sys.argv[2] if len(sys.argv) > 2 else '20260328'
    
    collect_limit_up_intraday(start_date, end_date)
