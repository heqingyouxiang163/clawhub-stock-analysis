import pandas as pd
from datetime import datetime
import json

# 读取涨停股数据
df = pd.read_csv('temp/涨停股_20260319.csv')

# 分析每只股票
results = []
for idx, row in df.iterrows():
    code = row['代码']
    name = row['名称']
    turnover = row['换手率']
    market_cap = row['流通市值']
    volume = row['成交额']
    lianban = row['连板数']
    first_close = str(row['首次封板时间'])
    zhaban = row['炸板次数']
    industry = row['所属行业']
    
    # 形态分类逻辑
    patterns = []
    
    # 连板/首板判断
    if lianban >= 2:
        patterns.append('连板')
    else:
        patterns.append('首板')
    
    # 一字板判断 (换手率<1% 且炸板 0 次)
    if turnover < 1 and zhaban == 0:
        patterns.append('一字板')
    # T 字板判断 (换手率<3% 且炸板>0 次)
    elif turnover < 3 and zhaban > 0:
        patterns.append('T 字板')
    # 换手板判断 (换手率>5%)
    elif turnover > 5:
        patterns.append('换手板')
    
    # 回封板判断
    if zhaban >= 1:
        patterns.append('回封板')
    
    # 时间判断
    close_hour = int(first_close[:2])
    close_min = int(first_close[2:4]) if len(first_close) >= 4 else 0
    if close_hour < 10:
        patterns.append('早盘板')
    elif 13 <= close_hour < 14:
        patterns.append('午盘板')
    elif close_hour >= 14 and close_min >= 30:
        patterns.append('尾盘板')
    
    # 市值分类
    if market_cap < 5e9:
        cap_class = '小市值 (<50 亿)'
    elif market_cap < 1e10:
        cap_class = '中市值 (50-100 亿)'
    else:
        cap_class = '大市值 (>100 亿)'
    
    results.append({
        '代码': code,
        '名称': name,
        '换手率': turnover,
        '流通市值 (亿)': round(market_cap/1e8, 2),
        '成交额 (亿)': round(volume/1e8, 2),
        '连板数': lianban,
        '炸板次数': zhaban,
        '首次封板': first_close,
        '形态分类': patterns,
        '市值分类': cap_class,
        '所属行业': industry
    })

# 保存分析结果
with open('temp/涨停分析_20260319.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f'完成分析 {len(results)} 只涨停股')
print('\n全部股票分析:')
for i, r in enumerate(results):
    print(f"{i+1}. {r['代码']} {r['名称']} | 换手:{r['换手率']}% | 连板:{r['连板数']} | 形态:{r['形态分类']} | 行业:{r['所属行业']}")

# 统计各形态数量
pattern_stats = {}
for r in results:
    for p in r['形态分类']:
        pattern_stats[p] = pattern_stats.get(p, 0) + 1

print('\n形态统计:')
for p, count in sorted(pattern_stats.items(), key=lambda x: -x[1]):
    print(f"  {p}: {count}只")

# 统计行业分布
industry_stats = {}
for r in results:
    industry_stats[r['所属行业']] = industry_stats.get(r['所属行业'], 0) + 1

print('\n行业分布:')
for ind, count in sorted(industry_stats.items(), key=lambda x: -x[1]):
    print(f"  {ind}: {count}只")
