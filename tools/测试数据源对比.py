#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股数据源实时获取对比测试
测试对象：腾讯财经、东方财富、新浪财经、网易财经
"""

import requests
import time
from datetime import datetime


# ==================== 测试股票池 ====================

TEST_STOCKS = [
    "002828",  # 贝肯能源
    "002342",  # 巨力索具
    "603778",  # 国晟科技
    "600569",  # 安阳钢铁
    "002455",  # 百川股份
]


# ==================== 腾讯财经 ====================

def test_tencent():
    """腾讯财经 - 批量获取"""
    print("\n📊 腾讯财经测试...")
    start = time.time()
    
    # 转腾讯格式
    symbols = []
    for code in TEST_STOCKS:
        if code.startswith('6'):
            symbols.append(f"sh{code}")
        else:
            symbols.append(f"sz{code}")
    
    code_list = ','.join(symbols)
    url = f"http://qt.gtimg.cn/q={code_list}"
    headers = {'Referer': 'https://stockapp.finance.qq.com/'}
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            lines = text.strip().split(';')
            
            count = 0
            for line in lines:
                if '=' in line:
                    parts = line.split('=')
                    if len(parts) >= 2:
                        data = parts[1].strip('"').split('~')
                        if len(data) >= 32 and data[3]:
                            count += 1
            
            elapsed = time.time() - start
            print(f"  ✅ 成功：{count}/{len(TEST_STOCKS)}只")
            print(f"  ⏱️  耗时：{elapsed*1000:.0f}ms")
            print(f"  📈 速度：{count/elapsed:.0f}只/秒")
            return True, elapsed, count
    except Exception as e:
        print(f"  ❌ 失败：{str(e)[:40]}")
        return False, 0, 0


# ==================== 东方财富 ====================

def test_em():
    """东方财富 - 获取涨幅排名"""
    print("\n📊 东方财富测试...")
    start = time.time()
    
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 100,
        'po': 1,
        'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2,
        'invt': 2,
        'fid': 'f3',
        'fs': 'm:0+m:1',
        'fields': 'f12,f14,f3'
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10,
                           headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            if data.get('data') and data['data'].get('diff'):
                stocks = data['data']['diff']
                elapsed = time.time() - start
                print(f"  ✅ 成功：{len(stocks)}只")
                print(f"  ⏱️  耗时：{elapsed*1000:.0f}ms")
                print(f"  📈 速度：{len(stocks)/elapsed:.0f}只/秒")
                return True, elapsed, len(stocks)
    except Exception as e:
        print(f"  ❌ 失败：{str(e)[:40]}")
        return False, 0, 0


# ==================== 新浪财经 ====================

def test_sina():
    """新浪财经 - 批量获取"""
    print("\n📊 新浪财经测试...")
    start = time.time()
    
    # 转新浪格式
    symbols = []
    for code in TEST_STOCKS:
        if code.startswith('6'):
            symbols.append(f"sh{code}")
        else:
            symbols.append(f"sz{code}")
    
    code_list = ','.join(symbols)
    url = f"http://hq.sinajs.cn/list={code_list}"
    
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            text = resp.content.decode('gbk')
            lines = text.strip().split(';')
            
            count = sum(1 for line in lines if '=' in line and len(line.split('=')) >= 2)
            
            elapsed = time.time() - start
            print(f"  ✅ 成功：{count}/{len(TEST_STOCKS)}只")
            print(f"  ⏱️  耗时：{elapsed*1000:.0f}ms")
            print(f"  📈 速度：{count/elapsed:.0f}只/秒")
            return True, elapsed, count
    except Exception as e:
        print(f"  ❌ 失败：{str(e)[:40]}")
        return False, 0, 0


# ==================== 网易财经 ====================

def test_netease():
    """网易财经 - 批量获取"""
    print("\n📊 网易财经测试...")
    start = time.time()
    
    # 转网易格式
    symbols = []
    for code in TEST_STOCKS:
        if code.startswith('6'):
            symbols.append(f"0{code}")  # 沪市加 0
        else:
            symbols.append(f"1{code}")  # 深市加 1
    
    code_list = ','.join(symbols)
    url = f"http://api.money.126.net/data/feed/{code_list}"
    
    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            text = resp.content.decode('utf-8')
            # 网易返回 JSONP 格式
            if '_ntes_quote_callback' in text:
                count = text.count('"code"')
                elapsed = time.time() - start
                print(f"  ✅ 成功：{count}/{len(TEST_STOCKS)}只")
                print(f"  ⏱️  耗时：{elapsed*1000:.0f}ms")
                print(f"  📈 速度：{count/elapsed:.0f}只/秒")
                return True, elapsed, count
    except Exception as e:
        print(f"  ❌ 失败：{str(e)[:40]}")
        return False, 0, 0


# ==================== 主测试 ====================

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 70)
    print("🦞 A 股数据源实时获取对比测试")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试股票：{len(TEST_STOCKS)}只")
    print("=" * 70)
    
    results = []
    
    # 测试各数据源
    tencent_result = test_tencent()
    results.append(("腾讯财经", *tencent_result))
    
    em_result = test_em()
    results.append(("东方财富", *em_result))
    
    sina_result = test_sina()
    results.append(("新浪财经", *sina_result))
    
    netease_result = test_netease()
    results.append(("网易财经", *netease_result))
    
    # 汇总排名
    print("\n" + "=" * 70)
    print("📊 数据源性能对比")
    print("=" * 70)
    print(f"{'数据源':<12} {'状态':<8} {'获取数量':<12} {'耗时':<12} {'速度':<12}")
    print("-" * 70)
    
    for name, success, elapsed, *extra in results:
        status = "✅ 成功" if success else "❌ 失败"
        count = extra[0] if extra else len(TEST_STOCKS)
        speed = count/elapsed if elapsed > 0 else 0
        
        print(f"{name:<12} {status:<8} {count:<12} {elapsed*1000:>6.0f}ms      {speed:>6.0f}只/秒")
    
    print("=" * 70)
    
    # 推荐最优方案
    print("\n💡 推荐方案:")
    
    successful = [(name, elapsed, count) for name, success, elapsed, count in results if success]
    if successful:
        # 按速度排序
        successful.sort(key=lambda x: x[1])
        best = successful[0]
        print(f"  🏆 最快：{best[0]} ({best[1]*1000:.0f}ms, {best[2]}只)")
        
        # 按获取数量排序
        successful.sort(key=lambda x: x[2], reverse=True)
        most = successful[0]
        print(f"  📊 最全：{most[0]} ({most[2]}只)")
    else:
        print("  ⚠️ 所有数据源均失败，请检查网络连接")
    
    print()
