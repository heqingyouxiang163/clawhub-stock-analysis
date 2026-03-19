#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪财经 - 获取全市场沪深 A 股实时数据
统计涨幅 5%-7% 的沪深主板股票数量
"""

import requests
import time
from datetime import datetime


def get_all_shanghai_codes():
    """获取沪市 A 股代码列表 (600/601/603/605)"""
    # 沪市 A 股列表 (简化版，实际需要动态获取)
    # 这里使用已知的主要代码段
    codes = []
    
    # 600xxx (约 1000 只)
    for i in range(1000):
        code = f"600{i:03d}"
        codes.append(f"sh{code}")
    
    # 601xxx (约 200 只)
    for i in range(200):
        code = f"601{i:03d}"
        codes.append(f"sh{code}")
    
    # 603xxx (约 400 只)
    for i in range(400):
        code = f"603{i:03d}"
        codes.append(f"sh{code}")
    
    # 605xxx (约 100 只)
    for i in range(100):
        code = f"605{i:03d}"
        codes.append(f"sh{code}")
    
    return codes


def get_all_shenzhen_codes():
    """获取深市 A 股代码列表 (000/001/002/003)"""
    codes = []
    
    # 000xxx (约 500 只)
    for i in range(500):
        code = f"000{i:03d}"
        codes.append(f"sz{code}")
    
    # 001xxx (约 50 只)
    for i in range(50):
        code = f"001{i:03d}"
        codes.append(f"sz{code}")
    
    # 002xxx (约 300 只)
    for i in range(300):
        code = f"002{i:03d}"
        codes.append(f"sz{code}")
    
    # 003xxx (约 50 只)
    for i in range(50):
        code = f"003{i:03d}"
        codes.append(f"sz{code}")
    
    return codes


def fetch_sina_data_batch(symbols):
    """
    从新浪财经批量获取股票数据
    
    Args:
        symbols: 股票代码列表 (如 ['sh600000', 'sz000001'])
    
    Returns:
        list: 股票数据列表
    """
    code_list = ','.join(symbols)
    url = f"http://hq.sinajs.cn/list={code_list}"
    
    try:
        response = requests.get(url, timeout=10)
        
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
                    if len(data) >= 32:
                        # 新浪财经格式
                        # data[0]=名称，data[1]=今开，data[2]=昨收，data[3]=现价，data[4]=最高，data[5]=最低
                        # data[32]=代码
                        symbol = parts[0].split('_')[-1]  # 如 sh600000
                        code = symbol[2:]  # 去掉 sh/sz
                        
                        name = data[0] if data[0] else '?'
                        current = float(data[3]) if data[3] else 0
                        prev_close = float(data[2]) if data[2] else current
                        high = float(data[4]) if data[4] else current
                        low = float(data[5]) if data[5] else current
                        open_p = float(data[1]) if data[1] else current
                        
                        # 计算涨幅
                        change_pct = ((current - prev_close) / prev_close * 100) if prev_close > 0 else 0
                        
                        if current > 0:  # 只保留有数据的股票
                            result.append({
                                'code': code,
                                'name': name,
                                'current': current,
                                'prev_close': prev_close,
                                'open': open_p,
                                'high': high,
                                'low': low,
                                'change_pct': change_pct
                            })
        
        return result
        
    except Exception as e:
        print(f"⚠️ 新浪财经失败：{str(e)[:50]}")
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
    print("🦞 新浪财经 - 全市场涨幅 5%-7% 沪深主板股票统计")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    print("📊 获取沪市 A 股数据...")
    sh_codes = get_all_shanghai_codes()[:500]  # 限制数量测试
    sh_data = fetch_sina_data_batch(sh_codes)
    print(f"  获取到 {len(sh_data)} 只沪市股票")
    
    print("\n📊 获取深市 A 股数据...")
    sz_codes = get_all_shenzhen_codes()[:500]  # 限制数量测试
    sz_data = fetch_sina_data_batch(sz_codes)
    print(f"  获取到 {len(sz_data)} 只深市股票")
    
    # 合并数据
    all_data = sh_data + sz_data
    
    # 筛选沪深主板 + 涨幅 5%-7%
    target_stocks = [s for s in all_data if is_main_board(s['code']) and 5 <= s['change_pct'] <= 7]
    
    # 排序
    target_stocks.sort(key=lambda x: x['change_pct'], reverse=True)
    
    print()
    print("=" * 75)
    print("📊 统计结果:")
    print(f"  总获取数：{len(all_data)}只")
    print(f"  沪深主板：{sum(1 for s in all_data if is_main_board(s['code']))}只")
    print(f"  涨幅 5%-7%: {len(target_stocks)}只")
    print("=" * 75)
    
    if target_stocks:
        print(f"\n📈 涨幅 5%-7% 股票列表 ({len(target_stocks)}只):")
        print()
        
        for i, s in enumerate(target_stocks[:20], 1):  # 只显示前 20 只
            print(f"{i:2}. {s['code']} {s['name']:8} ¥{s['current']:7.2f} {s['change_pct']:+6.1f}%")
        
        if len(target_stocks) > 20:
            print(f"... 还有 {len(target_stocks)-20}只")
    
    print()
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
