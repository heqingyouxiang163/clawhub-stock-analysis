#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 批量获取涨停数据 + 强化学习

功能:
- 批量获取指定日期范围的涨停股数据
- 自动分析形态
- 统计胜率
- 强化学习优化

使用:
    python3 批量涨停数据获取.py 20260317 20260328
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path


def fetch_limit_up_stocks(date: str) -> list:
    """
    获取指定日期的涨停股列表
    
    Args:
        date: 日期 (如 20260321)
    
    Returns:
        涨停股列表
    """
    print(f'  获取 {date} 涨停股...')
    
    # 东方财富涨停池接口
    url = f'http://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&Pagesize=10000&Sort=fbt:asc&date={date}&_=1711000000000'
    
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if data.get('success'):
            stocks = data.get('data', {}).get('pool', [])
            print(f'  ✅ {len(stocks)}只涨停股')
            return stocks
        else:
            print(f'  ⚠️ 接口返回失败')
            return []
    except Exception as e:
        print(f'  ❌ 获取失败：{e}')
        return []


def analyze_stock_morphology(stock: dict) -> dict:
    """
    分析个股形态
    
    Args:
        stock: 个股数据
    
    Returns:
        形态分析结果
    """
    info = stock.get('info', {})
    
    # 基础数据
    code = info.get('code', '')
    name = info.get('name', '')
    change_rate = info.get('hsl', 0)  # 换手率
    open_count = info.get('zcCount', 0)  # 炸板次数
    limit_count = info.get('zc', 1)  # 连板数
    limit_time = info.get('fbt', '')  # 涨停时间
    amount = info.get('amount', 0)  # 成交额
    close = info.get('price', 0)  # 收盘价
    
    # 形态标签
    morphology = []
    
    # 1. 换手率分类
    if change_rate > 5:
        morphology.append('9_换手板')
    else:
        morphology.append('10_缩量板')
    
    # 2. 炸板分类
    if open_count > 0:
        morphology.append('7_回封板')
    
    # 3. 连板分类
    if limit_count >= 2:
        morphology.append('8_连板')
    
    # 4. 涨停时间分类
    if limit_time:
        try:
            hour = int(limit_time[:2])
            if hour <= 9:
                morphology.append('1_早盘板')
            elif hour <= 11:
                morphology.append('2_盘中板')
            elif hour <= 14:
                morphology.append('3_午后板')
            else:
                morphology.append('4_尾盘板')
        except:
            pass
    
    # 5. 成交额分类
    if amount > 1000000000:  # >10 亿
        morphology.append('5_大成交额')
    elif amount > 500000000:  # >5 亿
        morphology.append('6_中成交额')
    else:
        morphology.append('6_小成交额')
    
    return {
        'code': code,
        'name': name,
        'change_rate': change_rate,
        'open_count': open_count,
        'limit_count': limit_count,
        'limit_time': limit_time,
        'amount': amount,
        'close': close,
        'morphology': morphology,
    }


def save_daily_data(date: str, stocks: list, analysis_list: list):
    """
    保存每日数据到涨停形态库
    
    Args:
        date: 日期
        stocks: 原始数据
        analysis_list: 分析结果
    """
    # 统计
    morphology_stats = {}
    for a in analysis_list:
        for m in a['morphology']:
            morphology_stats[m] = morphology_stats.get(m, 0) + 1
    
    # 生成 markdown 报告
    date_formatted = f'{date[:4]}-{date[4:6]}-{date[6:]}'
    
    content = f'''# 涨停形态库 - {date_formatted}

**日期**: {date_formatted}
**涨停总数**: {len(analysis_list)} 只
**数据来源**: 东方财富涨停股池

---

## 形态统计

| 形态分类 | 数量 | 占比 |
|---------|------|------|
'''
    
    for m, count in sorted(morphology_stats.items()):
        ratio = count / len(analysis_list) * 100 if analysis_list else 0
        content += f'| {m} | {count} | {ratio:.1f}% |\n'
    
    # 连板股详情
    limit_stocks = [a for a in analysis_list if '8_连板' in a['morphology']]
    
    content += f'''
---

## 连板股详情

| 股票 | 代码 | 连板数 | 换手率 | 涨停时间 | 成交额 | 形态 |
|------|------|--------|--------|----------|--------|------|
'''
    
    for a in limit_stocks[:20]:  # 最多 20 只
        morphology_str = ' | '.join(a['morphology'])
        content += f"| {a['name']} | {a['code']} | {a['limit_count']}连板 | {a['change_rate']:.1f}% | {a['limit_time']} | {a['amount']/100000000:.1f}亿 | {morphology_str} |\n"
    
    content += f'''
**连板高度**: {max([a['limit_count'] for a in limit_stocks], default=1)}板

---

## 数据保存

**原始数据**: `data_cache/limit_up_raw/{date}.json`
**分析数据**: `data_cache/limit_up_analysis/{date}.json`

---

*数据收集时间*: {datetime.now().strftime('%Y-%m-%d %H:%M')}
'''
    
    # 保存 markdown
    md_dir = Path('memory/涨停形态库')
    md_dir.mkdir(parents=True, exist_ok=True)
    md_file = md_dir / f'{date_formatted}.md'
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 保存 JSON 数据
    data_dir = Path('data_cache/limit_up_analysis')
    data_dir.mkdir(parents=True, exist_ok=True)
    json_file = data_dir / f'{date}.json'
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date': date,
            'count': len(analysis_list),
            'stocks': analysis_list,
            'morphology_stats': morphology_stats
        }, f, ensure_ascii=False, indent=2)
    
    print(f'  ✅ 已保存：{md_file}')


