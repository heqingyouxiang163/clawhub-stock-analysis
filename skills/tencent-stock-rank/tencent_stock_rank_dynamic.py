#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
腾讯财经 - A 股实时涨幅榜
用途：动态获取沪深主板所有股票涨幅排名
"""

import requests
import time
from datetime import datetime


def get_all_stock_codes():
    """
    动态获取沪深主板所有股票代码
    
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


def fetch_stocks_in_batches(codes, batch_size=100):
    """
    分批获取股票数据
    
    Args:
        codes: 股票代码列表
        batch_size: 每批数量
    
    Returns:
        list: 股票数据列表
    """
    all_stocks = []
    
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        code_list = ','.join(batch)
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
                                
                                # 只保留上涨的股票
                                if change_pct > 0:
                                    all_stocks.append({
                                        'code': code,
                                        'name': name,
                                        'price': price,
                                        'change_pct': change_pct
                                    })
        except Exception as e:
            print(f"⚠️ 批次 {i//batch_size + 1} 失败：{str(e)[:40]}")
        
        # 避免请求过快
        time.sleep(0.1)
    
    return all_stocks


def get_realtime_rank(limit=100):
    """
    获取实时涨幅榜
    
    Args:
        limit: 获取数量
    
    Returns:
        list: 股票列表
    """
    print(f"🔍 获取沪深主板所有股票...")
    
    # 获取所有股票代码
    all_codes = get_all_stock_codes()
    print(f"📋 共 {len(all_codes)} 只股票")
    
    # 分批获取数据
    print(f"📊 分批获取数据...")
    stocks = fetch_stocks_in_batches(all_codes, batch_size=100)
    
    print(f"✅ 获取到 {len(stocks)} 只上涨股票")
    
    # 按涨幅排序
    stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    return stocks[:limit]


if __name__ == '__main__':
    print("=" * 80)
    print("🦞 腾讯财经 - A 股实时涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # 获取前 100 只
    stocks = get_realtime_rank(limit=100)
    
    print()
    print(f"前 100 只涨幅榜:")
    for i, stock in enumerate(stocks, 1):
        marker = '📸' if stock['code'] in ['600773', '600671', '000688', '002653', '603288', '603507', '002549', '002685', '603806'] else ''
        print(f"{i:2}. {stock['code']} {stock['name']}: ¥{stock['price']}  {stock['change_pct']:+.2f}% {marker}")
    
    print()
    print("-" * 80)
    print("截图中的股票排名:")
    target_codes = ['600773', '600671', '000688', '002653', '603288', '603507', '002549', '002685', '603806']
    for stock in stocks:
        if stock['code'] in target_codes:
            rank = stocks.index(stock) + 1
            print(f"排名{rank}: {stock['code']} {stock['name']}: ¥{stock['price']}  {stock['change_pct']:+.2f}%")
