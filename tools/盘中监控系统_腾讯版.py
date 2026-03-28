#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中实时监控系统 - 腾讯财经版
替代 akshare，使用腾讯财经 API
"""

import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 腾讯财经_API import get_multiple_stocks, get_single_stock
from datetime import datetime
import json
import os
import time

# ==================== 配置区 ====================

# 统一引用持仓配置文件
from 持仓配置 import HOLDINGS

OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/盘中监控"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==================== 数据获取 ====================

def get_stock_realtime(code):
    """获取个股实时数据 (腾讯财经)"""
    data = get_single_stock(code)
    
    if not data.get('success'):
        return None
    
    return {
        "code": data['code'],
        "name": data['name'],
        "price": data['current'],
        "change": data['change_pct'],
        "change_amount": data['current'] - data['prev_close'],
        "volume": data['amount'] / data['current'] if data['current'] > 0 else 0,
        "amount": data['amount'],
        "high": data['high'],
        "low": data['low'],
        "open": data['open'],
        "prev_close": data['prev_close'],
    }


def get_market_sentiment_simple():
    """获取简化版市场情绪 (从股票池推断)"""
    # 获取股票池数据
    from 腾讯财经_API import get_all_stock_pool
    all_data = get_all_stock_pool()
    
    if not all_data:
        return {"up": 0, "down": 0, "limit_up": 0, "limit_down": 0, "ratio": 1}
    
    up = sum(1 for d in all_data.values() if d.get('change_pct', 0) > 0)
    down = sum(1 for d in all_data.values() if d.get('change_pct', 0) < 0)
    limit_up = sum(1 for d in all_data.values() if d.get('change_pct', 0) >= 9.5)
    limit_down = sum(1 for d in all_data.values() if d.get('change_pct', 0) <= -9.5)
    
    return {
        "up": up,
        "down": down,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "ratio": up / down if down > 0 else 999,
    }


# ==================== 形态识别 ====================

def check_intraday_pattern(code, realtime_data):
    """检查分时图形态"""
    if not realtime_data:
        return {"is_pattern": False, "score": 0, "details": ["数据不足"]}
    
    price = realtime_data.get("price", 0)
    open_p = realtime_data.get("open", 0)
    high = realtime_data.get("high", 0)
    low = realtime_data.get("low", 0)
    prev_close = realtime_data.get("prev_close", open_p)
    
    # 估算分时均线
    estimated_vwap = (open_p + high + low + price) / 4
    
    details = []
    score = 0
    
    # 1. 股价在分时均线上方
    if price > estimated_vwap * 1.01:
        score += 30
        details.append(f"✅ 股价在均线上方")
    elif price > estimated_vwap:
        score += 20
        details.append(f"🟡 股价在均线上方 (微弱)")
    else:
        details.append(f"❌ 股价跌破均线")
    
    # 2. 涨幅
    change = realtime_data.get("change", 0)
    if change > 5:
        score += 25
        details.append(f"✅ 大涨{change:.1f}%")
    elif change > 3:
        score += 15
        details.append(f"✅ 上涨{change:.1f}%")
    elif change > 0:
        score += 5
        details.append(f"🟡 微涨{change:.1f}%")
    else:
        details.append(f"❌ 下跌{change:.1f}%")
    
    return {
        "is_pattern": score >= 40,
        "score": score,
        "details": details
    }


# ==================== 监控主函数 ====================

def monitor_holdings():
    """监控持仓股"""
    print("=" * 75)
    print("🦞 盘中监控系统 - 腾讯财经版")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)
    print()
    
    # 获取所有持仓数据
    codes = [h["code"] for h in HOLDINGS]
    all_data = get_multiple_stocks(codes)
    
    results = []
    
    for holding in HOLDINGS:
        code = holding["code"]
        cost = holding["cost"]
        shares = holding["shares"]
        
        data = all_data.get(code)
        
        if not data:
            print(f"❌ {code} {holding['name']}: 获取数据失败")
            continue
        
        # 计算盈亏
        current = data['current']
        change_pct = data['change_pct']
        market_value = current * shares
        profit_loss = (current - cost) * shares
        profit_pct = (current - cost) / cost * 100
        
        # 检查形态
        realtime = get_stock_realtime(code)
        pattern = check_intraday_pattern(code, realtime)
        
        result = {
            "code": code,
            "name": data['name'],
            "current": current,
            "change_pct": change_pct,
            "market_value": market_value,
            "profit_loss": profit_loss,
            "profit_pct": profit_pct,
            "pattern_score": pattern['score'],
            "details": pattern['details']
        }
        results.append(result)
        
        # 输出
        status = "🟢" if profit_pct > 0 else "🔴" if profit_pct < -5 else "🟡"
        print(f"{status} {code} {data['name']}")
        print(f"   现价：¥{current:.2f} ({change_pct:+.1f}%)")
        print(f"   持仓：¥{market_value:.0f} ({profit_loss:+.0f}元, {profit_pct:+.1f}%)")
        print(f"   形态：{pattern['score']}分 - {', '.join(pattern['details'][:2])}")
        print()
    
    # 市场情绪
    print("=" * 75)
    print("市场情绪:")
    sentiment = get_market_sentiment_simple()
    print(f"  上涨：{sentiment['up']}家 | 下跌：{sentiment['down']}家")
    print(f"  涨停：{sentiment['limit_up']}家 | 跌停：{sentiment['limit_down']}家")
    print("=" * 75)
    
    return results


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    monitor_holdings()
