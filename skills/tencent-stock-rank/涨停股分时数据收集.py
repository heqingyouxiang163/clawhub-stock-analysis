#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 涨停股分时图数据收集

功能:
- 收集涨停股的分时图数据
- 记录涨停时间、封单变化
- 保存分时价格曲线
- 用于强化学习训练

使用:
    python3 涨停股分时数据收集.py
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path


def get_intraday_data(code: str, date: str = None) -> dict:
    """
    获取个股分时图数据
    
    Args:
        code: 股票代码 (如 sh600773)
        date: 日期 (如 20260328)
    
    Returns:
        分时图数据
    """
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    # 腾讯财经分时接口
    url = f'http://data.gtimg.cn/flashdata/hushen/minute/{code}.js?maxcnt=32000&date={date}'
    
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            # 解析数据
            lines = resp.text.strip().split('\n')
            data_points = []
            
            for line in lines:
                if 'data' in line:
                    # 格式：_sh600773.data = ["093000,19.50,1000", "093100,19.55,1200", ...]
                    content = line.split('=')[1].strip().strip('";')
                    points = content.strip('["').strip('"]').split('","')
                    
                    for point in points:
                        parts = point.split(',')
                        if len(parts) >= 3:
                            data_points.append({
                                'time': parts[0],  # 时间 (093000)
                                'price': float(parts[1]),  # 价格
                                'volume': int(parts[2]),  # 成交量
                            })
            
            return {
                'code': code,
                'date': date,
                'data': data_points,
                'count': len(data_points)
            }
    except Exception as e:
        print(f'⚠️ 获取 {code} 分时数据失败：{e}')
    
    return None


def analyze_limit_up_morphology(intraday_data: dict) -> dict:
    """
    分析涨停形态
    
    Args:
        intraday_data: 分时图数据
    
    Returns:
        形态分析结果
    """
    data = intraday_data.get('data', [])
    if not data:
        return None
    
    # 计算关键指标
    prices = [d['price'] for d in data]
    volumes = [d['volume'] for d in data]
    
    # 涨停时间
    limit_up_time = None
    limit_up_price = max(prices)
    
    for i, d in enumerate(data):
        if d['price'] == limit_up_price:
            limit_up_time = d['time']
            break
    
    # 分时均价
    avg_price = sum(prices) / len(prices)
    
    # 价格位置 (相对于均价)
    price_position = (limit_up_price - avg_price) / avg_price * 100
    
    # 量能分析
    avg_volume = sum(volumes) / len(volumes)
    volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
    
    # 形态分类
    morphology = []
    
    # 1. 涨停时间分类
    if limit_up_time:
        hour = int(limit_up_time[:2])
        minute = int(limit_up_time[2:4])
        time_minutes = hour * 60 + minute
        
        if time_minutes <= 9 * 60 + 35:  # 9:35 前
            morphology.append('早盘强势板')
        elif time_minutes <= 11 * 60 + 30:  # 11:30 前
            morphology.append('盘中板')
        elif time_minutes <= 14 * 60 + 30:  # 14:30 前
            morphology.append('午后板')
        else:
            morphology.append('尾盘偷袭板⚠️')
    
    # 2. 价格位置分类
    if price_position > 3:
        morphology.append('强势板')
    elif price_position > 1:
        morphology.append('一般板')
    else:
        morphology.append('弱势板')
    
    # 3. 量能分类
    if volume_ratio > 2:
        morphology.append('放量板')
    elif volume_ratio > 1:
        morphology.append('正常板')
    else:
        morphology.append('缩量板⚠️')
    
    return {
        'limit_up_time': limit_up_time,
        'limit_up_price': limit_up_price,
        'avg_price': round(avg_price, 2),
        'price_position': round(price_position, 2),
        'volume_ratio': round(volume_ratio, 2),
        'morphology': morphology,
        'score': calculate_score(morphology)
    }


def calculate_score(morphology: list) -> int:
    """
    计算形态评分 (0-100)
    
    Args:
        morphology: 形态标签列表
    
    Returns:
        评分
    """
    score = 60  # 基础分
    
    # 加分项
    if '早盘强势板' in morphology:
        score += 25
    if '盘中板' in morphology:
        score += 15
    if '强势板' in morphology:
        score += 10
    if '放量板' in morphology:
        score += 5
    
    # 减分项
    if '尾盘偷袭板⚠️' in morphology:
        score -= 30
    if '缩量板⚠️' in morphology:
        score -= 15
    if '弱势板' in morphology:
        score -= 10
    
    return min(100, max(0, score))


def collect_all_limit_up_stocks(date: str = None):
    """
    收集所有涨停股的分时数据
    
    Args:
        date: 日期
    """
    if date is None:
        date = datetime.now().strftime('%Y%m%d')
    
    print(f"🔍 收集 {date} 涨停股分时数据...")
    
    # 先获取涨停股列表
    from 盘中实时监控 import get_top_gainers
    stocks = get_top_gainers(limit=200)
    limit_up_stocks = [s for s in stocks if s['change_pct'] >= 9.5]
    
    print(f"✅ 找到 {len(limit_up_stocks)} 只涨停股")
    print()
    
    # 收集分时数据
    results = []
    for i, stock in enumerate(limit_up_stocks, 1):
        code = stock['code']
        prefix = 'sh' if code.startswith('6') else 'sz'
        full_code = f'{prefix}{code}'
        
        print(f'[{i}/{len(limit_up_stocks)}] 获取 {full_code} {stock["name"]}...')
        
        intraday = get_intraday_data(full_code, date)
        if intraday and intraday['data']:
            analysis = analyze_limit_up_morphology(intraday)
            if analysis:
                results.append({
                    'stock': stock,
                    'code': full_code,
                    'intraday_count': intraday['count'],
                    'analysis': analysis
                })
                print(f'  ✅ 涨停时间：{analysis["limit_up_time"]}, 评分：{analysis["score"]}')
        
        # 避免请求过快
        time.sleep(0.2)
    
    # 保存结果
    save_dir = Path('data_cache/limit_up_intraday')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    save_file = save_dir / f'{date}.json'
    with open(save_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print()
    print(f'✅ 数据已保存到：{save_file}')
    print(f'   共 {len(results)} 只涨停股')
    
    # 统计
    scores = [r['analysis']['score'] for r in results]
    print(f'   平均评分：{sum(scores)/len(scores):.1f}')
    print(f'   最高评分：{max(scores)}')
    print(f'   最低评分：{min(scores)}')


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/home/admin/openclaw/workspace/clawhub-stock-analysis/skills/tencent-stock-rank')
    
    date = sys.argv[1] if len(sys.argv) > 1 else None
    collect_all_limit_up_stocks(date)
