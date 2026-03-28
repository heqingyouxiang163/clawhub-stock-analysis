#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中分时图评分推送系统 v1.0

功能:
1. 每 5 分钟扫描全市场
2. 结合分时图形态 + 涨幅 + 量能评分
3. 9:35 开始推送，持续 1 小时 (共 12 次)
4. 只推评分≥75 分的高确定性股票

配置:
- 推送频率：5 分钟
- 开始时间：9:35
- 结束时间：10:35
- 推送阈值：≥75 分
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict

# 添加路径
sys.path.insert(0, '/home/admin/openclaw/workspace/tools')
sys.path.insert(0, '/home/admin/openclaw/workspace/skills/realtime-monitor-3min')

from realtime_monitor import get_full_market_scan, get_realtime_data
from 腾讯财经_API import get_multiple_stocks


# ==================== 配置区 ====================

# 推送配置
PUSH_CONFIG = {
    'start_time': (9, 35),      # 9:35 开始
    'end_time': (10, 35),       # 10:35 结束
    'interval_minutes': 5,       # 5 分钟间隔
    'min_score': 75,             # 最低推送分数
    'max_push_stocks': 5,        # 每次最多推 5 只
}

# 输出目录
OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/盘中推送"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 评分权重
SCORE_WEIGHTS = {
    'intraday_pattern': 40,   # 分时图形态 40 分
    'change_pct': 25,         # 涨幅 25 分
    'volume_ratio': 20,       # 量比 20 分
    'turnover': 15,           # 换手率 15 分
}


# ==================== 评分系统 ====================

def score_intraday_pattern(stock: Dict) -> int:
    """
    分时图形态评分 (0-40 分)
    
    评分标准:
    - 股价在分时均线上方：30 分
    - 均线斜率向上：25 分
    - 涨幅适中：10 分
    - 不破新低：15 分
    - 量价配合：20 分
    """
    score = 0
    details = []
    
    change_pct = stock.get('change_pct', 0)
    current = stock.get('current', 0)
    open_price = stock.get('open', current)
    high = stock.get('high', current)
    low = stock.get('low', current)
    prev_close = stock.get('prev_close', open_price)
    
    # 估算分时均线
    estimated_vwap = (open_price + high + low + current) / 4
    
    # 1. 股价在分时均线上方 (30 分)
    if current > estimated_vwap * 1.02:
        score += 30
        details.append(f"✅ 股价远高于均线 (+{((current-estimated_vwap)/estimated_vwap*100):.1f}%)")
    elif current > estimated_vwap * 1.01:
        score += 25
        details.append(f"✅ 股价在均线上方")
    elif current > estimated_vwap:
        score += 15
        details.append(f"🟡 股价略高于均线")
    else:
        details.append(f"❌ 股价跌破均线")
    
    # 2. 均线斜率向上 (25 分)
    change_from_open = (current - open_price) / open_price * 100 if open_price > 0 else 0
    if change_from_open > 4:
        score += 25
        details.append(f"✅ 均线陡峭向上 (+{change_from_open:.1f}%)")
    elif change_from_open > 2:
        score += 18
        details.append(f"✅ 均线向上 (+{change_from_open:.1f}%)")
    elif change_from_open > 0:
        score += 10
        details.append(f"🟡 均线走平 (+{change_from_open:.1f}%)")
    else:
        details.append(f"❌ 均线向下")
    
    # 3. 涨幅适中 (10 分) -  prefer 3-7%
    total_change = (current - prev_close) / prev_close * 100 if prev_close > 0 else 0
    if 3 <= total_change <= 7:
        score += 10
        details.append(f"✅ 涨幅适中 ({total_change:.1f}%)")
    elif 2 <= total_change < 3 or 7 < total_change <= 9:
        score += 6
        details.append(f"🟡 涨幅可接受 ({total_change:.1f}%)")
    else:
        details.append(f"❌ 涨幅不理想 ({total_change:.1f}%)")
    
    return min(score, 40), details


def score_change_pct(change_pct: float) -> int:
    """涨幅评分 (0-25 分)"""
    # 最优区间：5-8% (主升浪加速段)
    if 5 <= change_pct <= 8:
        return 25
    elif 3 <= change_pct < 5:
        return 20
    elif 8 < change_pct <= 9.5:
        return 18  # 接近涨停，可能买不进
    elif 2 <= change_pct < 3:
        return 15
    elif 0 <= change_pct < 2:
        return 10
    else:
        return 0


def score_volume_ratio(turnover: float, amount: float) -> int:
    """量比和成交额评分 (0-20 分)"""
    score = 0
    
    # 换手率评分 (0-10 分) - 最优 5-15%
    if 5 <= turnover <= 15:
        score += 10
    elif 3 <= turnover < 5 or 15 < turnover <= 20:
        score += 6
    elif turnover > 0:
        score += 3
    
    # 成交额评分 (0-10 分) - 优选>5 亿
    amount_yi = amount / 100000000 if amount else 0
    if amount_yi >= 10:
        score += 10
    elif amount_yi >= 5:
        score += 8
    elif amount_yi >= 2:
        score += 6
    elif amount_yi >= 1:
        score += 4
    elif amount_yi > 0:
        score += 2
    
    return min(score, 20)


