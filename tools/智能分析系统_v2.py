#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能股票分析系统 v2.0
优化版：月收益目标 50%+
"""

import akshare as ak
import pandas as pd
from datetime import datetime, time
import json
import os

# ==================== 配置区 ====================

# 统一引用持仓配置文件
import sys
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
from 持仓配置 import HOLDINGS

OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/智能分析_v2"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VERSION = "v2.0"
TARGET_RETURN = "50%/月"

# ==================== 时间判断逻辑 ====================

def get_current_mode():
    """根据当前时间判断分析模式"""
    now = datetime.now()
    current_time = now.time()
    weekday = now.weekday()
    
    is_trading_day = weekday < 5
    
    if not is_trading_day:
        return {"mode": "盘后复盘", "logic": "盘后"}
    
    if current_time < time(9, 25):
        return {"mode": "盘前准备", "logic": "盘后"}
    elif current_time < time(11, 30):
        return {"mode": "盘中监控 (早盘)", "logic": "盘中"}
    elif current_time < time(13, 0):
        return {"mode": "午间休市", "logic": "盘中"}
    elif current_time < time(15, 0):
        return {"mode": "盘中监控 (午后)", "logic": "盘中"}
    else:
        return {"mode": "盘后分析", "logic": "盘后"}

# ==================== v2.0 选股公式 ====================

def select_stocks_v2():
    """v2.0 选股公式"""
    
    criteria = {
        "首板选股": {
            "集合竞价高开": "3-5%",
            "竞价量": ">昨日 15%",
            "超大单流入": ">1000 万",
            "涨停基因评分": ">70",
            "情绪周期": "启动/强势",
            "板块排名": "前 3",
            "流通市值": "50-150 亿",
            "股价": "5-40 元",
            "预期成功率": "75%"
        },
        "连板选股": {
            "昨日涨停质量": "A 级",
            "集合竞价高开": "5-8%",
            "封单": ">2 亿",
            "超大单流入": ">3000 万",
            "连板数": "≤3",
            "情绪周期": "启动/高潮",
            "板块地位": "龙头",
            "预期成功率": "70%"
        },
        "五日线首阴": {
            "趋势": "MA5>MA10>MA20",
            "连阳": "3-5 连阳",
            "今日回调": "-1% 至 -5%",
            "缩量": "<0.7 倍",
            "触及": "5 日线",
            "RSI": "<50",
            "超大单流出": ">-1000 万",
            "预期成功率": "75%"
        }
    }
    
    return criteria

# ==================== v2.0 评分系统 ====================

def calculate_score_v2(stock_data):
    """v2.0 评分系统"""
    
    score = 0
    details = []
    
    # 资金面 (35 分)
    super_large = stock_data.get("super_large", 0)
    large = stock_data.get("large", 0)
    
    if super_large > 5000:
        score += 15
        details.append("✅ 超大单>5000 万 (+15)")
    elif super_large > 3000:
        score += 12
        details.append("✅ 超大单>3000 万 (+12)")
    elif super_large > 1000:
        score += 8
        details.append("✅ 超大单>1000 万 (+8)")
    elif super_large > 0:
        score += 3
        details.append("🟡 超大单流入 (+3)")
    
    if large > 2000:
        score += 10
        details.append("✅ 大单>2000 万 (+10)")
    elif large > 1000:
        score += 8
        details.append("✅ 大单>1000 万 (+8)")
    
    # 技术面 (25 分)
    ma_pattern = stock_data.get("ma_pattern", "")
    if ma_pattern == "多头":
        score += 25
        details.append("✅ 均线多头 (+25)")
    elif ma_pattern == "纠缠":
        score += 10
        details.append("🟡 均线纠缠 (+10)")
    
    # 分时图 (20 分)
    intraday_score = stock_data.get("intraday_score", 0)
    score += min(intraday_score, 20)
    details.append(f"🟡 分时图 +{min(intraday_score, 20)}")
    
    # 板块 (15 分)
    sector_rank = stock_data.get("sector_rank", 10)
    if sector_rank <= 3:
        score += 15
        details.append("✅ 板块前 3 (+15)")
    elif sector_rank <= 10:
        score += 8
        details.append("🟡 板块前 10 (+8)")
    
    # 情绪周期 (5 分)
    emotion = stock_data.get("emotion", "震荡")
    if emotion in ["冰点", "启动"]:
        score += 5
        details.append("✅ 情绪冰点/启动 (+5)")
    elif emotion == "强势":
        score += 3
        details.append("🟡 情绪强势 (+3)")
    
    return {
        "total": score,
        "max": 100,
        "details": details,
        "rating": get_rating(score)
    }

def get_rating(score):
    """获取评级"""
    if score >= 85:
        return "🟢🟢🟢 极强"
    elif score >= 70:
        return "🟢🟢 强势"
    elif score >= 55:
        return "🟡 中性"
    else:
        return "🔴 弱势"

# ==================== v2.0 止损策略 ====================

def calculate_stop_loss_v2(entry_price, current_price, high_price, ma5):
    """v2.0 止损策略"""
    
    stop_losses = {
        "固定止损": round(entry_price * 0.95, 2),
        "技术止损": {
            "破 5 日线": round(ma5 * 0.97, 2),
            "破分时均线": round(current_price * 0.98, 2),
        },
        "追踪止损": {
            "盈利>10%": round(high_price * 0.95, 2),
            "盈利>20%": round(high_price * 0.90, 2),
        }
    }
    
    return stop_losses

# ==================== v2.0 仓位管理 ====================

def calculate_position_v2(emotion, pattern, profit_loss):
    """v2.0 仓位管理"""
    
    # 基础仓位
    if pattern == "首板":
        base = 25
    elif pattern == "连板":
        base = 40
    elif pattern == "五日线首阴":
        base = 35
    else:
        base = 20
    
    # 情绪调整
    if emotion == "冰点":
        emotion_adj = 0.8
    elif emotion == "启动":
        emotion_adj = 1.0
    elif emotion == "强势":
        emotion_adj = 1.2
    elif emotion == "高潮":
        emotion_adj = 0.8
    else:
        emotion_adj = 0.6
    
    # 盈亏调整
    if profit_loss > 10:
        pl_adj = 1.1
    elif profit_loss < -5:
        pl_adj = 0.8
    else:
        pl_adj = 1.0
    
    position = base * emotion_adj * pl_adj
    position = min(max(position, 0), 50)  # 0-50%
    
    return round(position, 0)

# ==================== v2.0 预警系统 ====================

def check_warnings_v2(stock_data):
    """v2.0 预警系统"""
    
    warnings = []
    change = stock_data.get("change", 0)
    super_large = stock_data.get("super_large", 0)
    
    # 一级预警
    if change <= -8:
        warnings.append({
            "level": "🔴🔴🔴 一级预警",
            "type": "大幅下跌",
            "message": f"跌超 -8% ({change}%)",
            "action": "立即止损"
        })
    
    if super_large < -5000:
        warnings.append({
            "level": "🔴🔴🔴 一级预警",
            "type": "超大单流出",
            "message": f"超大单流出 {super_large}万",
            "action": "立即卖出"
        })
    
    # 二级预警
    if -8 < change <= -5:
        warnings.append({
            "level": "🔴🔴 二级预警",
            "type": "下跌",
            "message": f"跌超 -5% ({change}%)",
            "action": "反抽卖出"
        })
    
    # 机会预警
    if change >= 9.5:
        warnings.append({
            "level": "🟢 机会预警",
            "type": "涨停",
            "message": f"已涨停 ({change}%)",
            "action": "持有观察"
        })
    elif change >= 5:
        warnings.append({
            "level": "🟢 机会预警",
            "type": "大涨",
            "message": f"大涨超 5% ({change}%)",
            "action": "持有"
        })
    
    return warnings

# ==================== 主程序 ====================

def main():
    """主程序"""
    print("=" * 80)
    print(f"🤖 智能股票分析系统 {VERSION}")
    print(f"目标收益：{TARGET_RETURN}")
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 获取当前模式
    mode = get_current_mode()
    print(f"\n📊 分析模式：{mode['mode']}")
    print(f"📝 分析逻辑：{mode['logic']}")
    
    # 获取选股公式
    print(f"\n📋 v2.0 选股公式:")
    criteria = select_stocks_v2()
    for name, rules in criteria.items():
        print(f"\n  {name}:")
        for rule, value in rules.items():
            print(f"    {rule}: {value}")
    
    print(f"\n{'='*80}")
    print("系统 v2.0 就绪！")
    print(f"{'='*80}")

    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    main()
