#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实涨幅榜 - 手动维护 (根据用户截图更新)
包含 7-9% 主升浪股票
"""

# 2026-03-25 用户截图里的 7-9% 股票
REAL_TOP_GAINERS = [
    # 7-9% 主升浪 (用户截图)
    {'code': '600537', 'name': '亿晶光电', 'change_pct': 9.04, 'amount': 2160000},
    {'code': '600930', 'name': '华电新能', 'change_pct': 8.90, 'amount': 6780000},
    {'code': '002309', 'name': '中利集团', 'change_pct': 8.89, 'amount': 9960000},
    {'code': '002428', 'name': '云南锗业', 'change_pct': 8.78, 'amount': 1040000},
    {'code': '003043', 'name': '华亚智能', 'change_pct': 8.68, 'amount': 38800},
    {'code': '002887', 'name': '绿茵生态', 'change_pct': 8.67, 'amount': 139600},
    {'code': '000966', 'name': '长源电力', 'change_pct': 8.38, 'amount': 2910000},
    {'code': '600345', 'name': '长江通信', 'change_pct': 8.31, 'amount': 180400},
    
    # 其他热点
    {'code': '002730', 'name': '电光科技', 'change_pct': 10.0, 'amount': 7580000},
    {'code': '002475', 'name': '立讯精密', 'change_pct': 10.0, 'amount': 12500000},
    {'code': '601869', 'name': '长飞光纤', 'change_pct': 10.0, 'amount': 53780000},
]


def get_real_top_gainers():
    """获取真实涨幅榜"""
    return REAL_TOP_GAINERS.copy()


if __name__ == "__main__":
    print("真实涨幅榜 (7% 以上):\n")
    print("=" * 70)
    
    stocks = sorted(get_real_top_gainers(), key=lambda x: x['change_pct'], reverse=True)
    
    for i, s in enumerate(stocks, 1):
        amount = s['amount'] / 10000  # 亿
        print(f"{i:2d}. {s['code']} {s['name']:10s} {s['change_pct']:+6.2f}% | 成交：{amount:6.2f}亿")