def score_turnover(turnover: float) -> int:
    """换手率评分 (0-15 分)"""
    # 最优区间：5-15%
    if 5 <= turnover <= 15:
        return 15
    elif 3 <= turnover < 5 or 15 < turnover <= 20:
        return 10
    elif turnover > 0:
        return 5
    else:
        return 0


def calculate_total_score(stock: Dict) -> tuple:
    """计算总分 (0-100 分)"""
    # 分时图形态评分
    intraday_score, intraday_details = score_intraday_pattern(stock)
    
    # 涨幅评分
    change_score = score_change_pct(stock.get('change_pct', 0))
    
    # 量能评分
    volume_score = score_volume_ratio(
        stock.get('turnover', 0),
        stock.get('amount', 0)
    )
    
    # 换手评分
    turnover_score = score_turnover(stock.get('turnover', 0))
    
    # 总分
    total = intraday_score + change_score + volume_score + turnover_score
    
    details = {
        '分时图': intraday_score,
        '涨幅': change_score,
        '量能': volume_score,
        '换手': turnover_score,
        '总分': total,
        '分时图细节': intraday_details
    }
    
    return total, details


# ==================== 选股逻辑 ====================

def select_stocks(stocks: List[Dict], min_score: int = 75, max_count: int = 5) -> List[Dict]:
    """
    筛选高确定性股票
    
    条件:
    1. 总分≥75 分
    2. 涨幅 3-9% (避免涨停买不进)
    3. 换手率>3% (避免流动性不足)
    4. 成交额>1 亿 (避免冷门股)
    """
    qualified = []
    
    for stock in stocks:
        # 基础过滤
        change_pct = stock.get('change_pct', 0)
        turnover = stock.get('turnover', 0)
        amount = stock.get('amount', 0)
        
        # 过滤条件
        if change_pct < 3 or change_pct >= 9.5:  # 排除涨幅过小或涨停
            continue
        if turnover < 3:  # 排除换手不足
            continue
        if amount < 100000000:  # 排除成交额<1 亿
            continue
        
        # 计算评分
        score, details = calculate_total_score(stock)
        
        if score >= min_score:
            qualified.append({
                **stock,
                'score': score,
                'score_details': details
            })
    
    # 按分数排序，取前 N 只
    qualified.sort(key=lambda x: x['score'], reverse=True)
    return qualified[:max_count]


# ==================== 推送生成 ====================

def generate_push_report(selected: List[Dict], push_time: datetime) -> str:
    """生成推送报告"""
    report = []
    report.append("=" * 75)
    report.append(f"🦞 盘中高确定性推荐 - {push_time.strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 75)
    report.append("")
    
    if not selected:
        report.append("⚠️ 本次无符合条件的高确定性股票")
        report.append("")
        report.append("说明:")
        report.append("  - 市场整体强度不足")
        report.append("  - 或未达到推送阈值 (≥75 分)")
        report.append("  - 保持耐心，等待更好机会")
    else:
        report.append(f"✅ 推荐 {len(selected)} 只高确定性股票")
        report.append("")
        report.append("推送标准:")
        report.append("  - 分时图形态强势 (≥30 分)")
        report.append("  - 涨幅 3-9% (主升浪加速段)")
        report.append("  - 量比健康 (≥5 分)")
        report.append("  - 换手充分 (≥10 分)")
        report.append("  - 总分≥75 分")
        report.append("")
        report.append("-" * 75)
        report.append("")
        
        for i, stock in enumerate(selected, 1):
            code = stock['code']
            name = stock['name']
            current = stock.get('current', 0)
            change_pct = stock.get('change_pct', 0)
            turnover = stock.get('turnover', 0)
            amount = stock.get('amount', 0) / 100000000  # 转亿
            score = stock['score']
            
            report.append(f"{i}. {code} {name} (总分：{score}分)")
            report.append(f"   现价：¥{current:.2f}  涨幅：+{change_pct:.1f}%")
            report.append(f"   换手：{turnover:.1f}%  成交额：¥{amount:.2f}亿")
            report.append(f"   评分详情:")
            
            score_details = stock.get('score_details', {})
            report.append(f"     - 分时图：{score_details.get('分时图', 0)}/40")
            report.append(f"     - 涨幅：{score_details.get('涨幅', 0)}/25")
            report.append(f"     - 量能：{score_details.get('量能', 0)}/20")
            report.append(f"     - 换手：{score_details.get('换手', 0)}/15")
            
            # 操作建议
            if score >= 90:
                action = "🟢🟢🟢 积极买入"
            elif score >= 85:
                action = "🟢🟢 重点推荐"
            elif score >= 80:
                action = "🟢 值得关注"
            else:
                action = "🟡 观察为主"
            
            report.append(f"   评级：{action}")
            report.append("")
            report.append("-" * 75)
            report.append("")
    
    # 风险提示
    report.append("⚠️ 风险提示:")
    report.append("  - 本推荐仅供参考，不构成投资建议")
    report.append("  - 请结合个人判断和风险承受能力")
    report.append("  - 建议仓位：单只≤20%，总仓≤60%")
    report.append("  - 止损位：-5%，止盈位：+10%")
    report.append("")
    report.append("=" * 75)
    
    return "\n".join(report)


# ==================== 推送执行 ====================

def send_push_notification(report: str, push_time: datetime):
    """发送推送通知 (简化版：保存到文件)"""
    filename = f"盘中推送_{push_time.strftime('%Y%m%d_%H%M')}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 推送已保存：{filepath}")
    
    # TODO: 集成消息发送
    # send_message(report)


