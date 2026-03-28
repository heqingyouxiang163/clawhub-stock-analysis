#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短线盈利助手 v1.0 - 隔日超短线选股系统

功能:
1. 结合分时图形态 + 历史涨停形态库 + 每日学习知识
2. 综合评分系统 (技术面 + 资金面 + 情绪面 + 历史胜率)
3. 专注于隔日超短线盈利 (今天买，明天卖)
4. 推送高确定性股票 (≥80 分)

配置:
- 推送频率：每 5 分钟
- 推送时段：9:35-10:35 (黄金 1 小时)
- 推送阈值：≥80 分 (高确定性)
- 持仓时间：隔日出货
"""

import sys
import os
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
    'min_score': 80,             # 最低推送分数 (隔日超短线要求更高)
    'max_push_stocks': 3,        # 每次最多推 3 只 (少而精)
}

# 输出目录
OUTPUT_DIR = "/home/admin/openclaw/workspace/temp/短线盈利助手"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 错误日志配置
ERROR_LOG_DIR = "/home/admin/openclaw/workspace/temp/短线盈利助手/logs"
os.makedirs(ERROR_LOG_DIR, exist_ok=True)
ERROR_LOG_FILE = os.path.join(ERROR_LOG_DIR, f"错误日志_{datetime.now().strftime('%Y%m%d')}.md")

# 历史形态库路径
MORPHOLOGY_DIR = "/home/admin/openclaw/workspace/memory/涨停形态库"
MORPHOLOGY_FILE = "/home/admin/openclaw/workspace/memory/涨停形态库/形态胜率统计.json"

# 评分权重 (隔日超短线专用)
SCORE_WEIGHTS = {
    'intraday_pattern': 30,   # 分时图形态 30 分
    'limit_up_morphology': 25, # 历史涨停形态 25 分
    'volume_money': 20,       # 量能资金 20 分
    'market_sentiment': 15,   # 市场情绪 15 分
    'next_day_premium': 10,   # 历史次日溢价 10 分
}


# ==================== 历史形态库加载 ====================

def load_morphology_stats():
    """加载历史形态胜率统计"""
    if not os.path.exists(MORPHOLOGY_FILE):
        return {}
    
    try:
        with open(MORPHOLOGY_FILE, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        return stats
    except:
        return {}


def load_recent_limit_up(days: int = 5) -> List[Dict]:
    """加载最近 N 天的涨停股数据"""
    limit_up_stocks = []
    
    if not os.path.exists(MORPHOLOGY_DIR):
        return limit_up_stocks
    
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        # 跳过周末
        if date.weekday() >= 5:
            continue
        
        file_path = os.path.join(MORPHOLOGY_DIR, f"{date_str}.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                stocks = parse_limit_up_stocks(content, date_str)
                limit_up_stocks.extend(stocks)
    
    return limit_up_stocks


def parse_limit_up_stocks(content: str, date: str) -> List[Dict]:
    """解析涨停股数据"""
    stocks = []
    lines = content.split('\n')
    
    for line in lines:
        if '|' in line and ('涨停' in line or '涨幅' in line):
            parts = line.split('|')
            if len(parts) >= 6:
                try:
                    stock = {
                        'code': parts[2].strip(),
                        'name': parts[3].strip(),
                        'change_pct': float(parts[4].strip().replace('%', '')),
                        'morphology': parts[6].strip() if len(parts) > 6 else '',
                        'date': date
                    }
                    stocks.append(stock)
                except:
                    pass
    
    return stocks


# ==================== 知识学习成果加载 ====================

def load_learning_knowledge() -> Dict:
    """加载每日学习成果"""
    knowledge = {
        'hot_concepts': [],      # 热门概念
        'strong_sectors': [],    # 强势板块
        'success_patterns': [],  # 成功形态
        'fail_patterns': []      # 失败形态
    }
    
    learning_dir = "/home/admin/openclaw/workspace/memory/自我进化"
    
    if not os.path.exists(learning_dir):
        return knowledge
    
    # 读取最近的学习文件
    try:
        files = sorted(os.listdir(learning_dir), reverse=True)[:5]
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(learning_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 简单提取关键词
                    if '热门' in content or '概念' in content:
                        knowledge['hot_concepts'].append(file)
                    if '形态' in content or '涨停' in content:
                        knowledge['success_patterns'].append(file)
    except:
        pass
    
    return knowledge


# ==================== 综合评分系统 ====================

def score_intraday_pattern(stock: Dict) -> tuple:
    """
    分时图形态评分 (0-30 分)
    
    隔日超短线关注点:
    - 股价在分时均线上方 (易於次日溢价)
    - 涨幅适中 (3-7%，有上涨空间)
    - 量价配合健康
    """
    score = 0
    details = []
    
    current = stock.get('current', 0)
    open_price = stock.get('open', current)
    high = stock.get('high', current)
    low = stock.get('low', current)
    prev_close = stock.get('prev_close', open_price)
    change_pct = stock.get('change_pct', 0)
    
    # 估算分时均线
    estimated_vwap = (open_price + high + low + current) / 4
    
    # 1. 股价在分时均线上方 (15 分)
    if current > estimated_vwap * 1.02:
        score += 15
        details.append(f"✅ 股价远高于均线")
    elif current > estimated_vwap * 1.01:
        score += 12
        details.append(f"✅ 股价在均线上方")
    elif current > estimated_vwap:
        score += 8
        details.append(f"🟡 股价略高于均线")
    else:
        details.append(f"❌ 股价跌破均线")
    
    # 2. 涨幅适中 (10 分) - 隔日超短线 prefer 3-7%
    if 3 <= change_pct <= 7:
        score += 10
        details.append(f"✅ 涨幅适中 ({change_pct:.1f}%, 有空间)")
    elif 2 <= change_pct < 3 or 7 < change_pct <= 9:
        score += 6
        details.append(f"🟡 涨幅可接受 ({change_pct:.1f}%)")
    else:
        details.append(f"❌ 涨幅不理想 ({change_pct:.1f}%)")
    
    # 3. 量价配合 (5 分)
    amount = stock.get('amount', 0)
    if amount > 500000000 and change_pct > 3:  # 放量上涨
        score += 5
        details.append(f"✅ 量价配合良好")
    else:
        details.append(f"🟡 量价配合一般")
    
    return min(score, 30), details


def score_limit_up_morphology(stock: Dict, morphology_stats: Dict, recent_limit_up: List) -> tuple:
    """
    历史涨停形态评分 (0-25 分)
    
    基于历史形态库:
    - 该股是否出现过涨停
    - 涨停形态的胜率
    - 近期涨停频率
    """
    score = 0
    details = []
    code = stock.get('code', '')
    
    # 1. 检查该股是否在历史涨停库中
    stock_in_history = [s for s in recent_limit_up if s['code'] == code]
    
    if stock_in_history:
        score += 10
        details.append(f"✅ 近期出现过涨停 (股性活跃)")
        
        # 2. 检查涨停形态胜率
        for s in stock_in_history:
            morph = s.get('morphology', '')
            if morph in morphology_stats:
                stats = morphology_stats[morph]
                win_rate = stats.get('win_rate', 0)
                if win_rate > 70:
                    score += 10
                    details.append(f"✅ {morph}胜率高 ({win_rate:.0f}%)")
                elif win_rate > 50:
                    score += 6
                    details.append(f"🟡 {morph}胜率中等 ({win_rate:.0f}%)")
                else:
                    details.append(f"⚠️ {morph}胜率较低")
                break
    else:
        details.append(f"❌ 近期无涨停记录")
    
    # 3. 连板加分 (5 分)
    if len(stock_in_history) >= 2:
        score += 5
        details.append(f"✅ 有连板记录 (妖股潜质)")
    
    return min(score, 25), details


def score_volume_money(stock: Dict) -> tuple:
    """
    量能资金评分 (0-20 分)
    
    隔日超短线关注:
    - 成交额>5 亿 (流动性好)
    - 换手率 5-15% (充分换手)
    - 量比>1.5 (放量)
    """
    score = 0
    details = []
    
    turnover = stock.get('turnover', 0)
    amount = stock.get('amount', 0) / 100000000  # 转亿
    
    # 1. 成交额评分 (10 分)
    if amount >= 10:
        score += 10
        details.append(f"✅ 成交额大 (¥{amount:.1f}亿，流动性好)")
    elif amount >= 5:
        score += 8
        details.append(f"✅ 成交额适中 (¥{amount:.1f}亿)")
    elif amount >= 2:
        score += 5
        details.append(f"🟡 成交额一般 (¥{amount:.1f}亿)")
    else:
        details.append(f"❌ 成交额偏小 (¥{amount:.1f}亿)")
    
    # 2. 换手率评分 (10 分) - 隔日超短线 prefer 5-15%
    if 5 <= turnover <= 15:
        score += 10
        details.append(f"✅ 换手充分 ({turnover:.1f}%)")
    elif 3 <= turnover < 5 or 15 < turnover <= 20:
        score += 6
        details.append(f"🟡 换手可接受 ({turnover:.1f}%)")
    elif turnover > 0:
        score += 3
        details.append(f"⚠️ 换手不足 ({turnover:.1f}%)")
    else:
        details.append(f"❌ 无换手数据")
    
    return min(score, 20), details


def score_market_sentiment(stock: Dict, knowledge: Dict) -> tuple:
    """
    市场情绪评分 (0-15 分)
    
    基于每日学习成果:
    - 是否热门概念
    - 是否强势板块
    - 市场整体情绪
    """
    score = 0
    details = []
    
    name = stock.get('name', '')
    
    # 1. 热门概念加分 (8 分)
    # TODO: 需要集成概念识别
    # 简化：名称中包含热门关键词
    hot_keywords = ['科技', '芯片', 'AI', '新能源', '医药']
    for keyword in hot_keywords:
        if keyword in name:
            score += 8
            details.append(f"✅ 热门概念 ({keyword})")
            break
    
    # 2. 板块效应 (7 分)
    # TODO: 需要板块数据
    details.append(f"🟡 板块效应一般")
    
    return min(score, 15), details


def score_next_day_premium(stock: Dict, morphology_stats: Dict) -> tuple:
    """
    历史次日溢价评分 (0-10 分)
    
    基于历史数据:
    - 该股历史次日表现
    - 类似形态的次日溢价
    """
    score = 0
    details = []
    
    # TODO: 需要历史次日数据
    # 简化：根据形态胜率推断
    details.append(f"🟡 次日溢价数据不足")
    
    return score, details


def calculate_total_score(stock: Dict, morphology_stats: Dict, recent_limit_up: List, knowledge: Dict) -> tuple:
    """计算总分 (0-100 分)"""
    
    # 1. 分时图形态 (30 分)
    intraday_score, intraday_details = score_intraday_pattern(stock)
    
    # 2. 历史涨停形态 (25 分)
    morphology_score, morphology_details = score_limit_up_morphology(
        stock, morphology_stats, recent_limit_up
    )
    
    # 3. 量能资金 (20 分)
    volume_score, volume_details = score_volume_money(stock)
    
    # 4. 市场情绪 (15 分)
    sentiment_score, sentiment_details = score_market_sentiment(stock, knowledge)
    
    # 5. 历史次日溢价 (10 分)
    premium_score, premium_details = score_next_day_premium(stock, morphology_stats)
    
    # 总分
    total = intraday_score + morphology_score + volume_score + sentiment_score + premium_score
    
    details = {
        '分时图': intraday_score,
        '历史形态': morphology_score,
        '量能资金': volume_score,
        '市场情绪': sentiment_score,
        '次日溢价': premium_score,
        '总分': total,
        '分时图细节': intraday_details,
        '历史形态细节': morphology_details,
        '量能细节': volume_details,
        '情绪细节': sentiment_details,
        '溢价细节': premium_details
    }
    
    return total, details


# ==================== 选股逻辑 (隔日超短线专用) ====================

def select_stocks_for_next_day(stocks: List[Dict], morphology_stats: Dict, 
                                recent_limit_up: List, knowledge: Dict,
                                min_score: int = 80, max_count: int = 3) -> List[Dict]:
    """
    筛选隔日超短线股票
    
    核心逻辑:
    1. 总分≥80 分 (高确定性)
    2. 涨幅 3-7% (有上涨空间，避免追高)
    3. 换手率 5-15% (充分换手，易於次日溢价)
    4. 成交额>3 亿 (流动性好，易於出货)
    5. 近期有涨停记录 (股性活跃)
    6. 不属于失败形态
    """
    qualified = []
    
    for stock in stocks:
        # 基础过滤
        change_pct = stock.get('change_pct', 0)
        turnover = stock.get('turnover', 0)
        amount = stock.get('amount', 0)
        
        # 过滤条件 (隔日超短线专用)
        if change_pct < 3 or change_pct >= 9:  # 排除涨幅过小或接近涨停
            continue
        if turnover < 3 or turnover > 20:  # 排除换手不足或过高
            continue
        if amount < 300000000:  # 排除成交额<3 亿
            continue
        
        # 计算综合评分
        score, details = calculate_total_score(
            stock, morphology_stats, recent_limit_up, knowledge
        )
        
        if score >= min_score:
            qualified.append({
                **stock,
                'score': score,
                'score_details': details,
                'strategy': '隔日超短线',
                'target_profit': '3-8%',  # 目标盈利
                'stop_loss': '-3%',        # 止损位
                'sell_time': '次日 9:30-10:00'  # 出货时间
            })
    
    # 按分数排序，取前 N 只
    qualified.sort(key=lambda x: x['score'], reverse=True)
    return qualified[:max_count]


# ==================== 推送生成 ====================

def generate_push_report(selected: List[Dict], push_time: datetime) -> str:
    """生成推送报告 (隔日超短线专用)"""
    report = []
    report.append("=" * 75)
    report.append(f"🦞 短线盈利助手 - 隔日超短线推荐")
    report.append(f"时间：{push_time.strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 75)
    report.append("")
    
    if not selected:
        report.append("⚠️ 本次无符合条件的高确定性股票")
        report.append("")
        report.append("说明:")
        report.append("  - 市场整体强度不足")
        report.append("  - 或未达到推送阈值 (≥80 分)")
        report.append("  - 保持耐心，等待更好机会")
        report.append("  - 超短线讲究：宁可空仓，不做弱势")
    else:
        report.append(f"✅ 推荐 {len(selected)} 只隔日超短线股票")
        report.append("")
        report.append("🎯 策略说明:")
        report.append("  - 今天买入，明天出货")
        report.append("  - 目标盈利：3-8%")
        report.append("  - 止损位：-3%")
        report.append("  - 出货时间：次日 9:30-10:00")
        report.append("")
        report.append("📊 选股标准:")
        report.append("  - 综合评分≥80 分")
        report.append("  - 分时图形态强势")
        report.append("  - 历史涨停形态胜率高")
        report.append("  - 量能资金充足")
        report.append("  - 市场情绪向好")
        report.append("")
        report.append("-" * 75)
        report.append("")
        
        for i, stock in enumerate(selected, 1):
            code = stock['code']
            name = stock['name']
            current = stock.get('current', 0)
            change_pct = stock.get('change_pct', 0)
            turnover = stock.get('turnover', 0)
            amount = stock.get('amount', 0) / 100000000
            score = stock['score']
            
            report.append(f"{i}. {code} {name} (总分：{score}分)")
            report.append(f"   现价：¥{current:.2f}  涨幅：+{change_pct:.1f}%")
            report.append(f"   换手：{turnover:.1f}%  成交额：¥{amount:.2f}亿")
            report.append(f"   策略：今天买入，明天出货")
            report.append(f"   目标：+3-8%  止损：-3%")
            report.append(f"   出货：次日 9:30-10:00")
            report.append(f"   评分详情:")
            
            score_details = stock.get('score_details', {})
            report.append(f"     - 分时图：{score_details.get('分时图', 0)}/30")
            report.append(f"     - 历史形态：{score_details.get('历史形态', 0)}/25")
            report.append(f"     - 量能资金：{score_details.get('量能资金', 0)}/20")
            report.append(f"     - 市场情绪：{score_details.get('市场情绪', 0)}/15")
            report.append(f"     - 次日溢价：{score_details.get('次日溢价', 0)}/10")
            
            # 操作建议
            if score >= 90:
                action = "🟢🟢🟢 重点推荐 (高确定性)"
                position = "建议仓位：30-40%"
            elif score >= 85:
                action = "🟢🟢 积极买入"
                position = "建议仓位：20-30%"
            else:
                action = "🟢 值得关注"
                position = "建议仓位：10-20%"
            
            report.append(f"   评级：{action}")
            report.append(f"   {position}")
            report.append("")
            report.append("-" * 75)
            report.append("")
    
    # 风险提示
    report.append("⚠️ 重要风险提示:")
    report.append("  - 超短线风险极高，请严格控制仓位")
    report.append("  - 本推荐仅供参考，不构成投资建议")
    report.append("  - 必须设置止损，严格执行")
    report.append("  - 建议总仓≤60%，单只≤30%")
    report.append("  - 次日必须出货，不恋战")
    report.append("")
    report.append("📚 盈利模式:")
    report.append("  - 胜率目标：60%+")
    report.append("  - 盈亏比：1:2 (亏 3% 赚 6%)")
    report.append("  - 月目标：20-30%")
    report.append("")
    report.append("=" * 75)
    
    return "\n".join(report)


# ==================== 推送执行 ====================

def send_push_notification(report: str, push_time: datetime):
    """发送推送通知"""
    filename = f"短线盈利_{push_time.strftime('%Y%m%d_%H%M')}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 推送已保存：{filepath}")
    
    # TODO: 集成消息发送
    # send_message(report)


def run_push_cycle(force: bool = False):
    """执行推送周期"""
    start_time = datetime.now()
    error = None
    stock_count = 0
    selected_count = 0
    
    try:
        print("=" * 75)
        print("🦞 短线盈利助手 v1.0 - 隔日超短线选股系统")
        print("=" * 75)
        print()
        
        # 获取当前时间
        now = datetime.now()
        
        # 加载历史数据
        print("📚 加载历史知识...")
        morphology_stats = load_morphology_stats()
        recent_limit_up = load_recent_limit_up(days=5)
        knowledge = load_learning_knowledge()
        print(f"✅ 加载{len(recent_limit_up)}只历史涨停股，{len(morphology_stats)}种形态")
        print()
        
        # 获取全市场数据
        print("📊 扫描全市场...")
        stocks = get_full_market_scan(use_cache=False)
        stock_count = len(stocks)
        print(f"✅ 获取{len(stocks)}只股票数据")
        print()
        
        # 筛选股票
        print("🔍 筛选隔日超短线股票...")
        selected = select_stocks_for_next_day(
            stocks,
            morphology_stats,
            recent_limit_up,
            knowledge,
            min_score=PUSH_CONFIG['min_score'],
            max_count=PUSH_CONFIG['max_push_stocks']
        )
        selected_count = len(selected)
        print(f"✅ 筛选出{len(selected)}只")
        print()
        
        # 生成报告
        report = generate_push_report(selected, now)
        
        # 打印报告
        print(report)
        
        # 发送推送
        send_push_notification(report, now)
        
        # 保存统计
        save_push_stats(selected, now)
        
    except Exception as e:
        error = e
        import traceback
        error_trace = traceback.format_exc()
        
        print(f"❌ 运行出错：{str(e)}")
        
        # 记录错误
        log_error(
            error_type=type(e).__name__,
            error_msg=str(e),
            error_trace=error_trace,
            context={
                'force': force,
                'time': now.strftime('%Y-%m-%d %H:%M:%S'),
                'stocks_scanned': stock_count
            }
        )
    
    finally:
        end_time = datetime.now()
        
        # 记录运行统计
        log_run_stats(start_time, end_time, stock_count, selected_count, error)
        
        # 发送执行通知
        send_execution_notification(now, selected, error)
        
        # 显示运行时间
        duration = (end_time - start_time).total_seconds()
        print(f"\n⏱️ 运行时间：{duration:.1f}秒")
        
        if error:
            print(f"❌ 运行失败，请查看错误日志：{ERROR_LOG_FILE}")
        else:
            print(f"✅ 运行完成")


def send_execution_notification(push_time: datetime, selected: List, error: Exception = None):
    """发送执行完成通知"""
    notification = f"""
