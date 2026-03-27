#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓实时监控 - 简单直接版本
实时获取持仓股最新数据，不依赖复杂分析
"""

import sys
import requests
import time
from datetime import datetime

sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 持仓配置 import HOLDINGS


def get_stock_price_sina(code):
    """新浪财经获取单只股票实时数据"""
    try:
        if code.startswith('6'):
            symbol = f"sh{code}"
        else:
            symbol = f"sz{code}"
        
        url = f"http://hq.sinajs.cn/list={symbol}"
        headers = {'Referer': 'http://finance.sina.com.cn/'}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.text
            if '=' in data:
                parts = data.split('=')[1].strip('"').split(',')
                if len(parts) >= 32:
                    name = parts[0]
                    current = float(parts[3])
                    pre_close = float(parts[2])
                    change_pct = (current - pre_close) / pre_close * 100
                    change_amt = current - pre_close
                    return {
                        'name': name,
                        'current': current,
                        'change_pct': change_pct,
                        'change_amt': change_amt
                    }
    except Exception as e:
        pass
    return None


def monitor_holdings():
    """监控持仓股"""
    
    print("=" * 70)
    print("🦞 持仓实时监控")
    print(f"⏰ 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    total_value = 0
    total_profit = 0
    
    print("\n📊 持仓明细:\n")
    print(f"{'股票':<12} {'代码':<10} {'市值':>10} {'盈亏':>12} {'盈亏率':>10} {'涨幅':>10} {'现价':>10}")
    print("-" * 90)
    
    for holding in HOLDINGS:
        code = holding['code']
        name = holding['name']
        cost_value = holding.get('market_value', 0) - holding.get('profit', 0)
        
        # 获取实时数据
        realtime = get_stock_price_sina(code)
        
        if realtime:
            # 计算实时市值和盈亏
            if holding.get('profit_pct', 0) != 0:
                # 根据涨幅重新计算
                current_value = cost_value * (1 + realtime['change_pct'] / 100)
                current_profit = current_value - cost_value
                current_profit_pct = (current_profit / cost_value) * 100 if cost_value > 0 else 0
            else:
                current_value = holding.get('market_value', 0)
                current_profit = holding.get('profit', 0)
                current_profit_pct = holding.get('profit_pct', 0)
            
            total_value += current_value
            total_profit += current_profit
            
            profit_str = f"+{current_profit:.2f}" if current_profit >= 0 else f"{current_profit:.2f}"
            change_str = f"+{realtime['change_pct']:.2f}%" if realtime['change_pct'] >= 0 else f"{realtime['change_pct']:.2f}%"
            
            print(f"{name:<12} {code:<10} {current_value:>10.0f} {profit_str:>12} {current_profit_pct:>9.2f}% {change_str:>10} {realtime['current']:>9.2f}")
        else:
            # 使用配置数据
            current_value = holding.get('market_value', 0)
            current_profit = holding.get('profit', 0)
            current_profit_pct = holding.get('profit_pct', 0)
            
            total_value += current_value
            total_profit += current_profit
            
            profit_str = f"+{current_profit:.2f}" if current_profit >= 0 else f"{current_profit:.2f}"
            
            print(f"{name:<12} {code:<10} {current_value:>10.0f} {profit_str:>12} {current_profit_pct:>9.2f}% {'N/A':>10} {'N/A':>9}")
    
    print("-" * 90)
    print(f"{'合计':<12} {'':<10} {total_value:>10.0f} {total_profit:>+12.2f} {'':<10} {'':<10} {'':<9}")
    print("=" * 70)
    
    return {
        'total_value': total_value,
        'total_profit': total_profit
    }


if __name__ == "__main__":
    monitor_holdings()
