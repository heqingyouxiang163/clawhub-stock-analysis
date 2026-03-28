#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涨停形态每日学习分析脚本
获取今日涨停股并分析形态特征
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import os

# 日期设置
today = datetime.now()
today_str = today.strftime("%Y%m%d")
today_iso = today.strftime("%Y-%m-%d")

# 输出目录
output_dir = "/home/admin/openclaw/workspace/memory/涨停形态库"
stats_file = "/home/admin/openclaw/workspace/memory/涨停形态迭代统计.md"
temp_dir = "/home/admin/openclaw/workspace/temp"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(temp_dir, exist_ok=True)

print(f"📊 开始获取 {today_iso} 涨停股数据...")

# 1. 获取涨停股数据
try:
    # 获取涨跌停行情
    df = ak.stock_zt_pool_em(date=today_str)
    print(f"✅ 获取到 {len(df)} 只涨停股")
    
    # 保存原始数据
    df.to_csv(f"{temp_dir}/涨停股_{today_str}.csv", index=False, encoding='utf-8-sig')
    
except Exception as e:
    print(f"❌ 获取涨停数据失败：{e}")
    # 尝试备选方案
    try:
        df = ak.stock_zt_pool_detail_em(date=today_str)
        print(f"✅ 备选方案获取到 {len(df)} 只涨停股")
        df.to_csv(f"{temp_dir}/涨停股_{today_str}.csv", index=False, encoding='utf-8-sig')
    except Exception as e2:
        print(f"❌ 备选方案也失败：{e2}")
        exit(1)

# 2. 形态分析函数
def analyze_stock_morphology(row):
    """分析单只股票的形态特征"""
    morphologies = []
    
    # 基础数据
    code = row.get('代码', row.get('symbol', ''))
    name = row.get('名称', row.get('name', ''))
    close_price = float(row.get('最新价', row.get('close', 0)))
    change_pct = float(row.get('涨跌幅', row.get('change', 0)))
    turnover = float(row.get('换手率', row.get('turnover', 0)))
    total_mv = float(row.get('总市值', row.get('total_mv', 0))) / 100000000  # 转为亿
    circ_mv = float(row.get('流通市值', row.get('circ_mv', 0))) / 100000000  # 转为亿
    
    # 连板数
    continuous_limit = int(row.get('连板数', row.get('continuous_limit', 1)))
    
    # 封板时间
    first_limit_time = str(row.get('首次封板时间', row.get('first_limit_time', '092500')))
    last_limit_time = str(row.get('最后封板时间', row.get('last_limit_time', '092500')))
    
    # 炸板次数
    break_count = int(row.get('炸板次数', row.get('break_count', 0)))
    
    # 涨停统计
    limit_stats = str(row.get('涨停统计', row.get('limit_stats', '')))
    
    # 所属行业
    industry = str(row.get('所属行业', row.get('industry', '')))
    
    # 封板资金
    limit_fund = float(row.get('封板资金', row.get('limit_fund', 0)))
    
    # 成交额
    turnover_amount = float(row.get('成交额', row.get('turnover_amount', 0)))
    
    # === 形态分类 ===
    
    # 1. 一字板/T字板
    if first_limit_time == '092500' and break_count == 0:
        if '一字' in limit_stats or change_pct >= 9.9:
            morphologies.append('一字板')
        else:
            morphologies.append('T 字板/烂板')
    elif break_count > 0:
        morphologies.append('T 字板/烂板')
    
    # 2. 按涨停时间分类
    hour = int(first_limit_time[:2])
    minute = int(first_limit_time[2:4]) if len(first_limit_time) >= 4 else 0
    
    if hour == 9 and minute <= 35:
        morphologies.append('早盘快速板')
    elif hour == 9:
        morphologies.append('午盘板')
    elif hour >= 14:
        morphologies.append('尾盘板')
    else:
        morphologies.append('午盘板')
    
    # 3. 按连板数分类
    if continuous_limit == 1:
        morphologies.append('首板')
    elif continuous_limit == 2:
        morphologies.append('2 连板')
    elif continuous_limit >= 3:
        morphologies.append('高连板 (3 板+)')
    
    # 4. 按换手率分类
    if turnover < 3:
        morphologies.append('低换手板 (<3%)')
    elif 3 <= turnover <= 20:
        morphologies.append('中等换手板 (3-20%)')
    elif turnover > 20:
        morphologies.append('高换手板 (>20%)')
    
    # 5. 按市值分类
    if total_mv < 100:
        morphologies.append('小市值板 (<100 亿)')
    elif 100 <= total_mv <= 500:
        morphologies.append('中市值板 (100-500 亿)')
    elif total_mv > 500:
        morphologies.append('大市值板 (>500 亿)')
    
    # 6. 20cm 涨停（创业板/科创板）
    if code.startswith('300') or code.startswith('688'):
        if change_pct >= 19:
            morphologies.append('20cm 涨停')
    
    return {
        '代码': code,
        '名称': name,
        '收盘价': close_price,
        '涨跌幅': change_pct,
        '换手率': turnover,
        '总市值 (亿)': round(total_mv, 2),
        '流通市值 (亿)': round(circ_mv, 2),
        '连板数': continuous_limit,
        '首次封板': first_limit_time,
        '最后封板': last_limit_time,
        '炸板次数': break_count,
        '涨停统计': limit_stats,
        '所属行业': industry,
        '封板资金 (万)': round(limit_fund / 10000, 2),
        '成交额 (万)': round(turnover_amount / 10000, 2),
        '形态分类': ' | '.join(morphologies)
    }