🦞 **短线盈利助手执行通知**

**执行时间**: {push_time.strftime('%Y-%m-%d %H:%M')}
**推荐股票**: {len(selected)}只
"""
    
    if selected:
        notification += "\n**推荐列表**:\n"
        for stock in selected:
            code = stock.get('code', '')
            name = stock.get('name', '')
            score = stock.get('score', 0)
            change_pct = stock.get('change_pct', 0)
            notification += f"- {code} {name} ({score}分，+{change_pct:.1f}%)\n"
    else:
        notification += "\n**说明**: 本次无符合条件的高确定性股票\n"
        notification += "\n💡 超短线讲究：宁可空仓，不做弱势\n"
    
    if error:
        notification += f"\n⚠️ **运行错误**: {type(error).__name__}\n"
        notification += f"请查看错误日志：`temp/短线盈利助手/logs/错误日志_*.md`\n"
    else:
        notification += "\n✅ **运行状态**: 正常\n"
    
    notification += "\n⏱️ 下次执行：5 分钟后"
    notification += "\n📊 查看日志：`temp/短线盈利助手/`"
    notification += "\n\n---\n*小艺·炒股龙虾 v18.0 自动通知*"
    
    # 保存通知
    notification_file = os.path.join(OUTPUT_DIR, f"执行通知_{push_time.strftime('%Y%m%d_%H%M')}.md")
    with open(notification_file, 'w', encoding='utf-8') as f:
        f.write(notification)
    
    print(f"\n📬 执行通知已生成：{notification_file}")
    
    # TODO: 集成消息发送
    # send_message(notification)


def save_push_stats(selected: List, push_time: datetime):
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


# ==================== 错误日志记录 ====================

def log_error(error_type: str, error_msg: str, error_trace: str = None, context: Dict = None):
    """记录运行错误"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_content = f"""