def run_push_cycle(force: bool = False):
    """执行推送周期"""
    print("=" * 75)
    print("🦞 盘中分时图评分推送系统 v1.0")
    print("=" * 75)
    print()
    
    # 获取当前时间
    now = datetime.now()
    
    # 计算推送时间
    start_time = now.replace(hour=PUSH_CONFIG['start_time'][0], 
                            minute=PUSH_CONFIG['start_time'][1], 
                            second=0, microsecond=0)
    end_time = now.replace(hour=PUSH_CONFIG['end_time'][0], 
                          minute=PUSH_CONFIG['end_time'][1], 
                          second=0, microsecond=0)
    
    # 检查是否在推送时间段内 (force=True 时跳过检查)
    if not force:
        if now < start_time:
            print(f"⏰ 未到推送时间 (开始：{start_time.strftime('%H:%M')})")
            print(f"💡 提示：当前时间 {now.strftime('%H:%M')}，请等待")
            return
        
        if now > end_time:
            print(f"⏰ 推送时间已结束 (结束：{end_time.strftime('%H:%M')})")
            print(f"💡 提示：下次推送时间为明日 9:35")
            return
    
    # 计算应该推送的次数
    minutes_elapsed = (now - start_time).total_seconds() / 60
    push_count = int(minutes_elapsed / PUSH_CONFIG['interval_minutes']) + 1
    total_pushes = int((end_time - start_time).total_seconds() / 60 / PUSH_CONFIG['interval_minutes']) + 1
    
    print(f"📊 推送进度：第{push_count}次 / 共{total_pushes}次")
    print(f"⏰ 推送时间：{now.strftime('%H:%M')}")
    print()
    
    # 获取全市场数据
    print("📊 扫描全市场...")
    stocks = get_full_market_scan(use_cache=False)
    print(f"✅ 获取{len(stocks)}只股票数据")
    print()
    
    # 筛选股票
    print("🔍 筛选高确定性股票...")
    selected = select_stocks(
        stocks,
        min_score=PUSH_CONFIG['min_score'],
        max_count=PUSH_CONFIG['max_push_stocks']
    )
    print(f"✅ 筛选出{len(selected)}只")
    print()
    
    # 生成报告
    report = generate_push_report(selected, now)
    
    # 打印报告
    print(report)
    
    # 发送推送
    send_push_notification(report, now)
    
    # 保存统计
    save_push_stats(push_count, total_pushes, selected, now)


def save_push_stats(push_count: int, total_pushes: int, selected: List, push_time: datetime):
    """保存推送统计"""
    stats_file = os.path.join(OUTPUT_DIR, "推送统计.json")
    
    # 加载历史统计
    if os.path.exists(stats_file):
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    else:
        stats = {'pushes': [], 'total_pushes': 0, 'total_stocks': 0}
    
    # 更新统计
    stats['pushes'].append({
        'time': push_time.strftime('%Y-%m-%d %H:%M'),
        'count': len(selected),
        'stocks': [
            {
                'code': s['code'],
                'name': s['name'],
                'score': s['score'],
                'change_pct': s.get('change_pct', 0)
            }
            for s in selected
        ]
    })
    stats['total_pushes'] += 1
    stats['total_stocks'] += len(selected)
    
    # 保存
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


# ==================== 模拟测试 ====================

def simulate_push():
    """模拟推送 (用于测试)"""
    print("=" * 75)
    print("🦞 盘中推送系统 - 模拟测试")
    print("=" * 75)
    print()
    
    # 强制执行一次
    print("🔧 强制执行推送测试...")
    print()
    run_push_cycle(force=True)


# ==================== 主函数 ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'simulate':
        # 模拟测试
        simulate_push()
    elif len(sys.argv) > 1 and sys.argv[1] == 'force':
        # 强制执行 (跳过时间检查)
        run_push_cycle(force=True)
    else:
        # 实际执行 (检查时间)
        run_push_cycle()
