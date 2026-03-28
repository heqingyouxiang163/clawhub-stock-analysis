#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
腾讯财经 - A 股实时涨幅榜 (动态前 200 只)
用途：快速获取沪深主板前 200 只涨幅榜
"""

import requests
import time
from datetime import datetime


def fetch_batch(codes):
    """
    获取一批股票数据
    
    Args:
        codes: 股票代码列表
    
    Returns:
        list: 股票数据列表
    """
    stocks = []
    code_list = ','.join(codes)
    url = f"http://qt.gtimg.cn/q={code_list}"
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            text = response.content.decode('gbk')
            lines = text.strip().split(';')
            
            for line in lines:
                if '=' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        data = parts[1].strip('"').split('~')
                        if len(data) >= 33:
                            code = data[2]
                            name = data[1]
                            price = float(data[3]) if data[3] else 0
                            change_pct = float(data[32]) if data[32] else 0
                            
                            if change_pct > 0:
                                stocks.append({
                                    'code': code,
                                    'name': name,
                                    'price': price,
                                    'change_pct': change_pct
                                })
    except Exception as e:
        print(f"⚠️ 获取失败：{str(e)[:40]}")
    
    return stocks


def get_top_gainers(limit=200):
    """
    获取前 N 只涨幅榜 (动态获取)
    
    Args:
        limit: 获取数量
    
    Returns:
        list: 股票列表
    """
    print(f"🔍 动态获取沪深主板前 {limit} 只涨幅榜...")
    
    # 分批获取，每批 100 只
    batch_size = 100
    all_stocks = []
    
    # 沪市：600, 601, 603, 605
    sh_batches = []
    for prefix in ['600', '601', '603', '605']:
        for i in range(0, 1000, batch_size):
            batch = [f'sh{prefix}{j:03d}' for j in range(i, min(i+batch_size, 1000))]
            sh_batches.append(batch)
    
    # 深市：000, 001, 002, 003
    sz_batches = []
    for prefix in ['000', '001', '002', '003']:
        for i in range(0, 1000, batch_size):
            batch = [f'sz{prefix}{j:03d}' for j in range(i, min(i+batch_size, 1000))]
            sz_batches.append(batch)
    
    # 交替获取沪深两市
    print(f"📊 分批获取数据...")
    for i in range(max(len(sh_batches), len(sz_batches))):
        # 获取沪市
        if i < len(sh_batches):
            stocks = fetch_batch(sh_batches[i])
            all_stocks.extend(stocks)
            print(f"  批次 {i*2+1}: 获取 {len(stocks)} 只上涨股票")
        
        # 获取深市
        if i < len(sz_batches):
            stocks = fetch_batch(sz_batches[i])
            all_stocks.extend(stocks)
            print(f"  批次 {i*2+2}: 获取 {len(stocks)} 只上涨股票")
        
        # 每批间隔
        time.sleep(0.1)
        
        # 如果已经获取足够多的上涨股票，提前结束
        if len(all_stocks) >= limit * 3:
            print(f"  ✅ 已获取足够的上涨股票 ({len(all_stocks)} 只)")
            break
    
    # 按涨幅排序
    all_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    result = all_stocks[:limit]
    print(f"✅ 获取到 {len(result)} 只涨幅榜股票")
    
    return result


if __name__ == '__main__':
    print("=" * 80)
    print("🦞 腾讯财经 - A 股实时涨幅榜 (动态前 200)")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 获取前 200 只
    stocks = get_top_gainers(limit=200)
    
    print()
    print(f"前 100 只涨幅榜:")
    for i, stock in enumerate(stocks[:100], 1):
        marker = '📸' if stock['code'] in ['600773', '600671', '000688', '002653', '603288', '603507', '002549', '002685', '603806'] else ''
        print(f"{i:2}. {stock['code']} {stock['name']}: ¥{stock['price']}  {stock['change_pct']:+.2f}% {marker}")
    
    print()
    print("-" * 80)
    print("截图中的股票排名:")
    target_codes = ['600773', '600671', '000688', '002653', '603288', '603507', '002549', '002685', '603806']
    for stock in stocks[:100]:
        if stock['code'] in target_codes:
            rank = stocks[:100].index(stock) + 1
            print(f"排名{rank}: {stock['code']} {stock['name']}: ¥{stock['price']}  {stock['change_pct']:+.2f}%")
