#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富网 - 获取全市场涨幅榜
统计涨幅 5%-7% 的沪深主板股票数量
"""

import requests
from datetime import datetime


def get_rank_board():
    """
    从东方财富获取沪深 A 股涨幅排名
    
    接口：https://push2.eastmoney.com/api/qt/clist/get
    参数：
      - pn: 页码
      - pz: 每页数量 (最大 500)
      - po: 排序 (1=降序)
      - np: 返回字段
      - ut: 用户标识
      - fltt: 浮点精度
      - invt: 精度
      - fs: 市场筛选 (m:0 深市，m:1 沪市)
    """
    
    all_stocks = []
    
    # 沪深 A 股筛选
    # m:0 深市 + m:1 沪市
    # 排除创业板 (300/301) 和科创板 (688/689)
    filters = "m:0+m:1"
    
    for page in range(1, 10):  # 最多获取 10 页 (5000 只股票)
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': page,
            'pz': 500,
            'po': 1,  # 降序
            'np': 1,
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': 2,
            'invt': 2,
            'fid': 'f3',  # 按涨幅排序
            'fs': filters,
            'fields': 'f12,f14,f3,f11,f17,f18,f19,f20'  # 代码，名称，涨幅，今开，最高，最低，昨收，现价
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"⚠️ HTTP {response.status_code}")
                break
            
            data = response.json()
            
            if data.get('data') and data['data'].get('diff'):
                stocks = data['data']['diff']
                
                for s in stocks:
                    code = s.get('f12', '')
                    
                    # 筛选沪深主板
                    if code.startswith('300') or code.startswith('301'):  # 创业板
                        continue
                    if code.startswith('688') or code.startswith('689'):  # 科创板
                        continue
                    if not (code.startswith('60') or code.startswith('00')):
                        continue
                    
                    all_stocks.append({
                        'code': code,
                        'name': s.get('f14', '?'),
                        'change_pct': s.get('f3', 0),
                        'open': s.get('f11', 0),
                        'high': s.get('f17', 0),
                        'low': s.get('f18', 0),
                        'prev_close': s.get('f19', 0),
                        'current': s.get('f20', 0)
                    })
                
                # 如果返回数量不足 500，说明已经是最后一页
                if len(stocks) < 500:
                    break
                
                print(f"  第{page}页：获取{len(stocks)}只，累计{len(all_stocks)}只")
            else:
                break
                
        except Exception as e:
            print(f"⚠️ 请求失败：{str(e)[:50]}")
            break
        
        # 避免请求过快
        import time
        time.sleep(0.2)
    
    return all_stocks


def main():
    print("=" * 75)
    print("🦞 东方财富 - 全市场涨幅 5%-7% 沪深主板股票统计")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    print("📊 获取沪深 A 股涨幅榜...")
    all_stocks = get_rank_board()
    
    if not all_stocks:
        print("❌ 获取失败")
        return
    
    print(f"\n✅ 获取到 {len(all_stocks)} 只沪深主板股票")
    
    # 统计涨幅 5%-7%
    target_stocks = [s for s in all_stocks if 5 <= s['change_pct'] <= 7]
    target_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    # 完整涨幅分布
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
    print("=" * 75)
    print("📊 涨幅分布统计:")
    print("=" * 75)
    
    for name, min_pct, max_pct in ranges:
        count = sum(1 for s in all_stocks if min_pct <= s['change_pct'] < max_pct)
        print(f"  {name:<15} {count:4}只")
    
    print("=" * 75)
    
    # 涨幅 5%-7% 详细列表
    print(f"\n📈 涨幅 5%-7% 股票列表 ({len(target_stocks)}只):")
    print()
    
    if target_stocks:
        print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>8} {'现价':>10}")
        print("-" * 50)
        
        for i, s in enumerate(target_stocks, 1):
            print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+7.1f}% ¥{s['current']:>8.2f}")
        
        print("-" * 50)
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
