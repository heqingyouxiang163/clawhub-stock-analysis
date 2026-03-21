#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
多数据源并行获取 - 修复版
用途：同时从多个数据源获取，取最快结果
"""

import aiohttp
import asyncio
import time
from datetime import datetime
from 数据缓存 import get_stock_cache, set_stock_cache


async def fetch_sina(session, code):
    """新浪财经"""
    try:
        market = 'sh' if code.startswith('6') else 'sz'
        url = f"http://hq.sinajs.cn/list={market}{code}"
        headers = {'Referer': 'https://finance.sina.com.cn/'}
        
        start = time.time()
        async with session.get(url, headers=headers, timeout=5) as resp:
            text = await resp.text()
            elapsed = time.time() - start
            
            if '=' in text and resp.status == 200:
                data_str = text.split('=')[1].strip('"').strip('"')
                parts = data_str.split(',')
                
                if len(parts) >= 32:
                    return {
                        'success': True,
                        'source': 'sina',
                        'source_name': '新浪财经',
                        'data': {
                            'code': code,
                            'name': parts[0],
                            'current': float(parts[3]) if parts[3] else 0,
                            'open': float(parts[1]) if parts[1] else 0,
                            'high': float(parts[4]) if parts[4] else 0,
                            'low': float(parts[5]) if parts[5] else 0,
                            'pre_close': float(parts[2]) if parts[2] else 0,
                            'volume': float(parts[8]) if parts[8] else 0,
                            'amount': float(parts[9]) if parts[9] else 0,
                            'change_pct': (float(parts[3]) - float(parts[2])) / float(parts[2]) * 100 if parts[2] and parts[3] else 0,
                        },
                        'elapsed': elapsed
                    }
    except Exception as e:
        pass
    
    return {'success': False, 'source': 'sina', 'error': str(e), 'elapsed': 0}


async def fetch_eastmoney(session, code):
    """东方财富"""
    try:
        market_id = '1' if code.startswith('6') else '0'
        url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market_id}.{code}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f107,f108,f109"
        headers = {'Referer': 'http://quote.eastmoney.com/'}
        
        start = time.time()
        async with session.get(url, headers=headers, timeout=5) as resp:
            data = await resp.json()
            elapsed = time.time() - start
            
            if data.get('data'):
                d = data['data']
                return {
                    'success': True,
                    'source': 'eastmoney',
                    'source_name': '东方财富',
                    'data': {
                        'code': code,
                        'name': d.get('f58', ''),
                        'current': d.get('f46', 0),
                        'open': d.get('f47', 0),
                        'high': d.get('f44', 0),
                        'low': d.get('f45', 0),
                        'pre_close': d.get('f60', 0),
                        'change_pct': d.get('f170', 0),
                        'volume': d.get('f47', 0) * 100,
                        'amount': d.get('f48', 0),
                        'turnover': d.get('f107', 0),
                        'volume_ratio': d.get('f108', 0),
                    },
                    'elapsed': elapsed
                }
    except Exception as e:
        pass
    
    return {'success': False, 'source': 'eastmoney', 'error': str(e), 'elapsed': 0}


async def fetch_qq(session, code):
    """腾讯财经"""
    try:
        market = 'sh' if code.startswith('6') else 'sz'
        url = f"http://qt.gtimg.cn/q={market}{code}"
        headers = {'Referer': 'http://stockapp.finance.qq.com/'}
        
        start = time.time()
        async with session.get(url, headers=headers, timeout=5) as resp:
            text = await resp.text()
            elapsed = time.time() - start
            
            if '=' in text and resp.status == 200:
                data_str = text.split('=')[1].strip('"').strip('"')
                parts = data_str.split('~')
                
                if len(parts) >= 50:
                    return {
                        'success': True,
                        'source': 'qq',
                        'source_name': '腾讯财经',
                        'data': {
                            'code': code,
                            'name': parts[1],
                            'current': float(parts[3]) if parts[3] else 0,
                            'open': float(parts[5]) if parts[5] else 0,
                            'high': float(parts[33]) if parts[33] else 0,
                            'low': float(parts[34]) if parts[34] else 0,
                            'pre_close': float(parts[4]) if parts[4] else 0,
                            'volume': float(parts[6]) if parts[6] else 0,
                            'amount': float(parts[37]) if parts[37] else 0,
                            'change_pct': (float(parts[3]) - float(parts[4])) / float(parts[4]) * 100 if parts[4] and parts[3] else 0,
                        },
                        'elapsed': elapsed
                    }
    except Exception as e:
        pass
    
    return {'success': False, 'source': 'qq', 'error': str(e), 'elapsed': 0}


async def fetch_all_sources(code):
    """并行获取所有数据源"""
    async with aiohttp.ClientSession() as session:
        # 创建所有任务
        tasks = [
            fetch_sina(session, code),
            fetch_eastmoney(session, code),
            fetch_qq(session, code)
        ]
        
        # 等待所有任务完成，设置超时
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            results = [{'success': False, 'error': str(e)}]
        
        # 返回第一个成功的结果
        for result in results:
            if isinstance(result, dict) and result.get('success'):
                return result
        
        # 都失败
        return {'success': False, 'error': 'All sources failed', 'elapsed': 0}


def get_realtime_data(code):
    """获取实时数据 (同步接口)"""
    # 检查缓存
    cached = get_stock_cache(code)
    if cached and time.time() - cached.get('timestamp', 0) < 30:
        cached['from_cache'] = True
        return cached
    
    # 获取数据
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(fetch_all_sources(code))
        if result.get('success'):
            result['from_cache'] = False
            result['data']['timestamp'] = time.time()
            # 缓存
            set_stock_cache(code, result['data'], ttl=30)
        return result
    finally:
        loop.close()


# 测试
if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 70)
    print("🦞 多数据源并行获取 - 修复版")
    print("=" * 70)
    
    test_codes = ['002828', '600370', '600683']
    
    for code in test_codes:
        print(f"\n获取 {code}...")
        result = get_realtime_data(code)
        
        if result.get('success'):
            data = result['data']
            print(f"  ✅ 成功 | 来源：{result['source_name']} | 耗时：{result['elapsed']*1000:.1f}ms")
            print(f"     现价：¥{data['current']:.2f} ({data['change_pct']:+.1f}%)")
            if data.get('turnover'):
                print(f"     换手率：{data['turnover']:.2f}%")
            if data.get('volume_ratio'):
                print(f"     量比：{data['volume_ratio']:.2f}")
        else:
            print(f"  ❌ 失败 | 错误：{result.get('error', 'Unknown')}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成")
    print("=" * 70)

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")
