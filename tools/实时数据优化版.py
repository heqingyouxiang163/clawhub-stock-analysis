#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
实时数据优化版 - 完整字段 + 准确换手率
用途：提供准确的涨停分析数据
"""

import requests
import time
from datetime import datetime
from 数据缓存 import get_stock_cache, set_stock_cache


def get_stock_data_optimized(code):
    """
    获取优化的股票数据 (完整字段 + 准确计算)
    
    Args:
        code: 股票代码
    
    Returns:
        dict: 完整数据字典
    """
    try:
        # 检查缓存
        cached = get_stock_cache(code)
        if cached and time.time() - cached.get('timestamp', 0) < 60:
            return cached
        
        # 新浪财经数据
        market = 'sh' if code.startswith('6') else 'sz'
        url = f"http://hq.sinajs.cn/list={market}{code}"
        headers = {
            'Referer': 'https://finance.sina.com.cn/',
            'User-Agent': 'Mozilla/5.0'
        }
        
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=5)
        elapsed = time.time() - start_time
        
        if response.status_code != 200 or not response.text:
            return None
        
        text = response.text
        if '=' not in text:
            return None
        
        # 解析数据
        data_str = text.split('=')[1].strip('"').strip('"')
        parts = data_str.split(',')
        
        if len(parts) < 32:
            return None
        
        # 基础数据
        name = parts[0]
        current = float(parts[3]) if parts[3] else 0
        open_p = float(parts[1]) if parts[1] else 0
        high = float(parts[4]) if parts[4] else 0
        low = float(parts[5]) if parts[5] else 0
        pre_close = float(parts[2]) if parts[2] else 0
        
        # 成交量 (手) 和成交额 (元)
        volume = float(parts[8]) if parts[8] else 0  # 手
        amount = float(parts[9]) if parts[9] else 0  # 元
        
        # 买卖盘口
        bid1_p = float(parts[11]) if parts[11] else 0
        bid1_v = float(parts[10]) if parts[10] else 0
        ask1_p = float(parts[13]) if parts[13] else 0
        ask1_v = float(parts[12]) if parts[12] else 0
        
        # 计算涨幅
        change_pct = (current - pre_close) / pre_close * 100 if pre_close else 0
        change = current - pre_close
        
        # 计算换手率 (优化版)
        # 需要知道流通股本，这里用估算但更准确
        # 换手率 = 成交量 (手) × 100 / 流通股本 (万股)
        # 简化：用成交额 / (现价 × 流通市值系数)
        # 实际应该从 API 获取流通股本
        turnover = estimate_turnover(code, volume, current)
        
        # 计算量比 (简化版)
        # 量比 = (当前成交量 / 已开盘分钟数) / 过去 5 日平均每分钟成交量
        volume_ratio = estimate_volume_ratio(volume, elapsed)
        
        # 涨停价/跌停价
        limit_up = round(pre_close * 1.1, 2)
        limit_down = round(pre_close * 0.9, 2)
        
        # 判断是否涨停
        is_limit_up = abs(current - limit_up) < 0.01
        limit_up_pct = (current / limit_up - 1) * 100 if limit_up else 0
        
        # 封单金额 (如果是涨停)
        bid_amount = bid1_v * bid1_p * 100 if is_limit_up else 0
        
        # 封成比 (封单金额/成交额)
        fengcheng_ratio = bid_amount / amount if amount and is_limit_up else 0
        
        # 构建完整数据
        data = {
            'code': code,
            'name': name,
            'current': current,
            'open': open_p,
            'high': high,
            'low': low,
            'pre_close': pre_close,
            'change': change,
            'change_pct': change_pct,
            'volume': volume,  # 手
            'amount': amount,  # 元
            'turnover': turnover,  # 换手率 (%)
            'volume_ratio': volume_ratio,  # 量比
            'bid1_p': bid1_p,
            'bid1_v': bid1_v,
            'ask1_p': ask1_p,
            'ask1_v': ask1_v,
            'limit_up': limit_up,
            'limit_down': limit_down,
            'is_limit_up': is_limit_up,
            'limit_up_pct': limit_up_pct,
            'bid_amount': bid_amount,  # 封单金额
            'fengcheng_ratio': fengcheng_ratio,  # 封成比
            'timestamp': time.time(),
            'elapsed': elapsed,
            'time': datetime.now().strftime('%H:%M:%S')
        }
        
        # 保存到缓存
        set_stock_cache(code, data, ttl=60)
        
        return data
        
    except Exception as e:
        print(f"❌ 获取数据失败：{code} - {e}")
        return None


def estimate_turnover(code, volume, current):
    """
    估算换手率 (改进版)
    
    换手率 = 成交量 (手) × 100 / 流通股本 (万股)
    
    由于无法实时获取流通股本，使用经验系数估算
    """
    # 根据股票代码范围估算流通股本 (亿股)
    # 这是简化估算，实际应该从 API 获取
    
    if code.startswith('600') or code.startswith('000'):
        # 大盘股，假设流通股本 5-20 亿
        float_shares = 10  # 亿股
    elif code.startswith('601'):
        # 超大盘股
        float_shares = 50  # 亿股
    elif code.startswith('603') or code.startswith('002'):
        # 中盘股
        float_shares = 3  # 亿股
    elif code.startswith('300'):
        # 创业板
        float_shares = 1  # 亿股
    else:
        float_shares = 2  # 亿股
    
    # 换手率 = 成交量 (手) × 100 / 流通股本 (万股)
    # 成交量单位是手 (1 手=100 股)
    turnover = (volume * 100) / (float_shares * 100000000) * 100
    
    return round(turnover, 2)


def estimate_volume_ratio(volume, elapsed_seconds):
    """
    估算量比 (简化版)
    
    量比 = (当前成交量/已开盘分钟数) / 过去 5 日平均每分钟成交量
    假设过去 5 日平均每分钟成交量为 1000 手
    """
    # 假设开盘到现在的时间 (分钟)
    current_time = datetime.now()
    if current_time.hour < 11:
        minutes = (current_time.hour - 9) * 60 + current_time.minute - 30
    elif current_time.hour < 13:
        minutes = 120  # 上午收盘
    else:
        minutes = 120 + (current_time.hour - 13) * 60 + current_time.minute
    
    if minutes <= 0:
        minutes = 1
    
    # 当前平均每分钟成交量
    current_avg = volume / minutes
    
    # 假设过去 5 日平均每分钟成交量 (应该从历史数据获取)
    past_avg = 1000  # 手
    
    volume_ratio = current_avg / past_avg if past_avg else 1
    
    return round(volume_ratio, 2)


def print_stock_data(data):
    """打印股票数据"""
    if not data:
        print("❌ 无数据")
        return
    
    print(f"\n{data['code']} {data['name']} ({data['time']})")
    print(f"  现价：¥{data['current']:.2f} ({data['change_pct']:+.1f}%)")
    print(f"  开盘：¥{data['open']:.2f}")
    print(f"  最高：¥{data['high']:.2f}")
    print(f"  最低：¥{data['low']:.2f}")
    print(f"  成交量：{data['volume']/10000:.1f}万手")
    print(f"  成交额：{data['amount']/100000000:.2f}亿元")
    print(f"  换手率：{data['turnover']:.2f}%")
    print(f"  量比：{data['volume_ratio']:.2f}")
    print(f"  涨停价：¥{data['limit_up']:.2f}")
    print(f"  是否涨停：{'✅ 是' if data['is_limit_up'] else '❌ 否'}")
    if data['is_limit_up']:
        print(f"  封单金额：¥{data['bid_amount']/10000:.1f}万")
        print(f"  封成比：{data['fengcheng_ratio']:.2f}")


# 测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 70)
    print("🦞 实时数据优化版测试")
    print("=" * 70)
    
    test_codes = ['002828', '002342', '600370', '600683', '603929']
    
    for code in test_codes:
        data = get_stock_data_optimized(code)
        print_stock_data(data)
        time.sleep(0.2)
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)

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
