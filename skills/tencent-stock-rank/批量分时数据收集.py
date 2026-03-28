#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 批量分时图数据收集

功能:
- 批量收集指定日期范围的分时图数据
- 支持沪深主板所有股票
- 保存到 data_cache/intraday/

使用:
    python3 批量分时数据收集.py 20260317 20260328
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path


def get_all_stock_codes():
    """
    获取沪深主板所有股票代码
    
    Returns:
        list: 股票代码列表
    """
    stock_codes = []
    
    # 沪市主板：600xxx, 601xxx, 603xxx, 605xxx
    for prefix in ['600', '601', '603', '605']:
        for i in range(1000):
            code = f'sh{prefix}{i:03d}'
            stock_codes.append(code)
    
    # 深市主板：000xxx, 001xxx, 002xxx, 003xxx
    for prefix in ['000', '001', '002', '003']:
        for i in range(1000):
            code = f'sz{prefix}{i:03d}'
            stock_codes.append(code)
    
    return stock_codes


def get_intraday_data(code: str, date: str) -> dict:
    """
    获取个股分时图数据
    
    Args:
        code: 股票代码 (如 sh600773)
        date: 日期 (如 20260321)
    
    Returns:
        分时图数据
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
                        if len(parts) >= 3:
                            data_points.append({
                                'time': parts[0],
                                'price': float(parts[1]),
                                'volume': int(parts[2]),
                            })
            
            if data_points:
                return {
                    'code': code,
                    'date': date,
                    'data': data_points,
                    'count': len(data_points)
                }
    except:
        pass
    
    return None


def collect_intraday_for_date(date: str, stock_codes: list, save_dir: Path):
    """
    收集指定日期的分时图数据
    
    Args:
        date: 日期
        stock_codes: 股票代码列表
        save_dir: 保存目录
    """
    print(f'\n📅 收集 {date} 分时图数据...')
    
    date_dir = save_dir / date
    date_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    # 分批获取，每批 100 只
    batch_size = 100
    
    for i in range(0, min(len(stock_codes), 1000), batch_size):  # 限制 1000 只测试
        batch = stock_codes[i:i+batch_size]
        
        print(f'  批次 {i//batch_size + 1}: 获取 {len(batch)} 只股票...', end=' ')
        
        batch_data = []
        
        for code in batch:
            data = get_intraday_data(code, date)
            if data and data['count'] > 0:
                batch_data.append(data)
                success_count += 1
            else:
                fail_count += 1
            
            # 避免请求过快
            time.sleep(0.02)
        
        # 保存批次数据
        if batch_data:
            batch_file = date_dir / f'batch_{i//batch_size + 1}.json'
            with open(batch_file, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, ensure_ascii=False)
            print(f'✅ {len(batch_data)}只成功')
        else:
            print('❌ 无数据')
        
        # 批次间隔
        time.sleep(0.5)
    
    # 保存统计
    stats = {
        'date': date,
        'total_stocks': len(stock_codes),
        'success': success_count,
        'fail': fail_count,
        'success_rate': f'{success_count/(success_count+fail_count)*100:.1f}%' if (success_count+fail_count) > 0 else '0%'
    }
    
    stats_file = date_dir / 'stats.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ {date} 完成：{success_count}只成功，{fail_count}只失败，成功率 {stats["success_rate"]}')


def collect_all_dates(start_date: str, end_date: str):
    """
    批量收集多个日期的分时图数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    """
    print('=' * 80)
    print('🦞 批量分时图数据收集')
    print(f'日期范围：{start_date} 至 {end_date}')
    print('=' * 80)
    
    # 生成日期列表 (排除周末)
    dates = []
    current = datetime.strptime(start_date, '%Y%m%d')
    end = datetime.strptime(end_date, '%Y%m%d')
    
    while current <= end:
        if current.weekday() < 5:  # 周一到周五
            dates.append(current.strftime('%Y%m%d'))
        current += timedelta(days=1)
    
    print(f'\n📅 交易日：{len(dates)}天')
    for d in dates:
        print(f'   {d}')
    
    # 获取股票代码列表
    print(f'\n🔍 获取股票代码列表...')
    stock_codes = get_all_stock_codes()
    print(f'   共 {len(stock_codes)} 只股票')
    
    # 保存目录
    save_dir = Path('data_cache/intraday')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 批量收集
    for date in dates:
        collect_intraday_for_date(date, stock_codes, save_dir)
        
        # 每天间隔
        time.sleep(2)
    
    # 汇总统计
    print('\n' + '=' * 80)
    print('📊 汇总统计')
    print('=' * 80)
    
    total_success = 0
    total_fail = 0
    
    for date in dates:
        date_dir = save_dir / date
        stats_file = date_dir / 'stats.json'
        
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                total_success += stats['success']
                total_fail += stats['fail']
                print(f'{date}: {stats["success"]}只成功，{stats["fail"]}只失败 ({stats["success_rate"]})')
    
    print()
    print(f'总计：{total_success}只成功，{total_fail}只失败')
    print(f'平均成功率：{total_success/(total_success+total_fail)*100:.1f}%' if (total_success+total_fail) > 0 else '0%')
    
    # 保存总统计
    total_stats = {
        'start_date': start_date,
        'end_date': end_date,
        'total_days': len(dates),
        'total_success': total_success,
        'total_fail': total_fail,
        'avg_success_rate': f'{total_success/(total_success+total_fail)*100:.1f}%' if (total_success+total_fail) > 0 else '0%'
    }
    
    total_stats_file = save_dir / '汇总统计.json'
    with open(total_stats_file, 'w', encoding='utf-8') as f:
        json.dump(total_stats, f, ensure_ascii=False, indent=2)
    
    print(f'\n✅ 汇总统计已保存：{total_stats_file}')


if __name__ == '__main__':
    import sys
    
    start_date = sys.argv[1] if len(sys.argv) > 1 else '20260317'
    end_date = sys.argv[2] if len(sys.argv) > 2 else '20260328'
    
    collect_all_dates(start_date, end_date)
