#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
涨停分时形态学习工具

功能:
1. 分析历史涨停股的分时图特征
2. 学习涨停时间、封板强度、炸板情况
3. 生成形态胜率统计
4. 为盘中推送提供形态参考

使用场景:
- 盘后学习当日涨停股形态
- 统计各形态胜率
- 为次日推送提供依据
"""

import json
import os
from datetime import datetime

# 配置
MORPHOLOGY_FILE = "/home/admin/openclaw/workspace/memory/涨停形态库/形态胜率统计.json"
HISTORY_DAYS = 20  # 统计最近 20 天数据


# ==================== 涨停形态分类 ====================

LIMIT_UP_TYPES = {
    "早盘强势板": {
        "time_range": (930, 945),  # 9:30-9:45
        "desc": "开盘 15 分钟内涨停，最强形态"
    },
    "回封板": {
        "feature": "炸板后回封",
        "desc": "炸板后重新封死，多头强势"
    },
    "换手板": {
        "turnover_range": (5, 15),  # 换手率 5%-15%
        "desc": "充分换手后涨停，健康形态"
    },
    "缩量板": {
        "turnover_range": (0, 3),  # 换手率<3%
        "desc": "缩量涨停，一致性强"
    },
    "一字板": {
        "feature": "一字涨停",
        "desc": "开盘即涨停，最强一致性"
    },
    "尾盘板": {
        "time_range": (1430, 1500),  # 14:30-15:00
        "desc": "尾盘涨停，强度一般"
    },
    "秒板": {
        "feature": "秒速涨停",
        "desc": "瞬间涨停，资金强势"
    },
    "连板": {
        "feature": "连续涨停",
        "desc": "连板股，关注晋级率"
    }
}


# ==================== 数据加载 ====================

def load_limit_up_history(days=HISTORY_DAYS):
    """加载历史涨停数据"""
    history = []
    base_dir = "/home/admin/openclaw/workspace/memory/涨停形态库"
    
    if not os.path.exists(base_dir):
        print(f"⚠️ 涨停形态库不存在：{base_dir}")
        return history
    
    # 读取最近 N 天的涨停数据
    count = 0
    for i in range(days):
        date = datetime.now()
        from datetime import timedelta
        date = date - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        file_path = os.path.join(base_dir, f"{date_str}.md")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # 解析涨停股列表
                stocks = parse_limit_up_stocks(content, date_str)
                history.extend(stocks)
                count += 1
    
    print(f"✅ 加载{count}天涨停数据，共{len(history)}只")
    return history


def parse_limit_up_stocks(content, date):
    """解析涨停股数据"""
    stocks = []
    
    # 简单解析 Markdown 表格
    lines = content.split('\n')
    for line in lines:
        if '|' in line and '涨停' in line:
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


# ==================== 形态胜率统计 ====================

def calculate_morphology_win_rate(history):
    """计算各形态胜率"""
    morphology_stats = {}
    
    for stock in history:
        morph = stock.get('morphology', '未知')
        
        if morph not in morphology_stats:
            morphology_stats[morph] = {
                'count': 0,
                'next_day_premium': []  # 次日溢价
            }
        
        morphology_stats[morph]['count'] += 1
        
        # TODO: 获取次日溢价数据
        # 这里需要接入次日涨跌幅数据
    
    # 计算胜率
    results = {}
    for morph, stats in morphology_stats.items():
        results[morph] = {
            'count': stats['count'],
            'win_rate': 0,  # TODO: 计算胜率
            'avg_premium': 0,  # 平均溢价
            'description': LIMIT_UP_TYPES.get(morph, {}).get('desc', '')
        }
    
    return results


# ==================== 形态评分 ====================

def morphology_score(stock_morphology):
    """
    根据形态给出评分加成
    
    参数:
        stock_morphology: 股票形态 (如"早盘强势板"、"换手板"等)
    
    返回:
        评分加成 (-10 到 +20 分)
    """
    
    # 基于历史胜率的评分加成
    scores = {
        "早盘强势板": +15,  # 最强形态
        "回封板": +10,  # 多头强势
        "换手板": +8,  # 健康形态
        "缩量板": +5,  # 一致性强
        "一字板": +20,  # 最强一致性 (但买不到)
        "连板": +12,  # 连板股
        "秒板": +10,  # 资金强势
        "尾盘板": -5,  # 强度一般
        "未知": 0
    }
    
    return scores.get(stock_morphology, 0)


# ==================== 学习报告 ====================

def generate_learning_report(history):
    """生成学习报告"""
    print("=" * 70)
    print("📚 涨停分时形态学习报告")
    print(f"统计范围：最近{len(set(s['date'] for s in history))}天")
    print(f"涨停总数：{len(history)}只")
    print("=" * 70)
    print()
    
    # 形态分布
    morphology_count = {}
    for stock in history:
        morph = stock.get('morphology', '未知')
        morphology_count[morph] = morphology_count.get(morph, 0) + 1
    
    print("📊 形态分布:")
    print()
    print(f"{'形态':<15} {'数量':>8} {'占比':>10}")
    print("-" * 40)
    
    for morph, count in sorted(morphology_count.items(), key=lambda x: x[1], reverse=True):
        ratio = count / len(history) * 100 if len(history) > 0 else 0
        print(f"{morph:<15} {count:>8} {ratio:>9.1f}%")
    
    print()
    print("=" * 70)
    
    # 形态评分参考
    print("\n💡 形态评分参考:")
    print()
    print(f"{'形态':<15} {'评分加成':>10} {'说明':<30}")
    print("-" * 60)
    
    for morph, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        desc = LIMIT_UP_TYPES.get(morph, {}).get('desc', '')
        sign = '+' if score >= 0 else ''
        print(f"{morph:<15} {sign}{score:>8}分 {desc:<30}")
    
    print()
    print("=" * 70)


# ==================== 主函数 ====================

def learn_today():
    """学习今日涨停形态"""
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📚 学习今日 ({today}) 涨停形态...")
    
    # 加载今日数据
    history = load_limit_up_history(days=1)
    
    if not history:
        print("⚠️ 今日无涨停数据")
        return
    
    # 生成学习报告
    generate_learning_report(history)
    
    # 保存形态统计
    save_morphology_stats(history)


def save_morphology_stats(history):
    """保存形态统计"""
    stats = calculate_morphology_win_rate(history)
    
    os.makedirs(os.path.dirname(MORPHOLOGY_FILE), exist_ok=True)
    with open(MORPHOLOGY_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'update_time': datetime.now().isoformat(),
            'history_days': HISTORY_DAYS,
            'total_stocks': len(history),
            'morphology_stats': stats
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 形态统计已保存：{MORPHOLOGY_FILE}")


    # 显示总耗时
    total_elapsed = time.time() - total_start
    if total_elapsed < 1:
        print(f"
✅ **总耗时**: {total_elapsed*1000:.0f}ms")
    elif total_elapsed < 60:
        print(f"
✅ **总耗时**: {total_elapsed:.1f}秒")
    else:
        print(f"
✅ **总耗时**: {total_elapsed/60:.1f}分钟")

if __name__ == "__main__":
    total_start = time.time()  # 记录总开始时间
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python3 涨停分时形态学习.py [选项]")
        print()
        print("选项:")
        print("  --learn     学习今日涨停")
        print("  --history   查看历史统计")
        print("  --score     查看形态评分")
        sys.exit(1)
    
    option = sys.argv[1]
    
    if option == "--learn":
        learn_today()
    elif option == "--history":
        history = load_limit_up_history()
        generate_learning_report(history)
    elif option == "--score":
        print("形态评分参考:")
        for morph, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            desc = LIMIT_UP_TYPES.get(morph, {}).get('desc', '')
            sign = '+' if score >= 0 else ''
            print(f"  {morph}: {sign}{score}分 - {desc}")
