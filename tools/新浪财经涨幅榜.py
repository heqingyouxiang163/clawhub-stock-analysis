#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪财经 - 实时涨幅榜获取器
获取沪深主板真实涨幅排名（全市场数据）
"""

import requests
import time
import json


def get_sina_top_gainers(limit=100):
    """
    从新浪财经获取实时涨幅榜
    
    Returns:
        list: 股票列表，包含 code, name, change_pct, current, amount
    """
    try:
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple'
        params = {
            'page': '1',
            'num': str(limit * 2),  # 多获取一些，过滤后可能不够
            'sort': 'changepercent',
            'asc': '0',  # 降序
            'node': 'hs_a',  # 沪深 A 股
        }
        
        headers = {
            'Referer': 'http://vip.stock.finance.sina.com.cn/',
            'User-Agent': 'Mozilla/5.0'
        }
        
        start = time.time()
        response = requests.get(url, params=params, headers=headers, timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            
            # 过滤主板 (60/00 开头，排除 688/300/301)
            stocks = []
            for s in data:
                code = s.get('code', '')
                
                # 只保留主板
                if not (code.startswith('60') or code.startswith('00')):
                    continue
                
                # 排除科创板
                if code.startswith('688'):
                    continue
                
                # 排除创业板
                if code.startswith('30'):
                    continue
                
                change_pct = float(s.get('changepercent', 0) or 0)
                current = float(s.get('trade', 0) or 0)
                amount = float(s.get('turnover', 0) or 0)  # 单位：万
                
                # 排除停牌
                if current == 0:
                    continue
                
                stocks.append({
                    'code': code,
                    'name': s.get('name', '?'),
                    'current': current,
                    'change_pct': change_pct,
                    'amount': amount,
                })
            
            # 按涨幅排序
            stocks.sort(key=lambda x: x['change_pct'], reverse=True)
            
            # 统计
            limit_up = len([s for s in stocks if s['change_pct'] >= 9.5])
            main_rising = len([s for s in stocks if 7 <= s['change_pct'] < 9.5])
            strong = len([s for s in stocks if 5 <= s['change_pct'] < 7])
            
            print(f"✅ 新浪财经涨幅榜：{len(stocks)}只主板股票 ({elapsed*1000:.0f}ms)")
            print(f"   涨停≥9.5%: {limit_up}只 | 主升浪 7-9.5%: {main_rising}只 | 强势 5-7%: {strong}只")
            
            return stocks[:limit]
        else:
            print(f"⚠️ 新浪财经 HTTP {response.status_code}")
    
    except Exception as e:
        print(f"⚠️ 新浪财经失败：{str(e)[:50]}")
    
    return []


def get_stocks_by_range(stocks, min_pct, max_pct):
    """筛选指定涨幅范围的股票"""
    return [s for s in stocks if min_pct <= s['change_pct'] < max_pct]


if __name__ == "__main__":
    stocks = get_sina_top_gainers(100)
    
    print(f"\n{'='*80}")
    print("主板涨幅榜前 30 只:\n")
    
    for i, s in enumerate(stocks[:30], 1):
        flag = '🟢' if s['change_pct'] >= 7 else '🟡' if s['change_pct'] >= 5 else '⚪'
        amount = s['amount'] / 10000  # 亿
        print(f"{flag} {i:2d}. {s['code']} {s['name']:10s} {s['change_pct']:+6.2f}% | 成交：{amount:6.2f}亿")
    
    # 统计 7-9% 主升浪
    main_rising = get_stocks_by_range(stocks, 7, 9.5)
    if main_rising:
        print(f"\n{'='*80}")
        print(f"🎯 主升浪股票 (7-9.5%) 共 {len(main_rising)} 只:\n")
        for s in main_rising[:15]:
            amount = s['amount'] / 10000
            print(f"  {s['code']} {s['name']:10s} {s['change_pct']:+6.2f}% | 成交：{amount:.2f}亿")
