#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涨停形态每日学习分析脚本 - 快速版
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
    df = ak.stock_zt_pool_em(date=today_str)
    print(f"✅ 获取到 {len(df)} 只涨停股")
    df.to_csv(f"{temp_dir}/涨停股_{today_str}.csv", index=False, encoding='utf-8-sig')
except Exception as e:
    print(f"❌ 获取失败：{e}")
    exit(1)

# 2. 形态分析
def analyze_morphology(row):
    morphs = []
    
    code = str(row.get('代码', ''))
    name = str(row.get('名称', ''))
    turnover = float(row.get('换手率', 0))
    continuous = int(row.get('连板数', 1))
    first_time = str(row.get('首次封板时间', '092500'))
    break_count = int(row.get('炸板次数', 0))
    
    # 1. 一字板
    if first_time == '092500' and break_count == 0:
        morphs.append('1_一字板')
    # 2. 早盘秒板 (9:30-9:35)
    elif first_time >= '093000' and first_time <= '093500':
        morphs.append('2_早盘秒板')
    # 3. 早盘强势板 (9:30-10:00)
    elif first_time > '093000' and first_time <= '100000':
        morphs.append('3_早盘强势板')
    # 4. 上午板 (10:00-11:30)
    elif first_time > '100000' and first_time <= '113000':
        morphs.append('4_上午板')
    # 5. 午后板 (13:00-14:00)
    elif first_time > '130000' and first_time <= '140000':
        morphs.append('5_午后板')
    # 6. 尾盘板 (14:00 后)
    elif first_time > '140000':
        morphs.append('6_尾盘板')
    
    # 7. 回封板
    if break_count > 0:
        morphs.append('7_回封板')
    
    # 8. 连板
    if continuous >= 2:
        morphs.append('8_连板')
    
    # 9. 换手板
    if turnover > 5:
        morphs.append('9_换手板')
    
    # 10. 缩量板
    if turnover < 5 and break_count == 0:
        morphs.append('10_缩量板')
    
    return ' | '.join(morphs) if morphs else '3_早盘强势板'

print("🔍 分析形态...")
results = []
for idx, row in df.iterrows():
    r = {
        '代码': str(row.get('代码', '')),
        '名称': str(row.get('名称', '')),
        '最新价': float(row.get('最新价', 0)),
        '涨跌幅': float(row.get('涨跌幅', 0)),
        '换手率': float(row.get('换手率', 0)),
        '连板数': int(row.get('连板数', 1)),
        '首次封板': str(row.get('首次封板时间', '092500')),
        '炸板次数': int(row.get('炸板次数', 0)),
        '形态': analyze_morphology(row)
    }
    results.append(r)

result_df = pd.DataFrame(results)
result_df.to_csv(f"{temp_dir}/涨停分析_{today_str}.csv", index=False, encoding='utf-8-sig')

# 3. 统计形态
morph_count = {}
for r in results:
    for m in r['形态'].split(' | '):
        m = m.strip()
        if m:
            morph_count[m] = morph_count.get(m, 0) + 1

# 4. 生成报告
total = len(results)
print(f"\n{'='*50}")
print(f"📊 {today_iso} 涨停形态分析报告")
print(f"{'='*50}")
print(f"涨停总数：{total} 只")
print(f"\n形态统计:")
for m, c in sorted(morph_count.items(), key=lambda x: -x[1]):
    pct = round(c/total*100, 1) if total > 0 else 0
    print(f"  {m}: {c}只 ({pct}%)")

# 连板股
continuous_stocks = [r for r in results if r['连板数'] >= 2]
if continuous_stocks:
    print(f"\n连板股 ({len(continuous_stocks)}只):")
    for r in sorted(continuous_stocks, key=lambda x: -x['连板数'])[:5]:
        print(f"  {r['名称']}({r['代码']}): {r['连板数']}连板, 换手{r['换手率']}%")

# 5. 保存每日报告
report = f"""# 涨停形态库 - {today_iso}

**日期**: {today_iso}
**涨停总数**: {total} 只
**数据来源**: 东方财富涨停股池

---

## 形态统计

| 形态分类 | 数量 | 占比 | 说明 |
|---------|------|------|------|
"""
for m, c in sorted(morph_count.items(), key=lambda x: -x[1]):
    pct = round(c/total*100, 1) if total > 0 else 0
    desc = {
        '1_一字板': '开盘即涨停',
        '2_早盘秒板': '开盘 5 分钟内封板',
        '3_早盘强势板': '9:30-10:00 封板',
        '4_上午板': '10:00-11:30 封板',
        '5_午后板': '13:00-14:00 封板',
        '6_尾盘板': '14:00 后封板',
        '7_回封板': '炸板回封',
        '8_连板': '连板≥2',
        '9_换手板': '换手率>5%',
        '10_缩量板': '换手<5% 且无炸板'
    }.get(m, '')
    report += f"| {m} | {c} | {pct}% | {desc} |\n"

report += f"""
---

## 连板股详情

| 股票 | 代码 | 连板数 | 换手率 | 形态 |
|------|------|--------|--------|------|
"""
for r in sorted(continuous_stocks, key=lambda x: -x['连板数']):
    report += f"| {r['名称']} | {r['代码']} | {r['连板数']}连板 | {r['换手率']}% | {r['形态']} |\n"

max_cont = max(continuous_stocks, key=lambda x: x['连板数']) if continuous_stocks else {'名称': '无', '连板数': 1}
report += f"""
**连板高度**: {max_cont['连板数']}板 ({max_cont['名称']})

---

## 市场特征分析

### 情绪特征
- **涨停总数**: {total} 只 - {'火热' if total > 50 else '一般' if total > 30 else '偏冷'}
- **连板股**: {len(continuous_stocks)} 只
- **换手板比例**: {round(morph_count.get('9_换手板', 0)/total*100, 1) if total > 0 else 0}%
- **一字板**: {morph_count.get('1_一字板', 0)} 只

---

*数据生成时间*: {today.strftime("%Y-%m-%d %H:%M")}
"""

daily_file = f"{output_dir}/{today_iso}.md"
with open(daily_file, 'w', encoding='utf-8') as f:
    f.write(report)

print(f"\n✅ 报告已保存：{daily_file}")

# 6. 更新累计统计 (简化)
print("📝 更新累计统计...")
try:
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = f.read()
    
    # 添加今日数据到表格
    today_line = f"| {today_iso} | {total} | {len([r for r in results if r['连板数']==1])} | {len(continuous_stocks)} | {morph_count.get('9_换手板', 0)} | - |\n"
    
    if "| 日期 | 涨停总数 |" in stats:
        # 找到表格位置并插入
        lines = stats.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if line.startswith("| 日期 | 涨停总数 |"):
                new_lines.append(today_line)
        stats = '\n'.join(new_lines)
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write(stats)
    print(f"✅ 累计统计已更新")
except Exception as e:
    print(f"⚠️ 更新统计失败：{e}")

print(f"\n🎉 完成！涨停总数：{total}只")