---

## ❌ 错误记录 - {timestamp}

**错误类型**: {error_type}

**错误信息**: 
```
{error_msg}
```

**堆栈跟踪**:
```
{error_trace if error_trace else '无'}
```

**上下文信息**:
```json
{json.dumps(context, ensure_ascii=False, indent=2) if context else '无'}
```

---
"""
    
    # 追加到日志文件
    with open(ERROR_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_content)
    
    print(f"⚠️ 错误已记录：{ERROR_LOG_FILE}")


def log_run_stats(start_time: datetime, end_time: datetime, stock_count: int, selected_count: int, error: Exception = None):
    """记录运行统计"""
    duration = (end_time - start_time).total_seconds()
    
    stats = {
        'timestamp': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': duration,
        'stocks_scanned': stock_count,
        'stocks_selected': selected_count,
        'has_error': error is not None,
        'error_type': type(error).__name__ if error else None
    }
    
    # 保存到运行日志
    run_log_file = os.path.join(ERROR_LOG_DIR, f"运行统计_{datetime.now().strftime('%Y%m%d')}.json")
    
    if os.path.exists(run_log_file):
        with open(run_log_file, 'r', encoding='utf-8') as f:
            runs = json.load(f)
    else:
        runs = []
    
    runs.append(stats)
    
    with open(run_log_file, 'w', encoding='utf-8') as f:
        json.dump(runs, f, ensure_ascii=False, indent=2)


def generate_daily_report():
    """生成每日运行报告"""
    today = datetime.now().strftime('%Y%m%d')
    run_log_file = os.path.join(ERROR_LOG_DIR, f"运行统计_{today}.json")
    error_log_file = os.path.join(ERROR_LOG_DIR, f"错误日志_{today}.md")
    
    if not os.path.exists(run_log_file):
        return
    
    with open(run_log_file, 'r', encoding='utf-8') as f:
        runs = json.load(f)
    
    total_runs = len(runs)
    error_runs = sum(1 for r in runs if r.get('has_error'))
    total_stocks = sum(r.get('stocks_selected', 0) for r in runs)
    avg_duration = sum(r.get('duration_seconds', 0) for r in runs) / total_runs if total_runs > 0 else 0
    
    report = f"""
