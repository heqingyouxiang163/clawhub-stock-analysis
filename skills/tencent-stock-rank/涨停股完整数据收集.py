#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 沪深主板涨停股完整数据收集

功能:
- 收集两周所有沪深主板涨停股
- 包含分时图、均线、连板数等
- 保存到 data_cache/limit_up_complete/

使用:
    python3 涨停股完整数据收集.py 20260317 20260328
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict


def get_all_limit_up_stocks(date: str) -> List[Dict]:
    """
    获取指定日期所有涨停股
    
    Args:
        date: 日期 (如 20260321)
    
    Returns:
        涨停股列表
    """
    print(f'  获取 {date} 涨停股...')
    
    # 东方财富涨停池接口
    url = f'http://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&Pagesize=10000&Sort=fbt:asc&date={date}&_=1711000000000'
    
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data.get('success'):
            stocks = data.get('data', {}).get('pool', [])
            print(f'  ✅ {len(stocks)}只涨停股')
            return stocks
        else:
            print(f'  ⚠️ 接口返回失败')
            return []
    except Exception as e:
        print(f'  ❌ 获取失败：{e}')
        return []


def get_intraday_data(code: str, date: str) -> Dict:
    """
    获取分时图数据 (含均线)
    
    Args:
        code: 股票代码
        date: 日期
    
    Returns:
        分时数据
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
                                'time': parts[0],
                                'price': float(parts[1]),
                                'volume': int(parts[2]),
                                'avg_price': float(parts[3]),
                            })
            
            return {
                'code': code,
                'data': data_points,
                'count': len(data_points)
            }
    except:
        pass
    
    return None


def analyze_stock(stock: dict, intraday: dict) -> dict:
    """
    分析个股
    
    Args:
        stock: 涨停股数据
        intraday: 分时数据
    
    Returns:
        分析结果
    """
    info = stock.get('info', {})
    
    # 基础数据
    code = info.get('code', '')
    name = info.get('name', '')
    change_rate = info.get('hsl', 0)
    open_count = info.get('zcCount', 0)
    limit_count = info.get('zc', 1)
    limit_time = info.get('fbt', '')
    amount = info.get('amount', 0)
    close = info.get('price', 0)
    
    # 分时均线分析
    avg_line_analysis = None
    if intraday and intraday.get('data'):
        data_points = intraday['data']
        prices = [d['price'] for d in data_points]
        avg_prices = [d['avg_price'] for d in data_points if d.get('avg_price', 0) > 0]
        
        if avg_prices:
            # 均线上方占比
            above_avg = sum(1 for p in prices if p > avg_prices[0]) / len(prices) * 100
            
            # 均线支撑次数
            support_count = 0
            for i in range(10, len(prices)):
                if prices[i-1] < avg_prices[0] and prices[i] > avg_prices[0]:
                    support_count += 1
            
            # 乖离率
            avg_gap = sum(abs(p - avg_prices[0]) / avg_prices[0] * 100 for p in prices) / len(prices)
            
            avg_line_analysis = {
                'above_avg_ratio': round(above_avg, 1),
                'support_count': support_count,
                'avg_gap': round(avg_gap, 2)
            }
    
    return {
        'code': code,
        'name': name,
        'change_rate': change_rate,
        'open_count': open_count,
        'limit_count': limit_count,
        'limit_time': limit_time,
        'amount': amount,
        'close': close,
        'avg_line': avg_line_analysis,
        'intraday_count': intraday['count'] if intraday else 0
    }


def collect_all_dates(start_date: str, end_date: str):
    """
    批量收集多个日期
    """
    print('=' * 80)
    print('🦞 沪深主板涨停股完整数据收集')
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
    for d in dates:
        print(f'   {d}')
    
    # 保存目录
    save_dir = Path('data_cache/limit_up_complete')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 收集数据
    all_stocks = []
    
    for date in dates:
        print(f'\n[{dates.index(date)+1}/{len(dates)}] {date}')
        
        # 获取涨停股
        stocks = get_all_limit_up_stocks(date)
        
        if not stocks:
            continue
        
        # 分析每只股票
        date_results = []
        
        for i, stock in enumerate(stocks, 1):
            info = stock.get('info', {})
            code = info.get('code', '')
            
            if not code:
                continue
            
            # 添加前缀
            prefix = 'sh' if code.startswith('6') else 'sz'
            full_code = f'{prefix}{code}'
            
            # 获取分时数据 (每 10 只获取 1 次，避免请求过快)
            intraday = None
            if i % 10 == 0:
                intraday = get_intraday_data(full_code, date)
                time.sleep(0.1)
            
            # 分析
            analysis = analyze_stock(stock, intraday)
            analysis['date'] = date
            date_results.append(analysis)
            all_stocks.append(analysis)
        
        # 保存当日数据
        if date_results:
            date_file = save_dir / f'{date}.json'
            with open(date_file, 'w', encoding='utf-8') as f:
                json.dump(date_results, f, ensure_ascii=False, indent=2)
            
            print(f'  ✅ 已保存 {len(date_results)}只')
        
        # 间隔
        time.sleep(1)
    
    # 汇总统计
    print('\n' + '=' * 80)
    print('📊 汇总统计')
    print('=' * 80)
    
    total = len(all_stocks)
    print(f'\n总涨停股数：{total}只')
    
    # 连板统计
    limit_stocks = [s for s in all_stocks if s['limit_count'] >= 2]
    print(f'连板股：{len(limit_stocks)}只 ({len(limit_stocks)/total*100:.1f}%)')
    
    # 分时数据获取情况
    with_intraday = [s for s in all_stocks if s['avg_line'] is not None]
    print(f'有分时数据：{len(with_intraday)}只 ({len(with_intraday)/total*100:.1f}%)')
    
    # 保存汇总
    summary = {
        'period': f'{start_date} 至 {end_date}',
        'total_days': len(dates),
        'total_stocks': total,
        'limit_stocks': len(limit_stocks),
        'with_intraday': len(with_intraday),
        'data': all_stocks
    }
    
    summary_file = save_dir / '汇总数据.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ 汇总数据已保存：{summary_file}')


if __name__ == '__main__':
    import sys
    
    start_date = sys.argv[1] if len(sys.argv) > 1 else '20260317'
    end_date = sys.argv[2] if len(sys.argv) > 2 else '20260328'
    
    collect_all_dates(start_date, end_date)
