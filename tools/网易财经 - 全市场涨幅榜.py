#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网易财经 - 获取沪深 A 股涨幅榜
接口稳定，数据准确
"""

import requests
import json
from datetime import datetime


def get_163_rank():
    """
    从网易财经获取涨幅榜
    
    接口：http://api.money.126.net/timeshare/
    返回沪深 A 股实时数据
    """
    
    all_stocks = []
    
    # 沪市 A 股
    print("📊 获取沪市 A 股...")
    for page in range(1, 20):
        url = f"http://api.money.126.net/timeshare/space/sha/list/{page}/500/1/0.json"
        
        try:
            response = requests.get(url, timeout=8)
            if response.status_code == 200:
                text = response.text
                # 去除 JSONP 包装
                if text.startswith('var ') and '(' in text:
                    start = text.index('(') + 1
                    end = text.rindex(')')
                    json_str = text[start:end]
                    data = json.loads(json_str)
                    
                    if data.get('data') and data['data'].get('list'):
                        stocks = data['data']['list']
                        for s in stocks:
                            code = s.get('code', '')
                            if code.startswith('600') or code.startswith('601') or code.startswith('603') or code.startswith('605'):
                                all_stocks.append({
                                    'code': code,
                                    'name': s.get('name', '?'),
                                    'change_pct': s.get('increase', 0),
                                    'current': s.get('price', 0),
                                    'market': '沪市'
                                })
                        
                        print(f"  第{page}页：{len(stocks)}只 (累计{len(all_stocks)}只)")
                        
                        if len(stocks) < 500:
                            break
        except Exception as e:
            print(f"  ⚠️ 失败：{str(e)[:40]}")
            break
        
        import time
        time.sleep(0.2)
    
    # 深市 A 股
    print("\n📊 获取深市 A 股...")
    shenzhen_count = len(all_stocks)
    
    for page in range(1, 20):
        url = f"http://api.money.126.net/timeshare/space/sza/list/{page}/500/1/0.json"
        
        try:
            response = requests.get(url, timeout=8)
            if response.status_code == 200:
                text = response.text
                if text.startswith('var ') and '(' in text:
                    start = text.index('(') + 1
                    end = text.rindex(')')
                    json_str = text[start:end]
                    data = json.loads(json_str)
                    
                    if data.get('data') and data['data'].get('list'):
                        stocks = data['data']['list']
                        for s in stocks:
                            code = s.get('code', '')
                            if code.startswith('000') or code.startswith('001') or code.startswith('002') or code.startswith('003'):
                                all_stocks.append({
                                    'code': code,
                                    'name': s.get('name', '?'),
                                    'change_pct': s.get('increase', 0),
                                    'current': s.get('price', 0),
                                    'market': '深市'
                                })
                        
                        print(f"  第{page}页：{len(stocks)}只 (累计{len(all_stocks)}只)")
                        
                        if len(stocks) < 500:
                            break
        except Exception as e:
            print(f"  ⚠️ 失败：{str(e)[:40]}")
            break
        
        import time
        time.sleep(0.2)
    
    return all_stocks


def main():
    print("=" * 75)
    print("🦞 网易财经 - 全市场涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    all_stocks = get_163_rank()
    
    if not all_stocks:
        print("\n❌ 获取失败")
        return
    
    print()
    print("=" * 75)
    print(f"📊 获取结果：{len(all_stocks)}只")
    print("=" * 75)
    
    # 涨幅分布
    ranges = [
        ('涨停 (≥9.5%)', 9.5, 999),
        ('8-9.5%', 8, 9.5),
        ('7-8%', 7, 8),
        ('5-7%', 5, 7),
        ('3-5%', 3, 5),
        ('0-3%', 0, 3),
        ('下跌 (<0%)', -999, 0)
    ]
    
    print()
    print("📊 涨幅分布:")
    print()
    
    for name, min_pct, max_pct in ranges:
        count = sum(1 for s in all_stocks if min_pct <= s['change_pct'] < max_pct)
        if count > 0:
            print(f"  {name:<15} {count:4}只")
    
    print("=" * 75)
    
    # 涨幅 5%-7%
    target = [s for s in all_stocks if 5 <= s['change_pct'] <= 7]
    target.sort(key=lambda x: x['change_pct'], reverse=True)
    
    print(f"\n📈 涨幅 5%-7% 股票 ({len(target)}只):")
    print()
    
    if target:
        for i, s in enumerate(target[:30], 1):
            print(f"{i:2}. {s['code']} {s['name']:8} ¥{s['current']:7.2f} {s['change_pct']:+6.1f}% ({s['market']})")
        
        if len(target) > 30:
            print(f"... 还有 {len(target)-30}只")
    
    print("=" * 75)


    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"
✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"
✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"
✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    main()
