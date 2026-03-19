#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沪深主板涨幅前 30 名 - 腾讯财经版
"""

import requests
import time
from datetime import datetime

print("=" * 70)
print("🦞 沪深主板涨幅前 30 名 (腾讯财经)")
print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print()

# 沪深主板股票池 (简化版，实际需要完整股票池)
# 沪市主板：600, 601, 603, 605
# 深市主板：000, 001, 002, 003

def generate_main_board_codes():
    """生成沪深主板代码列表"""
    codes = []
    
    # 沪市主板
    for prefix in ['600', '601', '603', '605']:
        for i in range(1000):
            code = f"{prefix}{i:03d}"
            codes.append(code)
    
    # 深市主板
    for prefix in ['000', '001', '002', '003']:
        for i in range(1000):
            code = f"{prefix}{i:03d}"
            codes.append(code)
    
    return codes


def get_tencent_data(codes):
    """腾讯财经批量获取"""
    print(f"📊 腾讯财经 - 获取{len(codes)}只股票数据...")
    start = time.time()
    
    # 分批获取
    batch_size = 150
    batches = [codes[i:i+batch_size] for i in range(0, len(codes), batch_size)]
    
    all_stocks = []
    completed = 0
    
    for batch in batches:
        symbols = ','.join([f"sh{s}" if s.startswith('6') else f"sz{s}" for s in batch])
        url = f"http://qt.gtimg.cn/q={symbols}"
        
        try:
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                text = resp.content.decode('gbk')
                lines = text.strip().split(';')
                
                for line in lines:
                    if '=' in line:
                        parts = line.split('=')
                        if len(parts) >= 2:
                            data = parts[1].strip('"').split('~')
                            if len(data) >= 32 and data[3]:
                                code = data[2]
                                # 过滤主板
                                if (code.startswith('600') or code.startswith('601') or
                                    code.startswith('603') or code.startswith('605') or
                                    code.startswith('000') or code.startswith('001') or
                                    code.startswith('002') or code.startswith('003')):
                                    all_stocks.append({
                                        'code': code,
                                        'name': data[1] or '?',
                                        'change_pct': float(data[32]) if len(data) > 32 else 0,
                                        'current': float(data[3]) if data[3] else 0,
                                    })
                
                completed += 1
                print(f"  批次{completed}/{len(batches)}: 累计{len(all_stocks)}只")
        except Exception as e:
            print(f"  ⚠️ 批次失败：{str(e)[:30]}")
    
    # 排序
    all_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    elapsed = time.time() - start
    print(f"✅ 获取{len(all_stocks)}只，耗时{elapsed*1000:.0f}ms，速度{len(all_stocks)/elapsed:.0f}只/秒")
    
    return all_stocks


# 生成代码
print("🔄 生成沪深主板代码池...")
all_codes = generate_main_board_codes()
print(f"  代码池：{len(all_codes)}只")
print()

# 获取数据
stocks = get_tencent_data(all_codes)

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
    print(f"  最低涨幅：{top30[-1]['change_pct']:+.1f}% ({top30[-1]['name']})")
else:
    print("⚠️ 获取失败")

print()
print("=" * 70)
