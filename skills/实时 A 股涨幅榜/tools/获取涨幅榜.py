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
    获取沪深 A 股实时涨幅榜（多数据源）
    
    Args:
        limit: 返回数量，默认 150 只
        
    Returns:
        list: 股票列表，包含排名、代码、名称、涨幅、现价、涨跌额
    """
    
    print(f"📈 正在获取沪深 A 股实时涨幅榜 (前{limit}名)...")
    start_time = time.time()
    
    # 数据源 1：东方财富
    stocks = _fetch_eastmoney(limit)
    if stocks:
        elapsed = time.time() - start_time
        print(f"✅ 成功获取{len(stocks)}只股票，耗时{elapsed*1000:.0f}ms")
        return stocks
    
    # 数据源 2：新浪财经（备用）
    print("⚠️ 东方财富失败，切换到新浪财经...")
    stocks = _fetch_sina(limit)
    if stocks:
        elapsed = time.time() - start_time
        print(f"✅ 成功获取{len(stocks)}只股票，耗时{elapsed*1000:.0f}ms")
        return stocks
    
    print("❌ 获取失败：所有数据源都失败")
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


def _fetch_eastmoney(limit=150):
    """东方财富网实时行情 API"""
    try:
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'pn': '1',
            'pz': str(limit),
            'po': '1',
            'np': '1',
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'm:0 t:6,m:1 t:2',  # 沪深主板
            'fields': 'f12,f14,f3,f2,f4',
            '_': str(int(time.time() * 1000))
        }
        headers = {
            'Referer': 'http://quote.eastmoney.com/',
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
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
                    if code and name and current > 0:
                        stocks.append({
                            'rank': idx,
                            'code': code,
                            'name': name,
                            'change_pct': change_pct,
                            'current': current,
                            'change_amt': change_amt
                        })
                return stocks
    except:
        pass
    return None


def _fetch_sina(limit=150):
    """新浪财经备用数据源"""
    try:
        url = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple'
        params = {
            'page': '1',
            'num': str(limit * 2),
            'sort': 'changepercent',
            'asc': '0',
            'node': 'hs_a'
        }
        headers = {
            'Referer': 'http://vip.stock.finance.sina.com.cn/',
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            stocks = []
            idx = 0
            for s in data:
                code = s.get('code', '')
                # 只保留主板
                if not (code.startswith('60') or code.startswith('00')):
                    continue
                idx += 1
                if idx > limit:
                    break
                change_pct = float(s.get('changepercent', 0) or 0)
                current = float(s.get('trade', 0) or 0)
                change_amt = float(s.get('pricechange', 0) or 0)
                if current > 0:
                    stocks.append({
                        'rank': idx,
                        'code': code,
                        'name': s.get('name', '?'),
                        'change_pct': change_pct,
                        'current': current,
                        'change_amt': change_amt
                    })
            return stocks
    except:
        pass
    return None


if __name__ == "__main__":
    main()
