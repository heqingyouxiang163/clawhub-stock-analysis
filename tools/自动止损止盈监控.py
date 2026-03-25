#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动止损止盈监控 (优化版)
用途：每 1 分钟检查持仓股盈亏，触发条件自动提醒
优化：简化逻辑，快速执行
"""

import requests
import time
from datetime import datetime
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')

# 统一引用持仓配置文件
from 持仓配置 import HOLDINGS

# 止损止盈阈值
STOP_LOSS_PCT = -5.0   # -5% 止损
TAKE_PROFIT_PCT = 10.0  # +10% 止盈

# 止损止盈阈值
STOP_LOSS_PCT = -5.0   # -5% 止损
TAKE_PROFIT_PCT = 10.0  # +10% 止盈


def get_price(code):
    """快速获取股价 (腾讯财经)"""
    try:
        prefix = 'sh' if code.startswith('6') else 'sz'
        url = f"http://qt.gtimg.cn/q={prefix}{code}"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            text = r.content.decode('gbk')
            if '=' in text:
                data = text.split('=')[1].strip('"').split('~')
                if len(data) > 3:
                    return float(data[3]) if data[3] else 0
    except:
        pass
    return 0


def check_holdings():
    """检查持仓"""
    alerts = []
    
    for holding in HOLDINGS:
        code = holding['code']
        name = holding['name']
        cost = holding['cost']
        shares = holding.get('shares', 1000)
        
        price = get_price(code)
        if price == 0:
            continue
        
        pnl_pct = (price - cost) / cost * 100
        pnl_amount = (price - cost) * shares
        
        # 判断触发条件
        if pnl_pct <= STOP_LOSS_PCT:
            alerts.append({
                'code': code,
                'name': name,
                'price': price,
                'pnl_pct': pnl_pct,
                'pnl_amount': pnl_amount,
                'type': '止损',
                'action': f'⚠️ 触发止损 ({STOP_LOSS_PCT}%)'
            })
        elif pnl_pct >= TAKE_PROFIT_PCT:
            alerts.append({
                'code': code,
                'name': name,
                'price': price,
                'pnl_pct': pnl_pct,
                'pnl_amount': pnl_amount,
                'type': '止盈',
                'action': f'✅ 触发止盈 ({TAKE_PROFIT_PCT}%)'
            })
        else:
            alerts.append({
                'code': code,
                'name': name,
                'price': price,
                'pnl_pct': pnl_pct,
                'pnl_amount': pnl_amount,
                'type': '持有',
                'action': '继续持有'
            })
    
    return alerts


def print_report(alerts):
    """打印报告"""
    print("=" * 60)
    print("🦞 自动止损止盈监控")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    for a in alerts:
        icon = "🔴" if a['type'] == '止损' else "🟢" if a['type'] == '止盈' else "🟡"
        print(f"{icon} {a['code']} {a['name']}")
        print(f"   现价：¥{a['price']:.2f} | 盈亏：{a['pnl_pct']:+.1f}%")
        print(f"   状态：{a['action']}")
        print()
    
    # 汇总
    stop_loss = [a for a in alerts if a['type'] == '止损']
    take_profit = [a for a in alerts if a['type'] == '止盈']
    
    if stop_loss:
        print(f"⚠️ 止损警告：{len(stop_loss)} 只")
    if take_profit:
        print(f"✅ 止盈机会：{len(take_profit)} 只")
    
    print("=" * 60)


if __name__ == "__main__":
    start = time.time()
    
    alerts = check_holdings()
    print_report(alerts)
    
    elapsed = time.time() - start
    print(f"⏱️  执行耗时：{elapsed*1000:.0f}ms")
