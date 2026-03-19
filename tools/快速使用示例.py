#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速使用示例 - 使用优化后的数据获取系统
"""

import requests
import time
from 数据缓存 import get_stock_cache, set_stock_cache

def get_stock_price_sina(code):
    """从新浪财经获取股票价格 (快速版)"""
    
    # 1. 检查缓存
    cached = get_stock_cache(code)
    if cached:
        print(f"✅ 缓存命中：{code}")
        return cached
    
    # 2. 获取市场
    market = 'sh' if code.startswith('6') else 'sz'
    
    # 3. 请求数据
    url = f"http://hq.sinajs.cn/list={market}{code}"
    headers = {
        'Referer': 'https://finance.sina.com.cn/',
        'User-Agent': 'Mozilla/5.0'
    }
    
    start = time.time()
    response = requests.get(url, headers=headers, timeout=5)
    elapsed = time.time() - start
    
    if response.status_code == 200:
        # 4. 解析数据
        text = response.text
        if '=' in text:
            data_str = text.split('=')[1].strip('"').strip('"')
            parts = data_str.split(',')
            
            if len(parts) >= 3:
                name = parts[0]
                current_price = float(parts[3]) if parts[3] else 0
                open_price = float(parts[1]) if parts[1] else 0
                high = float(parts[4]) if parts[4] else 0
                low = float(parts[5]) if parts[5] else 0
                
                data = {
                    'code': code,
                    'name': name,
                    'price': current_price,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'time': time.time()
                }
                
                # 5. 保存到缓存
                set_stock_cache(code, data, ttl=60)
                
                print(f"✅ 获取成功：{code} - {name} - ¥{current_price} - 耗时：{elapsed*1000:.1f}ms")
                return data
    
    print(f"❌ 获取失败：{code}")
    return None

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 快速使用示例")
    print("=" * 50)
    
    # 测试股票
    test_codes = ["002828", "600519"]
    
    print("\n第一次获取 (从 API):")
    for code in test_codes:
        get_stock_price_sina(code)
    
    print("\n第二次获取 (从缓存):")
    for code in test_codes:
        get_stock_price_sina(code)
    
    print("\n✅ 演示完成！")
    print("\n使用说明:")
    print("from 快速使用示例 import get_stock_price_sina")
    print("data = get_stock_price_sina('002828')")

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