# 3. 分析所有股票
print("🔍 开始分析形态特征...")
analyzed_stocks = []

for idx, row in df.iterrows():
    result = analyze_stock_morphology(row)
    analyzed_stocks.append(result)

# 转为 DataFrame
result_df = pd.DataFrame(analyzed_stocks)

# 保存详细分析
result_df.to_csv(f"{temp_dir}/涨停股详细分析_{today_str}.csv", index=False, encoding='utf-8-sig')
print(f"✅ 完成 {len(result_df)} 只股票形态分析")

# 4. 统计各形态数量
print("📈 统计形态分布...")
morphology_count = {}
for stock in analyzed_stocks:
    morphs = stock['形态分类'].split(' | ')
    for morph in morphs:
        morph = morph.strip()
        if morph:
            morphology_count[morph] = morphology_count.get(morph, 0) + 1

# 5. 生成每日报告
report_content = f"""# 涨停形态学习报告 - {today_iso}

**生成时间**: {today.strftime("%Y-%m-%d %H:%M")}  
**涨停总数**: {len(result_df)} 只

---

## 📊 形态分布统计

| 形态类型 | 出现次数 | 占比 |
|----------|----------|------|
"""

# 按次数排序
sorted_morphs = sorted(morphology_count.items(), key=lambda x: x[1], reverse=True)
for morph, count in sorted_morphs:
    ratio = round(count / len(result_df) * 100, 1)
    report_content += f"| {morph} | {count} | {ratio}% |\n"

report_content += f"""
---

## 📋 涨停股详细列表

| 序号 | 代码 | 名称 | 价格 | 涨跌幅 | 换手率 | 市值 (亿) | 连板 | 首次封板 | 形态分类 |
|------|------|------|------|--------|--------|-----------|------|----------|----------|
"""

for i, stock in enumerate(analyzed_stocks, 1):
    report_content += f"| {i} | {stock['代码']} | {stock['名称']} | {stock['收盘价']} | {stock['涨跌幅']}% | {stock['换手率']}% | {stock['总市值 (亿)']} | {stock['连板数']}板 | {stock['首次封板']} | {stock['形态分类']} |\n"

report_content += f"""
---

## 🏆 重点股票分析

### 连板高度
"""

# 找出最高连板
max_continuous = max(analyzed_stocks, key=lambda x: x['连板数'])
report_content += f"- **最高连板**: {max_continuous['名称']}({max_continuous['代码']}) - {max_continuous['连板数']}连板\n"

# 20cm 涨停
twenty_cm = [s for s in analyzed_stocks if '20cm 涨停' in s['形态分类']]
if twenty_cm:
    report_content += f"\n### 20cm 涨停 ({len(twenty_cm)}只)\n"
    for s in twenty_cm:
        report_content += f"- {s['名称']}({s['代码']}): {s['涨跌幅']}%, {s['所属行业']}\n"

# 早盘快速板
early_board = [s for s in analyzed_stocks if '早盘快速板' in s['形态分类']]
report_content += f"\n### 早盘快速板 ({len(early_board)}只)\n"
for s in early_board[:10]:  # 只显示前 10 只
    report_content += f"- {s['名称']}({s['代码']}): {s['首次封板']}封板，{s['所属行业']}\n"

report_content += f"""
---

## 💡 市场情绪分析

- **涨停总数**: {len(result_df)} 只
- **首板数量**: {len([s for s in analyzed_stocks if '首板' in s['形态分类']])} 只
- **连板数量**: {len([s for s in analyzed_stocks if s['连板数'] > 1])} 只
- **20cm 数量**: {len(twenty_cm)} 只
- **一字/T 字板**: {len([s for s in analyzed_stocks if '一字板' in s['形态分类'] or 'T 字板/烂板' in s['形态分类']])} 只

---

## 📁 数据文件

- 原始数据：`temp/涨停股_{today_str}.csv`
- 详细分析：`temp/涨停股详细分析_{today_str}.csv`

---

*本报告由自动化系统生成，数据仅供参考学习*
"""

# 保存每日报告
daily_file = f"{output_dir}/{today_iso}.md"
with open(daily_file, 'w', encoding='utf-8') as f:
    f.write(report_content)

print(f"✅ 每日报告已保存：{daily_file}")

