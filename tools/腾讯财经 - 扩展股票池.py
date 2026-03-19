#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯财经 - 扩展股票池版本
目标：获取 500+ 只沪深主板股票
策略：手动扩展股票池列表
"""

import requests
import time
from datetime import datetime


# 扩展股票池 - 沪深主板 500+ 只
EXTENDED_STOCK_POOL = []

# 沪市主板 (600/601/603/605) - 热点 + 活跃股
for i in list(range(0, 200)) + list(range(300, 400)) + list(range(500, 600)) + list(range(700, 800)):
    EXTENDED_STOCK_POOL.append(f"sh600{i:03d}")

for i in list(range(0, 100)) + list(range(100, 200)):
    EXTENDED_STOCK_POOL.append(f"sh601{i:03d}")

for i in list(range(0, 200)) + list(range(300, 400)) + list(range(500, 600)):
    EXTENDED_STOCK_POOL.append(f"sh603{i:03d}")

for i in range(0, 50):
    EXTENDED_STOCK_POOL.append(f"sh605{i:03d}")

# 深市主板 (000/001/002/003) - 热点 + 活跃股
for i in list(range(0, 200)) + list(range(300, 400)) + list(range(500, 600)) + list(range(700, 800)):
    EXTENDED_STOCK_POOL.append(f"sz000{i:03d}")

for i in range(0, 100):
    EXTENDED_STOCK_POOL.append(f"sz001{i:03d}")

for i in list(range(0, 300)) + list(range(400, 500)):
    EXTENDED_STOCK_POOL.append(f"sz002{i:03d}")

for i in range(0, 100):
    EXTENDED_STOCK_POOL.append(f"sz003{i:03d}")

# 去重
EXTENDED_STOCK_POOL = list(set(EXTENDED_STOCK_POOL))


def fetch_tencent_batch(symbols):
    """批量获取腾讯财经数据"""
    code_list = ','.join(symbols)
    url = f"http://qt.gtimg.cn/q={code_list}"
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        
        text = response.content.decode('gbk')
        lines = text.strip().split(';')
        
        result = []
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    data = parts[1].strip('"').split('~')
                    if len(data) >= 32 and data[3]:
                        code = data[2]
                        name = data[1] or '?'
                        current = float(data[3]) if data[3] else 0
                        change_pct = float(data[32]) if len(data) > 32 else 0
                        
                        if current > 0:
                            result.append({
                                'code': code,
                                'name': name,
                                'current': current,
                                'change_pct': change_pct
                            })
        
        return result
    except Exception as e:
        print(f"⚠️ 失败：{str(e)[:40]}")
        return []


def is_main_board(code):
    """判断是否沪深主板"""
    if code.startswith('6'):
        return code[:3] in ['600', '601', '603', '605']
    elif code.startswith('0'):
        return code[:3] in ['000', '001', '002', '003']
    return False


def main():
    print("=" * 75)
    print("🦞 腾讯财经 - 扩展股票池 (500+ 只)")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    print(f"📊 股票池总数：{len(EXTENDED_STOCK_POOL)}只")
    print()
    
    # 分批获取 (每批 100 只)
    batch_size = 100
    batches = [EXTENDED_STOCK_POOL[i:i+batch_size] for i in range(0, len(EXTENDED_STOCK_POOL), batch_size)]
    
    print(f"📊 分批获取 (每批{batch_size}只，共{len(batches)}批)...")
    print()
    
    all_stocks = []
    
    for i, batch in enumerate(batches):
        stocks = fetch_tencent_batch(batch)
        all_stocks.extend(stocks)
        
        print(f"  第{i+1}批：{len(stocks)}只 (累计{len(all_stocks)}只)")
        
        time.sleep(0.2)
    
    print()
    print("=" * 75)
    print(f"📊 获取结果：{len(all_stocks)}只")
    print(f"  成功率：{len(all_stocks)/len(EXTENDED_STOCK_POOL)*100:.1f}%")
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
    
    # 涨幅 5%-7%
    target = [s for s in main_board if 5 <= s['change_pct'] <= 7]
    target.sort(key=lambda x: x['change_pct'], reverse=True)
    
    print(f"\n📈 涨幅 5%-7% 沪深主板股票 ({len(target)}只):")
    print()
    
    if target:
        print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>8} {'现价':>10}")
        print("-" * 50)
        
        for i, s in enumerate(target, 1):
            print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+7.1f}% ¥{s['current']:>8.2f}")
        
        print("-" * 50)
        print(f"\n✅ 总计：{len(target)}只")
    else:
        print("⚠️ 无涨幅 5%-7% 的股票")
    
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
