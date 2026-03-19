#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能股票分析系统 - 腾讯财经版
替代 akshare，使用腾讯财经 API + 本地历史数据
"""

import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 腾讯财经_API import get_multiple_stocks, get_single_stock
from datetime import datetime, time
import json
import os

# ==================== 配置区 ====================

HOLDINGS = [
    {"code": "002342", "name": "巨力索具", "cost": 14.132, "shares": 500},
    {"code": "603778", "name": "国晟科技", "cost": 24.410, "shares": 500},
]

OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/智能分析"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 本地历史数据缓存 (盘后写入)
HISTORY_CACHE_FILE = "/home/admin/openclaw/workspace/temp/历史数据缓存.json"


# ==================== 历史数据 ====================

def load_history_cache():
    """加载本地历史数据缓存"""
    if os.path.exists(HISTORY_CACHE_FILE):
        try:
            with open(HISTORY_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_history_cache(data):
    """保存历史数据到本地"""
    try:
        with open(HISTORY_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存历史数据失败：{e}")


def get_stock_history(code, days=20):
    """获取股票历史数据 (从本地缓存)"""
    cache = load_history_cache()
    return cache.get(code, [])


# ==================== 时间判断 ====================

def get_current_mode():
    """根据当前时间判断分析模式"""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    
    is_trading_day = weekday < 5
    
    if not is_trading_day:
        return {"mode": "盘后复盘", "desc": "非交易日"}
    
    if current_time < time(9, 25):
        return {"mode": "盘前", "desc": "9:25 前"}
    elif current_time < time(11, 30):
        return {"mode": "盘中", "desc": "早盘"}
    elif current_time < time(13, 0):
        return {"mode": "午间", "desc": "午休"}
    elif current_time < time(15, 0):
        return {"mode": "盘中", "desc": "午盘"}
    else:
        return {"mode": "盘后", "desc": "15:00 后"}


# ==================== 分析函数 ====================

def analyze_stock(code, name, cost, shares):
    """分析单只股票"""
    print(f"\n{'='*70}")
    print(f"📈 {name} ({code})")
    print(f"{'='*70}")
    
    # 获取实时数据
    data = get_single_stock(code)
    
    if not data.get('success'):
        print(f"❌ 获取数据失败")
        return None
    
    current = data['current']
    change = data['change_pct']
    position_value = current * shares
    profit = (current - cost) * shares
    profit_pct = ((current - cost) / cost) * 100
    
    print(f"\n【实时数据】")
    print(f"  现价：¥{current:.2f} ({change:+.1f}%)")
    print(f"  持仓：¥{position_value:.0f} ({profit:+.0f}元, {profit_pct:+.1f}%)")
    
    # 获取历史数据
    history = get_stock_history(code)
    
    if history and len(history) >= 20:
        # 计算均线
        closes = [d['close'] for d in history[-20:]]
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        ma20 = sum(closes[-20:]) / 20
        
        print(f"\n【技术指标】")
        print(f"  MA5: {ma5:.2f}")
        print(f"  MA10: {ma10:.2f}")
        print(f"  MA20: {ma20:.2f}")
        
        if ma5 > ma10 > ma20:
            print(f"  均线：🟢 多头排列")
        elif ma5 < ma10 < ma20:
            print(f"  均线：🔴 空头排列")
        else:
            print(f"  均线：🟡 纠缠震荡")
    
    # 形态识别
    print(f"\n【形态识别】")
    
    if change >= 9.5:
        print(f"  🔥 涨停板")
    elif change >= 5:
        print(f"  ✅ 大涨{change:.1f}%")
    elif change >= 3:
        print(f"  ✅ 上涨{change:.1f}%")
    elif change >= 0:
        print(f"  🟡 微涨{change:.1f}%")
    else:
        print(f"  🔴 下跌{change:.1f}%")
    
    # 操作建议
    print(f"\n【操作建议】")
    
    if profit_pct < -10:
        print(f"  ⚠️ 已破止损线，考虑止损")
    elif profit_pct < -5:
        print(f"  ⚠️ 接近止损线，密切关注")
    elif profit_pct > 10:
        print(f"  ✅ 盈利良好，可继续持有")
    else:
        print(f"  🟡 震荡持有，等待方向")
    
    return {
        "code": code,
        "name": name,
        "current": current,
        "change": change,
        "profit": profit,
        "profit_pct": profit_pct
    }


# ==================== 主函数 ====================

def main():
    """主函数"""
    mode = get_current_mode()
    
    print("=" * 75)
    print("🦞 智能分析系统 - 腾讯财经版")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模式：{mode['mode']} ({mode['desc']})")
    print("=" * 75)
    
    results = []
    
    for h in HOLDINGS:
        result = analyze_stock(h["code"], h["name"], h["cost"], h["shares"])
        if result:
            results.append(result)
    
    print(f"\n{'='*75}")
    print("总结:")
    total_profit = sum(r['profit'] for r in results)
    print(f"  总盈亏：{total_profit:+.0f}元")
    print(f"{'='*75}")
    
    return results


if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    main()