# 6. 更新累计统计
print("📝 更新累计统计...")

# 读取现有统计
try:
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats_content = f.read()
except:
    stats_content = """# 涨停形态迭代统计

**最后更新**: 待更新  
**统计起始**: 2026-03-16  
**累计交易日**: 0 天

---

## 📈 累计形态统计

| 形态类型 | 出现次数 | 今日数量 |
|----------|----------|----------|

---

## 📊 每日涨停数量趋势

| 日期 | 涨停总数 | 首板 | 连板 | 20cm | 炸板率 |
|------|----------|------|------|------|--------|

---

## 🏆 连板高度统计

| 日期 | 最高连板 | 股票名称 |
|------|----------|----------|

---

## 📋 形态胜率追踪

| 形态类型 | 样本数 | 次日溢价>0% | 次日溢价>3% | 次日溢价>5% | 平均溢价 |
|----------|--------|-------------|-------------|-------------|----------|
"""

# 计算今日统计
first_board_count = len([s for s in analyzed_stocks if '首板' in s['形态分类']])
continuous_count = len([s for s in analyzed_stocks if s['连板数'] > 1])
twenty_cm_count = len(twenty_cm)

# 估算炸板率（有炸板次数的股票）
broken_count = len([s for s in analyzed_stocks if s['炸板次数'] > 0])
break_rate = round(broken_count / len(result_df) * 100, 1) if len(result_df) > 0 else 0

# 添加到每日趋势
today_trend = f"| {today_iso} | {len(result_df)} | {first_board_count} | {continuous_count} | {twenty_cm_count} | {break_rate}% |"

# 添加到连板高度
today_max_board = f"| {today_iso} | {max_continuous['连板数']}板 | {max_continuous['名称']} |"

# 更新累计形态统计
new_stats = f"""# 涨停形态迭代统计

**最后更新**: {today_iso} {today.strftime("%H:%M")}  
**统计起始**: 2026-03-16  
**累计交易日**: 需要计算

---

## 📈 累计形态统计

| 形态类型 | 出现次数 | 今日数量 |
|----------|----------|----------|
"""

# 从之前的统计中读取累计数据（简化处理，重新计算）
all_morphs = {}
for morph, count in morphology_count.items():
    all_morphs[morph] = {'累计': count, '今日': count}

for morph, data in sorted(all_morphs.items(), key=lambda x: x[1]['今日'], reverse=True):
    new_stats += f"| {morph} | {data['累计']} | {data['今日']} |\n"

# 添加每日趋势部分
new_stats += f"""
---

## 📊 每日涨停数量趋势

| 日期 | 涨停总数 | 首板 | 连板 | 20cm | 炸板率 |
|------|----------|------|------|------|--------|
{today_trend}

---

## 🏆 连板高度统计

| 日期 | 最高连板 | 股票名称 |
|------|----------|----------|
{today_max_board}

---

## 📋 形态胜率追踪（需要后续数据）

> 注：胜率统计需要后续交易日数据来追踪各形态的次日溢价表现

| 形态类型 | 样本数 | 次日溢价>0% | 次日溢价>3% | 次日溢价>5% | 平均溢价 |
|----------|--------|-------------|-------------|-------------|----------|
| 一字板 | 0 | - | - | - | - |
| T 字板/烂板 | 0 | - | - | - | - |
| 早盘快速板 | 0 | - | - | - | - |
| 首板 | 0 | - | - | - | - |
| 2 连板 | 0 | - | - | - | - |
| 高连板 (3 板+) | 0 | - | - | - | - |
| 高换手板 (>20%) | 0 | - | - | - | - |
| 低换手板 (<3%) | 0 | - | - | - | - |

---

## 🎯 形态库更新日志

- **{today_iso}**: 更新涨停形态统计
  - 今日涨停：{len(result_df)}只
  - 最高连板：{max_continuous['名称']}({max_continuous['连板数']}板)
  - 20cm 涨停：{twenty_cm_count}只

---

## 📝 使用说明

1. **每日自动更新**: 交易日 15:30 自动获取涨停数据并分析
2. **形态分类**: 每只股票可能属于多个形态类别
3. **胜率追踪**: 需要 T+1 日数据来计算各形态的次日表现
4. **数据积累**: 胜率统计需要至少 20 个交易日样本才有参考价值

---

*本统计由自动化系统生成，数据仅供参考学习*
"""

with open(stats_file, 'w', encoding='utf-8') as f:
    f.write(new_stats)

print(f"✅ 累计统计已更新：{stats_file}")

print("\n" + "="*50)
print("🎉 涨停形态每日学习完成！")
print("="*50)
print(f"📊 今日涨停总数：{len(result_df)}只")
print(f"🏆 最高连板：{max_continuous['名称']}({max_continuous['连板数']}板)")
print(f"📈 形态分析已保存到：{daily_file}")
print(f"📝 累计统计已更新：{stats_file}")
