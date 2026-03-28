#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 批量处理工具

功能:
- 批量分析多只股票
- 减少 AI 调用次数
- 节省 Token

使用:
    from 批量处理工具 import batch_analyze
    results = batch_analyze([股票 1, 股票 2, ...])
"""

import json
from typing import List, Dict
from pathlib import Path


def batch_analyze(stocks: List[Dict], batch_size: int = 10) -> List[Dict]:
    """批量分析股票
    
    Args:
        stocks: 股票数据列表
        batch_size: 每批处理数量
    
    Returns:
        分析结果列表
    """
    results = []
    
    # 分批处理
    for i in range(0, len(stocks), batch_size):
        batch = stocks[i:i+batch_size]
        print(f"📊 处理批次 {i//batch_size + 1}: {len(batch)} 只股票")
        
        # 批量分析 (1 次 AI 调用 vs len(batch) 次)
        batch_results = _analyze_batch(batch)
        results.extend(batch_results)
    
    return results


def _analyze_batch(batch: List[Dict]) -> List[Dict]:
    """分析一批股票
    
    Args:
        batch: 一批股票数据
    
    Returns:
        分析结果
    """
    # 构建批量分析提示
    # 1 次调用分析多只股票，大幅节省 Token
    
    prompt = f"""批量分析 {len(batch)} 只股票，每只返回精简结果:

数据:
{json.dumps(batch, ensure_ascii=False, indent=2)}

返回格式 (JSON):
{{
    "results": [
        {{
            "code": "股票代码",
            "recommend": true/false,
            "score": 0-100,
            "reasons": ["理由 1", "理由 2"],
            "risk": "高/中/低"
        }}
    ]
}}
"""
    
    # TODO: 调用 AI 分析
    # 为了演示，返回模拟结果
    
    results = []
    for stock in batch:
        results.append({
            'code': stock.get('code', ''),
            'name': stock.get('name', ''),
            'recommend': stock.get('price_change_pct', 0) > 3,
            'score': min(100, max(0, stock.get('price_change_pct', 0) * 10)),
            'reasons': ['批量分析结果'],
            'risk': '中'
        })
    
    return results


def batch_optimize_output(results: List[Dict]) -> str:
    """批量优化输出 (精简格式)
    
    Args:
        results: 分析结果列表
    
    Returns:
        精简输出文本
    """
    if not results:
        return "无数据"
    
    # 只输出推荐股票
    recommended = [r for r in results if r.get('recommend')]
    
    if not recommended:
        return "❌ 无推荐股票"
    
    # 按评分排序
    recommended.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # 生成精简输出
    output = []
    output.append(f"🦞 股票推荐 ({len(recommended)} 只)")
    output.append("")
    
    for i, stock in enumerate(recommended[:10], 1):  # 最多 10 只
        output.append(f"{i}. {stock.get('name')} ({stock.get('code')})")
        output.append(f"   评分：{stock.get('score')} | 风险：{stock.get('risk')}")
        for reason in stock.get('reasons', [])[:2]:  # 最多 2 个理由
            output.append(f"   • {reason}")
        output.append("")
    
    return "\n".join(output)


if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("🦞 批量处理工具测试")
    print("=" * 60)
    print()
    
    # 测试数据
    test_stocks = [
        {'code': '000001', 'name': '平安银行', 'price_change_pct': 5.2},
        {'code': '000002', 'name': '万科 A', 'price_change_pct': 3.1},
        {'code': '000003', 'name': '测试股票', 'price_change_pct': 8.5},
    ]
    
    # 批量分析
    results = batch_analyze(test_stocks)
    
    # 优化输出
    output = batch_optimize_output(results)
    print(output)
