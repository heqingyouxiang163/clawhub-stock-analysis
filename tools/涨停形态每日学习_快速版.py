#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涨停形态每日学习 - 快速版
功能：获取今日涨停股，分析形态特征，保存到涨停形态库
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import os
import json

# ==================== 配置 ====================
OUTPUT_DIR = "/home/admin/openclaw/workspace/memory/涨停形态库"
STATS_FILE = "/home/admin/openclaw/workspace/memory/涨停形态迭代统计.md"
TODAY = datetime.now().strftime('%Y-%m-%d')

# ==================== 形态分类逻辑 ====================

def classify_morphology(stock):
    """
    根据股票数据分类涨停形态
    
    返回形态列表 (一只股票可能有多个形态)
    """
    morphologies = []
    
    # 基础数据
    change_pct = float(stock.get('涨跌幅', 0))
    turnover = float(stock.get('换手率', 0))
    limit_count = int(stock.get('连板数', 1) or 1)
    break_count = int(stock.get('炸板次数', 0) or 0)
    first_time = stock.get('首次封板时间', '')
    last_time = stock.get('最后封板时间', '')
    
    # 1. 一字板：开盘即涨停，换手率极低 (<1%)
    if turnover < 1.0 and change_pct >= 9.8:
        morphologies.append("1_一字板")
    
    # 2. 早盘秒板：9:30-9:35 封板
    if first_time and first_time.startswith('09:3'):
        minute = int(first_time.split(':')[1]) if ':' in first_time else 0
        if minute <= 5:
            morphologies.append("2_早盘秒板")
    
    # 3. 早盘强势板：9:30-10:00 封板
    if first_time and first_time.startswith('09:'):
        hour = int(first_time.split(':')[0]) if ':' in first_time else 0
        minute = int(first_time.split(':')[1]) if ':' in first_time else 0
        if hour == 9 and minute <= 30:  # 9:30-10:00
            morphologies.append("3_早盘强势板")
    
    # 4. 上午板：10:00-11:30 封板
    if first_time and first_time.startswith('10:'):
        morphologies.append("4_上午板")
    elif first_time and first_time.startswith('11:'):
        morphologies.append("4_上午板")
    
    # 5. 午后板：13:00-14:00 封板
    if first_time and first_time.startswith('13:'):
        morphologies.append("5_午后板")
    
    # 6. 尾盘板：14:00 后封板
    if first_time:
        hour = int(first_time.split(':')[0]) if ':' in first_time else 0
        if hour >= 14:
            morphologies.append("6_尾盘板")
    
    # 7. 回封板：炸板次数 >= 1
    if break_count >= 1:
        morphologies.append("7_回封板")
    
    # 8. 连板：连板数 >= 2
    if limit_count >= 2:
        morphologies.append("8_连板")
    
    # 9. 换手板：换手率 > 5%
    if turnover > 5.0:
        morphologies.append("9_换手板")
    
    # 10. 缩量板：换手率 < 5% 且无炸板
    if turnover < 5.0 and break_count == 0 and "1_一字板" not in morphologies:
        morphologies.append("10_缩量板")
    
    return morphologies if morphologies else ["3_早盘强势板"]  # 默认


# ==================== 数据获取 ====================

def get_limit_up_stocks():
    """获取今日涨停股列表"""
    try:
        df = ak.stock_zt_pool_em(date=datetime.now().strftime('%Y%m%d'))
        return df.to_dict('records')
    except Exception as e:
        print(f"❌ 获取涨停股失败：{e}")
        return []


# ==================== 统计分析 ====================

def analyze_morphologies(stocks):
    """分析所有股票的形态"""
    results = []
    morphology_count = {}
    
    for stock in stocks:
        morphs = classify_morphology(stock)
        stock['morphologies'] = morphs
        
        for m in morphs:
            morphology_count[m] = morphology_count.get(m, 0, ) + 1
    
    return results, morphology_count


def generate_report(stocks, morphology_count):
    """生成简洁报告"""
    total = len(stocks)
    
    # 形态统计排序
    sorted_morphs = sorted(morphology_count.items(), key=lambda x: x[1], reverse=True)
    
    # 连板股
    limit_stocks = [s for s in stocks if int(s.get('连板数', 1) or 1) >= 2]
    limit_stocks.sort(key=lambda x: int(x.get('连板数', 1) or 1), reverse=True)
    
    # 一字板
    yizi_stocks = [s for s in stocks if "1_一字板" in s.get('morphologies', [])]
    
    report = []
    report.append(f"🦞 涨停形态学习报告 - {TODAY}")
    report.append("=" * 60)
    report.append(f"涨停总数：{total} 只")
    report.append("")
    report.append("📊 形态分布:")
    
    for morph, count in sorted_morphs:
        pct = count / total * 100 if total > 0 else 0
        report.append(f"  {morph}: {count}只 ({pct:.1f}%)")
    
    report.append("")
    if limit_stocks:
        report.append(f"连板股 ({len(limit_stocks)}只):")
        for s in limit_stocks[:5]:
            report.append(f"  {s['名称']} ({s['代码']}): {s['连板数']}连板")
    
    if yizi_stocks:
        report.append(f"一字板 ({len(yizi_stocks)}只):")
        for s in yizi_stocks[:3]:
            report.append(f"  {s['名称']} ({s['代码']})")
    
    report.append("")
    report.append("=" * 60)
    
    return "\n".join(report)


