#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富网页版 - 获取全市场涨幅榜
通过模拟浏览器请求获取完整数据
"""

import requests
import json
from datetime import datetime


def get_full_market_rank():
    """
    从东方财富网页版获取完整涨幅榜
    
    使用多个接口并行获取：
    1. 沪市 A 股
    2. 深市 A 股
    3. 创业板
    4. 科创板
    """
    
    all_stocks = []
    
    # 市场配置
    markets = [
        {'name': '沪市 A 股', 'fs': 'm:1 t:2', 'count': 0},  # 沪市主板
        {'name': '深市主板', 'fs': 'm:0 t:2', 'count': 0},  # 深市主板
        {'name': '创业板', 'fs': 'm:0 t:80', 'count': 0},
        {'name': '科创板', 'fs': 'm:1 t:81', 'count': 0},
    ]
    
    for market in markets:
        print(f"📊 获取 {market['name']}...")
        
        page = 1
        while True:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': page,
                'pz': 500,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': market['fs'],
                'fields': 'f12,f14,f3,f11,f17,f18,f19,f20,f37,f38'
            }
            
            try:
                response = requests.get(url, params=params, timeout=10, 
                                       headers={'User-Agent': 'Mozilla/5.0'})
                
                if response.status_code != 200:
                    print(f"  ⚠️ HTTP {response.status_code}")
                    break
                
                data = response.json()
                
                if data.get('data') and data['data'].get('diff'):
                    stocks = data['data']['diff']
                    
                    for s in stocks:
                        code = s.get('f12', '')
                        name = s.get('f14', '?')
                        change_pct = s.get('f3', 0)
                        current = s.get('f20', 0)
                        
                        if current > 0 and name and name != '-':
                            all_stocks.append({
                                'code': code,
                                'name': name,
                                'change_pct': change_pct,
                                'current': current,
                                'market': market['name']
                            })
                    
                    market['count'] += len(stocks)
                    print(f"  第{page}页：{len(stocks)}只 (累计{market['count']}只)")
                    
                    if len(stocks) < 500:
                        break
                    
                    page += 1
                else:
                    break
                    
            except Exception as e:
                print(f"  ⚠️ 失败：{str(e)[:40]}")
                break
            
            import time
            time.sleep(0.3)
    
    return all_stocks


def is_main_board(code):
    """判断是否沪深主板"""
    if code.startswith('6'):
        return code[:3] in ['600', '601', '603', '605']
    elif code.startswith('0'):
        return code[:3] in ['000', '001', '002', '003']
    return False


def main():
    print("=" * 75)
    print("🦞 东方财富网页版 - 全市场涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 获取数据
    all_stocks = get_full_market_rank()
    
    if not all_stocks:
        print("\n❌ 获取失败")
        return
    
    print()
    print("=" * 75)
    print("📊 市场分布:")
    print("=" * 75)
    
    markets = {}
    for s in all_stocks:
        m = s.get('market', '未知')
        markets[m] = markets.get(m, 0) + 1
    
    for m, c in sorted(markets.items(), key=lambda x: x[1], reverse=True):
        print(f"  {m:<10} {c:5}只")
    
    print(f"\n  总计：{len(all_stocks)}只")
    print("=" * 75)
    
    # 筛选沪深主板
    main_board = [s for s in all_stocks if is_main_board(s['code'])]
    
    print()
    print("=" * 75)
    print("📊 沪深主板涨幅分布:")
    print("=" * 75)
    
    ranges = [
        ('涨停 (≥9.5%)', 9.5, 999),
        ('8-9.5%', 8, 9.5),
        ('7-8%', 7, 8),
        ('5-7%', 5, 7),
        ('3-5%', 3, 5),
        ('0-3%', 0, 3),
        ('下跌 (<0%)', -999, 0)
    ]
    
    for name, min_pct, max_pct in ranges:
        count = sum(1 for s in main_board if min_pct <= s['change_pct'] < max_pct)
        if count > 0:
            print(f"  {name:<15} {count:4}只")
    
    print("=" * 75)
    
    # 涨幅 5%-7% 详细列表
    target = [s for s in main_board if 5 <= s['change_pct'] <= 7]
    target.sort(key=lambda x: x['change_pct'], reverse=True)
    
    print(f"\n📈 涨幅 5%-7% 沪深主板股票 ({len(target)}只):")
    print()
    
    if target:
        print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>8} {'现价':>10} {'市场':<10}")
        print("-" * 60)
        
        for i, s in enumerate(target, 1):
            print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+7.1f}% ¥{s['current']:>8.2f} {s['market']:<8}")
        
        print("-" * 60)
        print(f"\n✅ 总计：{len(target)}只")
    else:
        print("⚠️ 无涨幅 5%-7% 的股票")
    
    print("=" * 75)


    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    main()
