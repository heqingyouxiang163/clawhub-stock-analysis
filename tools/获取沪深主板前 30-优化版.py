#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沪深主板涨幅前 30 名 - 腾讯财经优化版

优化点:
1. 缩小代码池范围 (只请求有效代码段)
2. 增加并发线程 (10 线程)
3. 过滤无效数据
4. 优化排序
"""

import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

print("=" * 70)
print("🦞 沪深主板涨幅前 30 名 (腾讯财经优化版)")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print()

# 沪深主板代码范围 (精确版)
MAIN_BOARD_RANGES = [
    # 沪市主板
    ('600', 0, 999),    # 600000-600999
    ('601', 0, 999),    # 601000-601999
    ('603', 0, 999),    # 603000-603999
    ('605', 0, 399),    # 605000-605399
    # 深市主板
    ('000', 0, 999),    # 000000-000999
    ('001', 0, 999),    # 001000-001999
    ('002', 0, 999),    # 002000-002999
    ('003', 0, 399),    # 003000-003399
]


def generate_codes():
    """生成沪深主板代码"""
    codes = []
    for prefix, start, end in MAIN_BOARD_RANGES:
        for i in range(start, end + 1):
            codes.append(f"{prefix}{i:03d}")
    return codes


def fetch_batch(codes):
    """批量获取腾讯数据"""
    symbols = ','.join([f"sh{s}" if s.startswith('6') else f"sz{s}" for s in codes])
    url = f"http://qt.gtimg.cn/q={symbols}"
    
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            lines = text.strip().split(';')
            
            result = []
            for line in lines:
                if '=' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        data = parts[1].strip('"').split('~')
                        if len(data) >= 32 and data[3] and data[2]:
                            code = data[2]
                            # 验证主板代码
                            if (code.startswith('600') or code.startswith('601') or
                                code.startswith('603') or code.startswith('605') or
                                code.startswith('000') or code.startswith('001') or
                                code.startswith('002') or code.startswith('003')):
                                result.append({
                                    'code': code,
                                    'name': data[1] or '?',
                                    'change_pct': float(data[32]),
                                    'current': float(data[3]),
                                })
            return result
    except:
        pass
    return []


def get_main_board_data():
    """获取沪深主板数据"""
    print("📊 腾讯财经 - 获取沪深主板数据...")
    start = time.time()
    
    # 生成代码池
    codes = generate_codes()
    print(f"  代码池：{len(codes)}只")
    
    # 分批 (每批 200 只)
    batch_size = 200
    batches = [codes[i:i+batch_size] for i in range(0, len(codes), batch_size)]
    print(f"  分批次：{len(batches)}批")
    
    # 多线程并发 (10 线程)
    all_stocks = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_batch, batch): i for i, batch in enumerate(batches)}
        
        for future in as_completed(futures):
            data = future.result()
            all_stocks.extend(data)
    
    # 去重
    seen = set()
    unique_stocks = []
    for s in all_stocks:
        if s['code'] not in seen:
            seen.add(s['code'])
            unique_stocks.append(s)
    
    # 排序
    unique_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    elapsed = time.time() - start
    print(f"✅ 获取{len(unique_stocks)}只，耗时{elapsed*1000:.0f}ms，速度{len(unique_stocks)/elapsed:.0f}只/秒")
    
    return unique_stocks


# 获取数据
stocks = get_main_board_data()

print()
print("=" * 70)
print("📈 沪深主板涨幅前 30 名")
print("=" * 70)
print()

if stocks:
    print(f"{'序号':<4} {'代码':<8} {'名称':<10} {'涨幅':>10} {'现价':>10}")
    print("-" * 50)
    
    for i, s in enumerate(stocks[:30], 1):
        print(f"{i:<4} {s['code']:<8} {s['name']:<10} {s['change_pct']:>+9.1f}% ¥{s['current']:>8.2f}")
    
    print("-" * 50)
    print(f"✅ 总计：30 只")
    print()
    
    # 统计
    top30 = stocks[:30]
    avg_change = sum(s['change_pct'] for s in top30) / 30
    limit_up = sum(1 for s in top30 if s['change_pct'] >= 9.5)
    
    print(f"📊 前 30 统计:")
    print(f"  平均涨幅：{avg_change:+.1f}%")
    print(f"  涨停数量：{limit_up}只")
    print(f"  最高涨幅：{top30[0]['change_pct']:+.1f}% ({top30[0]['name']})")
    print(f"  第 30 名：{top30[29]['change_pct']:+.1f}% ({top30[29]['code']} {top30[29]['name']})")
else:
    print("⚠️ 获取失败")

print()
print("=" * 70)