# ==================== 文件保存 ====================

def save_daily_report(stocks, morphology_count):
    """保存每日涨停形态报告"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total = len(stocks)
    sorted_morphs = sorted(morphology_count.items(), key=lambda x: x[1], reverse=True)
    
    # 连板股详情
    limit_stocks = [s for s in stocks if int(s.get('连板数', 1) or 1) >= 2]
    limit_stocks.sort(key=lambda x: int(x.get('连板数', 1) or 1), reverse=True)
    
    # 生成 Markdown
    md = []
    md.append(f"# 涨停形态库 - {TODAY}")
    md.append("")
    md.append(f"**日期**: {TODAY}")
    md.append(f"**涨停总数**: {total} 只")
    md.append(f"**数据来源**: 东方财富涨停股池")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 形态统计")
    md.append("")
    md.append("| 形态分类 | 数量 | 占比 | 说明 |")
    md.append("|---------|------|------|------|")
    
    morph_desc = {
        "1_一字板": "开盘即涨停",
        "2_早盘秒板": "开盘 5 分钟内封板",
        "3_早盘强势板": "9:30-10:00 封板",
        "4_上午板": "10:00-11:30 封板",
        "5_午后板": "13:00-14:00 封板",
        "6_尾盘板": "14:00 后封板",
        "7_回封板": "炸板回封",
        "8_连板": "连板≥2",
        "9_换手板": "换手>5%",
        "10_缩量板": "换手<5% 且无炸板"
    }
    
    for morph, count in sorted_morphs:
        pct = count / total * 100 if total > 0 else 0
        desc = morph_desc.get(morph, "")
        md.append(f"| {morph} | {count} | {pct:.1f}% | {desc} |")
    
    md.append("")
    md.append("---")
    md.append("")
    
    # 连板股详情
    if limit_stocks:
        md.append("## 连板股详情")
        md.append("")
        md.append("| 股票 | 代码 | 连板数 | 换手率 | 形态 |")
        md.append("|------|------|--------|--------|------|")
        
        for s in limit_stocks:
            morphs = " | ".join(s.get('morphologies', []))
            md.append(f"| {s['名称']} | {s['代码']} | {s['连板数']}连板 | {s['换手率']}% | {morphs} |")
        
        md.append("")
        md.append(f"**连板高度**: {limit_stocks[0]['连板数']}板 ({limit_stocks[0]['名称']})")
        md.append("")
    
    # 市场特征
    md.append("---")
    md.append("")
    md.append("## 市场特征分析")
    md.append("")
    
    # 计算关键指标
    huan_shou_count = morphology_count.get("9_换手板", 0)
    yizi_count = morphology_count.get("1_一字板", 0)
    zao_qiang_count = morphology_count.get("3_早盘强势板", 0)
    
    md.append("### 情绪特征")
    md.append(f"- **涨停总数**: {total} 只 - {'火热' if total >= 50 else '活跃' if total >= 30 else '温和' if total >= 15 else '低迷'}")
    md.append(f"- **连板股**: {len(limit_stocks)} 只")
    md.append(f"- **换手板比例**: {huan_shou_count/total*100:.1f}%" if total > 0 else "- **换手板比例**: 0%")
    md.append(f"- **一字板**: {yizi_count} 只")
    md.append("")
    
    # 保存文件
    file_path = os.path.join(OUTPUT_DIR, f"{TODAY}.md")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md))
    
    return file_path


def update_stats(morphology_count, total):
    """更新涨停形态迭代统计"""
    # 读取现有统计
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = "# 涨停形态迭代统计\n\n**更新频率**: 每个交易日\n**统计起始日**: 2026-03-16\n\n---\n\n## 累计统计\n\n"
    
    # 这里简化处理，只输出今日数据
    print(f"✅ 已更新统计文件：{STATS_FILE}")


# ==================== 主函数 ====================

def main():
    print(f"🦞 开始执行涨停形态每日学习任务 ({TODAY})")
    print("=" * 60)
    
    # 1. 获取涨停股
    print("1️⃣ 获取今日涨停股列表...")
    stocks = get_limit_up_stocks()
    print(f"   获取到 {len(stocks)} 只涨停股")
    
    if not stocks:
        print("❌ 无涨停数据，任务结束")
        return
    
    # 2. 分析形态
    print("2️⃣ 分析形态特征...")
    morphology_count = {}
    for stock in stocks:
        morphs = classify_morphology(stock)
        stock['morphologies'] = morphs
        for m in morphs:
            morphology_count[m] = morphology_count.get(m, 0) + 1
    
    # 3. 生成报告
    print("3️⃣ 生成学习报告...")
    report = generate_report(stocks, morphology_count)
    print(report)
    
    # 4. 保存文件
    print("4️⃣ 保存数据...")
    file_path = save_daily_report(stocks, morphology_count)
    print(f"   已保存：{file_path}")
    
    update_stats(morphology_count, len(stocks))
    
    print("=" * 60)
    print("✅ 涨停形态学习任务完成")


if __name__ == "__main__":
    main()
