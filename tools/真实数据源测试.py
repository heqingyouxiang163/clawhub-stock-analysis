#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
真实数据源测试 - 测试可用的股票数据 API
"""

import requests
import time

def test_sina(code):
    """测试新浪财经"""
    market = 'sh' if code.startswith('6') else 'sz'
    url = f"http://hq.sinajs.cn/list={market}{code}"
    
    headers = {
        'Referer': 'https://finance.sina.com.cn/',
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200 and response.text.strip():
            print(f"✅ 新浪财经：{code} - 成功")
            print(f"   数据：{response.text[:100]}")
            return True
        else:
            print(f"❌ 新浪财经：{code} - 失败 ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ 新浪财经：{code} - 异常 ({e})")
        return False

def test_eastmoney(code):
    """测试东方财富"""
    market = '1' if code.startswith('6') else '0'
    url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60"
    
    headers = {
        'Referer': 'http://quote.eastmoney.com/',
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        if data.get('data'):
            print(f"✅ 东方财富：{code} - 成功")
            print(f"   最新价：{data['data'].get('f46', 'N/A')}")
            return True
        else:
            print(f"❌ 东方财富：{code} - 无数据")
            return False
    except Exception as e:
        print(f"❌ 东方财富：{code} - 异常 ({e})")
        return False

def test_akshare(code):
    """测试 akshare"""
    try:
        import akshare as ak
        df = ak.stock_zh_a_spot_em()
        result = df[df['代码'] == code]
        if not result.empty:
            print(f"✅ akshare: {code} - 成功")
            print(f"   最新价：{result['最新价'].values[0]}")
            return True
        else:
            print(f"❌ akshare: {code} - 未找到")
            return False
    except Exception as e:
        print(f"❌ akshare: {code} - 异常 ({e})")
        return False

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    print("=" * 50)
    print("🦞 真实数据源测试")
    print("=" * 50)
    
    test_codes = ["002828", "600519"]
    
    for code in test_codes:
        print(f"\n测试 {code}:")
        print("-" * 30)
        
        # 测试各数据源
        test_sina(code)
        time.sleep(0.5)
        
        test_eastmoney(code)
        time.sleep(0.5)
        
        test_akshare(code)
        time.sleep(0.5)
