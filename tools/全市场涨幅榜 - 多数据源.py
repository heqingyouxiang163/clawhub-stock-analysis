#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据源融合 - 获取全市场涨幅榜
目标：覆盖全市场 5000+ 只股票
策略：多个数据源并行获取，合并去重
"""

import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_sina_batch(symbols):
    """新浪财经批量获取"""
    code_list = ','.join(symbols)
    url = f"http://hq.sinajs.cn/list={code_list}"
    
    try:
        response = requests.get(url, timeout=8)
        if response.status_code != 200:
            return []
        
        text = response.content.decode('gbk')
        lines = text.strip().split(';')
        
        result = []
        for line in lines:
            if '=' in line:
                parts = line.split('=')
                if len(parts) >= 2:
                    data = parts[1].strip('"').split(',')
                    if len(data) >= 32 and data[3]:
                        symbol = parts[0].split('_')[-1]
                        code = symbol[2:]
                        
                        name = data[0] or '?'
                        current = float(data[3]) if data[3] else 0
                        prev_close = float(data[2]) if data[2] else current
                        
                        if current > 0 and prev_close > 0:
                            change_pct = (current - prev_close) / prev_close * 100
                            result.append({
                                'code': code,
                                'name': name,
                                'current': current,
                                'change_pct': change_pct,
                                'source': 'sina'
                            })
        
        return result
    except:
        return []


def get_qq_batch(symbols):
    """腾讯财经批量获取"""
    code_list = ','.join(symbols)
    url = f"http://qt.gtimg.cn/q={code_list}"
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        response = requests.get(url, headers=headers, timeout=8)
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
                                'change_pct': change_pct,
                                'source': 'qq'
                            })
        
        return result
    except:
        return []


def generate_main_board_codes():
    """生成沪深主板代码列表"""
    codes = []
    
    # 沪市主板：600/601/603/605
    for prefix in ['600', '601', '603', '605']:
        for i in range(1000 if prefix == '600' else 200 if prefix == '601' else 500 if prefix == '603' else 100):
            code = f"{prefix}{i:03d}"
            codes.append(f"sh{code}")
    
    # 深市主板：000/001/002/003
    for prefix in ['000', '001', '002', '003']:
        for i in range(500 if prefix == '000' else 100 if prefix == '001' else 300 if prefix == '002' else 100):
            code = f"{prefix}{i:03d}"
            codes.append(f"sz{code}")
    
    return codes


def main():
    print("=" * 75)
    print("🦞 多数据源融合 - 全市场涨幅榜")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 生成代码列表
    print("📊 生成沪深主板代码列表...")
    all_codes = generate_main_board_codes()
    print(f"  总代码数：{len(all_codes)}只")
    print()
    
    # 分批获取 (每批 60 只)
    batch_size = 60
    batches = [all_codes[i:i+batch_size] for i in range(0, min(3000, len(all_codes)), batch_size)]
    
    print(f"📊 分批获取 (每批{batch_size}只，共{len(batches)}批)...")
    print()
    
    all_stocks = []
    success_count = 0
    
    # 使用多线程加速
    with ThreadPoolExecutor(max_workers=5) as executor:
        for i, batch in enumerate(batches):
            # 交替使用新浪和腾讯
            if i % 2 == 0:
                future = executor.submit(get_sina_batch, batch)
                source = '新浪'
            else:
                future = executor.submit(get_qq_batch, batch)
                source = '腾讯'
            
            stocks = future.result()
            all_stocks.extend(stocks)
            
            if stocks:
                success_count += 1
            
            # 进度显示
            if (i + 1) % 10 == 0:
                print(f"  进度：{i+1}/{len(batches)}批，获取{len(all_stocks)}只")
            
            time.sleep(0.3)  # 避免请求过快
    
    print()
    print("=" * 75)
    print("📊 获取结果:")
    print(f"  成功批次：{success_count}/{len(batches)}")
    print(f"  获取股票：{len(all_stocks)}只")
    print(f"  覆盖率：{len(all_stocks)/len(all_codes)*100:.1f}%")
    print("=" * 75)
    
    # 去重 (优先保留腾讯数据)
    unique_stocks = {}
    for s in all_stocks:
        code = s['code']
        if code not in unique_stocks or s['source'] == 'qq':
            unique_stocks[code] = s
    
    stocks_list = list(unique_stocks.values())
    stocks_list.sort(key=lambda x: x['change_pct'], reverse=True)
    
    print()
    print("=" * 75)
    print("📊 涨幅分布统计:")
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
        count = sum(1 for s in stocks_list if min_pct <= s['change_pct'] < max_pct)
        if count > 0:
            print(f"  {name:<15} {count:4}只")
    
    print("=" * 75)
    
    # 涨幅 5%-7% 详细列表
    target = [s for s in stocks_list if 5 <= s['change_pct'] <= 7]
    
    print(f"\n📈 涨幅 5%-7% 股票列表 ({len(target)}只):")
    print()
    
    if target:
        for i, s in enumerate(target[:30], 1):
            print(f"{i:2}. {s['code']} {s['name']:8} ¥{s['current']:7.2f} {s['change_pct']:+6.1f}%")
        
        if len(target) > 30:
            print(f"... 还有 {len(target)-30}只")
    
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
