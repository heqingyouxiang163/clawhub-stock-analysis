# -*- coding: utf-8 -*-
"""
🦞 持仓配置文件

最后更新：2026-03-27 12:46
数据来源：用户截图
"""

# 当前持仓配置 (2026-03-27 12:02 截图)
HOLDINGS = [
    {
        "code": "002692",
        "name": "法尔胜",
        "market_value": 2696.00,
        "current_price": 13.480,
        "cost_price": 13.385,
        "day_profit": 19.00,
        "day_profit_pct": 0.710,
        "shares": 200  # 根据市值/现价估算
    },
    {
        "code": "000973",
        "name": "佛塑科技",
        "market_value": 3684.00,
        "current_price": 18.420,
        "cost_price": 18.544,
        "day_profit": -25.85,
        "day_profit_pct": -0.349,
        "shares": 200
    },
    {
        "code": "002455",
        "name": "百川股份",
        "market_value": 4323.00,
        "current_price": 14.410,
        "cost_price": 13.117,
        "day_profit": 393.00,
        "day_profit_pct": 10.000,
        "shares": 300
    },
    {
        "code": "002151",
        "name": "恒生科技",
        "market_value": 1708.00,
        "current_price": 0.610,
        "cost_price": 0.607,
        "day_profit": 7.98,
        "day_profit_pct": 0.469,
        "shares": 2800,  # ETF 份额
        "type": "ETF"
    },
]

# 当日清仓
SOLD_TODAY = [
    {
        "code": "002491",
        "name": "通鼎互联",
        "day_profit": -44.07
    }
]

# 账户汇总
"""
证券市值：12411.00 元
当日盈亏：+350.06 元
可取资金：39.08 元
"""