# 📊 短线盈利助手 - 每日运行报告

**日期**: {datetime.now().strftime('%Y-%m-%d')}

## 运行统计

| 指标 | 数值 |
|------|------|
| 总运行次数 | {total_runs} |
| 成功次数 | {total_runs - error_runs} |
| 错误次数 | {error_runs} |
| 成功率 | {(total_runs - error_runs) / total_runs * 100:.1f}% |
| 推荐股票总数 | {total_stocks} |
| 平均运行时间 | {avg_duration:.1f}秒 |

## 错误统计

"""
    
    if os.path.exists(error_log_file):
        with open(error_log_file, 'r', encoding='utf-8') as f:
            error_count = f.read().count('## ❌ 错误记录')
        report += f"**错误总数**: {error_count}\n\n"
    else:
        report += "**无错误记录** ✅\n\n"
    
    report += f"""
## 优化建议

"""
    
    if error_runs > 0:
        report += f"- ⚠️ 发现{error_runs}次错误，请查看错误日志\n"
    if avg_duration > 120:
        report += f"- ⚠️ 平均运行时间{avg_duration:.1f}秒，建议优化性能\n"
    if total_stocks == 0:
        report += f"- ⚠️ 今日无推荐股票，市场强度不足或阈值过高\n"
    
    report += f"\n---\n*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    # 保存报告
    report_file = os.path.join(ERROR_LOG_DIR, f"每日报告_{today}.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📊 每日报告已生成：{report_file}")


# ==================== 主函数 ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'force':
        # 强制执行 (跳过时间检查)
        run_push_cycle(force=True)
    else:
        # 实际执行
        run_push_cycle()
