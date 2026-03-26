#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📈 实时 A 股涨幅榜 - 主入口

触发关键词：
- 实时涨幅榜
- A 股涨幅榜
- 今日涨幅榜
- 涨幅榜
- 涨停榜

使用示例：
    python3 realtime_gainers.py
    python3 realtime_gainers.py 50  # 获取前 50 只
"""

import sys
import os

# 添加工具路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from 获取涨幅榜 import get_realtime_gainers, display_gainers


def main():
    """主函数 - 支持命令行参数"""
    
    # 获取命令行参数（默认 150 只）
    limit = 150
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            if limit < 1 or limit > 500:
                limit = 150
        except ValueError:
            limit = 150
    
    print(f"\n🦞 炒股龙虾 - 实时 A 股涨幅榜")
    print(f"📊 获取前 {limit} 只股票\n")
    
    # 获取数据
    stocks = get_realtime_gainers(limit=limit)
    
    # 显示结果
    display_gainers(stocks)
    
    # 返回数据
    return stocks


if __name__ == "__main__":
    main()
