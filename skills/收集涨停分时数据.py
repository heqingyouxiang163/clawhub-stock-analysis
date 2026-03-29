#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 收集历史涨停股分时数据

从涨停形态库读取历史数据，收集分时图数据
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime


def get_intraday_data(code: str, date: str) -> list:
    """
    获取个股分时图数据
    
    Args:
        code: 股票代码 (如 600227)
        date: 日期 (如 20260321)
    
    Returns:
        分时数据列表
    """
    prefix = 'sh' if code.startswith('6') else 'sz'
    full_code = f'{prefix}{code}'
    
    url = f'http://data.gtimg.cn/flashdata/hushen/minute/{full_code}.js?maxcnt=32000&date={date}'
    
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            lines = resp.text.strip().split('\n')
            data_points = []
            
            for line in lines:
                if 'data' in line:
                    content = line.split('=')[1].strip().strip('";')
                    points = content.strip('["').strip('"]').split('","')
                    
                    for point in points:
                        parts = point.split(',')
                        if len(parts) >= 4:
                            data_points.append({
                                'time': parts[0],
                                'price': float(parts[1]),
                                'volume': int(parts[2]),
                                'avg_price': float(parts[3])
                            })
            
            return data_points
    except Exception as e:
        pass
    
    return []


def collect_history_data():
    """收集历史涨停股分时数据"""
    print("=" * 80)
    print("🦞 收集历史涨停股分时数据")
    print("=" * 80)
    print()
    
    # 涨停形态库目录
    library_dir = Path('memory/涨停形态库')
    save_dir = Path('data_cache/limit_up_intraday')
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取所有涨停形态库文件
    collected_stocks = []
    
    for md_file in library_dir.glob('*.md'):
        if '回测' in str(md_file) or '统计' in str(md_file) or '强化' in str(md_file) or '报告' in str(md_file):
            continue
        
        print(f"📄 处理 {md_file.name}...")
        
        date = md_file.stem  # 如 2026-03-21
        date_str = date.replace('-', '')  # 如 20260321
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取连板股表格
        lines = content.split('\n')
        in_table = False
        
        for line in lines:
            if '| 股票 | 代码 | 连板数 |' in line or '| 股票 | 代码 |' in line:
                in_table = True
                continue
            
            if in_table and line.startswith('|') and '---' not in line:
                parts = line.split('|')
                if len(parts) >= 5:
                    try:
                        name = parts[1].strip()
                        code = parts[2].strip()
                        limit_count = parts[3].strip()
                        
                        # 获取分时数据
                        print(f"  获取 {code} {name} 分时数据...", end=' ')
                        intraday = get_intraday_data(code, date_str)
                        
                        if intraday:
                            print(f"✅ {len(intraday)}个点")
                            
                            collected_stocks.append({
                                '日期': date,
                                '代码': code,
                                '名称': name,
                                '连板数': limit_count,
                                'intraday_data': intraday
                            })
                            
                            # 保存单个股票数据
                            stock_file = save_dir / f"{code}_{date_str}.json"
                            with open(stock_file, 'w', encoding='utf-8') as f:
                                json.dump({
                                    '日期': date,
                                    '代码': code,
                                    '名称': name,
                                    '连板数': limit_count,
                                    'intraday_data': intraday
                                }, f, ensure_ascii=False, indent=2)
                        else:
                            print("❌ 无数据")
                        
                        # 避免请求过快
                        time.sleep(0.1)
                        
                    except Exception as e:
                        continue
        
        print()
    
    # 保存汇总数据
    if collected_stocks:
        summary_file = save_dir / '汇总数据.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                '收集时间': datetime.now().isoformat(),
                '总股票数': len(collected_stocks),
                '股票列表': collected_stocks
            }, f, ensure_ascii=False, indent=2)
        
        print("=" * 80)
        print(f"✅ 收集完成！")
        print(f"总股票数：{len(collected_stocks)}只")
        print(f"保存目录：{save_dir}")
        print("=" * 80)
    else:
        print("⚠️ 没有收集到数据")


if __name__ == '__main__':
    collect_history_data()
