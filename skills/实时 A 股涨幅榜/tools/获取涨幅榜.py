#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 实时 A 股涨幅榜获取工具

功能：获取沪深 A 股实时涨幅榜前 150 名
数据源：东方财富网公开实时行情接口
用途：个人学习研究，请勿高频调用

作者：炒股龙虾系统
版本：v1.0
最后更新：2026-03-27
"""

import requests
import time
from datetime import datetime


def get_realtime_gainers(limit=150):
    """
    获取沪深 A 股实时涨幅榜
    
    Args:
        limit: 返回数量，默认 150 只
        
    Returns:
        list: 股票列表，包含排名、代码、名称、涨幅、现价、涨跌额
    """
    
    print(f"📈 正在获取沪深 A 股实时涨幅榜 (前{limit}名)...")
    start_time = time.time()
    
    # 东方财富网实时行情 API
    # 沪深 A 股：m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23
    # m:0=深市，m:1=沪市
    # t:6=深市主板，t:80=创业板，t:2=沪市主板，t:23=科创板
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    
    params = {
        'pn': '1',  # 页码
        'pz': str(limit),  # 每页数量
        'po': '1',  # 降序排列
        'np': '1',
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': '2',
        'invt': '2',
        'fid': 'f3',  # 按涨幅排序
        'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',  # 沪深 A 股
        'fields': 'f12,f14,f3,f2,f4,f268',  # 代码，名称，涨幅，现价，涨跌额，排名
        '_': str(int(time.time() * 1000))
    }
    
    headers = {
        'Referer': 'http://quote.eastmoney.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'diff' in data['data']:
                stocks = []
                
                for idx, item in enumerate(data['data']['diff'], 1):
                    code = item.get('f12', '')
                    name = item.get('f14', '')
                    change_pct = item.get('f3', 0)
                    current = item.get('f2', 0)
                    change_amt = item.get('f4', 0)
                    
                    # 跳过无效数据
                    if not code or not name or current == 0:
                        continue
                    
                    stocks.append({
                        'rank': idx,
                        'code': code,
                        'name': name,
                        'change_pct': change_pct,
                        'current': current,
                        'change_amt': change_amt
                    })
                
                print(f"✅ 成功获取 {len(stocks)}只股票，耗时{elapsed*1000:.0f}ms")
                return stocks
            else:
                print("❌ 数据格式异常")
                return []
        else:
            print(f"❌ 请求失败：HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ 获取失败：{e}")
        return []


def display_gainers(stocks):
    """
    格式化显示涨幅榜
    
    Args:
        stocks: 股票列表
    """
    
    if not stocks:
        print("❌ 暂无数据")
        return
    
    print("\n" + "=" * 70)
    print(f"📈 沪深 A 股实时涨幅榜")
    print(f"⏰ 更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"{'排名':<6} {'代码':<10} {'名称':<15} {'涨幅':>10} {'现价':>10} {'涨跌额':>10}")
    print("-" * 70)
    
    for s in stocks:
        # 涨幅颜色标记
        change_str = f"{s['change_pct']:+.2f}%"
        
        print(f"{s['rank']:<6} {s['code']:<10} {s['name']:<15} {change_str:>10} {s['current']:>10.2f} {s['change_amt']:>+10.2f}")
    
    print("-" * 70)
    print(f"📊 共展示 {len(stocks)}只股票 | 数据源：东方财富网")
    print("=" * 70 + "\n")


def main():
    """主函数"""
    
    print("\n🦞 炒股龙虾 - 实时 A 股涨幅榜查询工具")
    print("-" * 50)
    
    # 获取涨幅榜
    stocks = get_realtime_gainers(limit=150)
    
    # 显示结果
    display_gainers(stocks)
    
    # 返回数据供其他模块使用
    return stocks


if __name__ == "__main__":
    main()