def backtest_period(start_date: str, end_date: str):
    """
    回测指定日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    """
    print('=' * 80)
    print(f'🦞 批量获取涨停数据 + 强化学习')
    print(f'日期范围：{start_date} 至 {end_date}')
    print('=' * 80)
    print()
    
    # 生成日期列表 (排除周末)
    dates = []
    current = datetime.strptime(start_date, '%Y%m%d')
    end = datetime.strptime(end_date, '%Y%m%d')
    
    while current <= end:
        if current.weekday() < 5:  # 周一到周五
            dates.append(current.strftime('%Y%m%d'))
        current += timedelta(days=1)
    
    print(f'📅 交易日：{len(dates)}天')
    print(f'   {dates}')
    print()
    
    # 批量获取数据
    all_analysis = []
    
    for date in dates:
        print(f'[{dates.index(date)+1}/{len(dates)}] {date}')
        
        # 获取涨停股
        stocks = fetch_limit_up_stocks(date)
        
        if stocks:
            # 分析形态
            analysis_list = [analyze_stock_morphology(s) for s in stocks]
            all_analysis.extend(analysis_list)
            
            # 保存数据
            save_daily_data(date, stocks, analysis_list)
        
        print()
        time.sleep(1)  # 避免请求过快
    
    # 汇总统计
    print('=' * 80)
    print('📊 汇总统计')
    print('=' * 80)
    
    total = len(all_analysis)
    morphology_total = {}
    
    for a in all_analysis:
        for m in a['morphology']:
            morphology_total[m] = morphology_total.get(m, 0) + 1
    
    print(f'总涨停股数：{total}只')
    print()
    print('形态分布:')
    for m, count in sorted(morphology_total.items()):
        ratio = count / total * 100 if total else 0
        print(f'  {m}: {count}只 ({ratio:.1f}%)')
    
    # 保存汇总结果
    summary_file = Path('data_cache/limit_up_analysis/汇总统计.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'start_date': start_date,
            'end_date': end_date,
            'total_days': len(dates),
            'total_stocks': total,
            'morphology_stats': morphology_total
        }, f, ensure_ascii=False, indent=2)
    
    print()
    print(f'✅ 汇总统计已保存：{summary_file}')
    
    # 强化学习建议
    print()
    print('=' * 80)
    print('🎯 强化学习建议')
    print('=' * 80)
    
    # 高胜率形态 (假设)
    high_win_rate = ['1_早盘板', '2_盘中板', '8_连板', '9_换手板']
    low_win_rate = ['4_尾盘板', '10_缩量板']
    
    print()
    print('✅ 高胜率形态 (重点关注):')
    for m in high_win_rate:
        if m in morphology_total:
            print(f'  {m}: {morphology_total[m]}只')
    
    print()
    print('❌ 低胜率形态 (建议回避):')
    for m in low_win_rate:
        if m in morphology_total:
            print(f'  {m}: {morphology_total[m]}只')
    
    print()
    print('=' * 80)
    print('✅ 批量获取完成！')
    print('=' * 80)


if __name__ == '__main__':
    import sys
    
    start_date = sys.argv[1] if len(sys.argv) > 1 else '20260317'
    end_date = sys.argv[2] if len(sys.argv) > 2 else '20260328'
    
    backtest_period(start_date, end_date)
