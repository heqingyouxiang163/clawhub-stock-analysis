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

# 缩量涨停检测阈值
SHRINK_TURNOVER_THRESHOLD = 5.0  # 换手率<5% 视为缩量


def get_stock_data(code):
    """获取股票详细数据 (腾讯财经)"""
    try:
        prefix = 'sh' if code.startswith('6') else 'sz'
        url = f"http://qt.gtimg.cn/q={prefix}{code}"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            text = r.content.decode('gbk')
            if '=' in text:
                data = text.split('=')[1].strip('"').split('~')
                if len(data) > 40:
                    # 腾讯字段：[3]=现价，[5]=开盘，[6]=成交量 (手), [32]=涨幅%, [33]=最高，[34]=最低，[37]=成交额 (万), [38]=换手率%
                    return {
                        'price': float(data[3]) if data[3] else 0,
                        'change_pct': float(data[32]) if data[32] else 0,
                        'volume': float(data[6]) if data[6] else 0,  # 成交量 (手)
                        'amount': float(data[37]) if data[37] else 0,  # 成交额 (万)
                        'turnover': float(data[38]) if data[38] else 0,  # 换手率%
                        'high': float(data[33]) if data[33] else 0,
                        'low': float(data[34]) if data[34] else 0,
                        'open': float(data[5]) if data[5] else 0,
                    }
    except:
        pass
    return None


def is_shrink_limit_up(data):
    """判断是否缩量涨停板 (继续持有信号)"""
    if not data:
        return False
    
    # 涨停判断 (≥9.5%)
    if data['change_pct'] < 9.5:
        return False
    
    # 缩量判断：换手率<5% 视为缩量
    is_shrink = (data['turnover'] < SHRINK_TURNOVER_THRESHOLD)
    
    # 封板质量：最高价=现价 (封死涨停)
    is_sealed = (abs(data['high'] - data['price']) < 0.01)
    
    return is_shrink and is_sealed


def is_weak_limit_up(data):
    """判断是否烂板/放量涨停 (止盈信号)"""
    if not data:
        return False
    
    # 涨停判断
    if data['change_pct'] < 9.5:
        return False
    
    # 放量判断：换手率>15% 视为放量
    is_heavy = (data['turnover'] > 15.0)
    
    # 烂板判断：最高>现价 (涨停被打开过)
    is_weak = (data['high'] > data['price'] + 0.05)
    
    return is_heavy or is_weak


def check_holdings():
    """检查持仓"""
    alerts = []
    
    for holding in HOLDINGS:
        code = holding['code']
        name = holding['name']
        cost = holding['cost']
        shares = holding.get('shares', 1000)
        
        data = get_stock_data(code)
        if not data or data['price'] == 0:
            continue
        
        price = data['price']
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
            # 智能止盈：判断涨停质量
            if is_shrink_limit_up(data):
                alerts.append({
                    'code': code,
                    'name': name,
                    'price': price,
                    'pnl_pct': pnl_pct,
                    'pnl_amount': pnl_amount,
                    'type': '缩量涨停',
                    'action': '🚀 缩量涨停，继续持有！'
                })
            elif is_weak_limit_up(data):
                alerts.append({
                    'code': code,
                    'name': name,
                    'price': price,
                    'pnl_pct': pnl_pct,
                    'pnl_amount': pnl_amount,
                    'type': '烂板/放量',
                    'action': '⚠️ 烂板/放量，建议止盈！'
                })
            else:
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
    print("🦞 自动止损止盈监控 (智能版)")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    for a in alerts:
        if a['type'] == '止损':
            icon = "🔴"
        elif a['type'] == '缩量涨停':
            icon = "🚀"
        elif a['type'] == '烂板/放量':
            icon = "⚠️"
        elif a['type'] == '止盈':
            icon = "🟢"
        else:
            icon = "🟡"
        
        print(f"{icon} {a['code']} {a['name']}")
        print(f"   现价：¥{a['price']:.2f} | 盈亏：{a['pnl_pct']:+.1f}%")
        print(f"   状态：{a['action']}")
        print()
    
    # 汇总
    stop_loss = [a for a in alerts if a['type'] == '止损']
    take_profit = [a for a in alerts if a['type'] == '止盈']
    shrink_limit = [a for a in alerts if a['type'] == '缩量涨停']
    weak_limit = [a for a in alerts if a['type'] == '烂板/放量']
    
    if stop_loss:
        print(f"⚠️ 止损警告：{len(stop_loss)} 只")
    if shrink_limit:
        print(f"🚀 缩量涨停：{len(shrink_limit)} 只 (继续持有！)")
    if weak_limit:
        print(f"⚠️ 烂板/放量：{len(weak_limit)} 只 (建议止盈)")
    if take_profit:
        print(f"✅ 普通止盈：{len(take_profit)} 只")
    
    print("=" * 60)


if __name__ == "__main__":
    start = time.time()
    
    alerts = check_holdings()
    print_report(alerts)
    
    elapsed = time.time() - start
    print(f"⏱️  执行耗时：{elapsed*1000:.0f}ms")
