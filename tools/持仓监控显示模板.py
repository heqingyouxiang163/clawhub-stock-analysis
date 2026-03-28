#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓监控显示模板
用于生成持仓监控消息
"""

from 持仓配置 import HOLDINGS

def generate_holdings_message():
    """生成持仓监控消息"""
    
    total_value = sum(h.get('market_value', 0) for h in HOLDINGS)
    total_profit = sum(h.get('profit', 0) for h in HOLDINGS)
    
    lines = [
        "🦞 持仓监控提醒",
        "",
        "📊 持仓明细:",
    ]
    
    for h in HOLDINGS:
        code = h['code']
        name = h['name']
        value = h.get('market_value', 0)
        profit = h.get('profit', 0)
        profit_pct = h.get('profit_pct', 0)
        
        # 格式化显示
        if profit >= 0:
            profit_str = f"+{profit:.2f}"
        else:
            profit_str = f"{profit:.2f}"
        
        lines.append(f"- {name} ({code}): 市值{value:.0f}元，盈亏{profit_str}元 ({profit_pct:+.1f}%)")
    
    lines.extend([
        "",
        f"总市值：{total_value:.0f}元",
        f"总盈亏：{total_profit:+.0f}元",
        "",
        "正在获取最新数据..."
    ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_holdings_message())
