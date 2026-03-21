# 全市场扫描接口

## 用途
获取全市场 5000+ 只股票的实时涨幅排名，适用于选股、市场情绪分析等场景。

## 速度
- **60-120 秒** 完成全市场扫描
- 数据源：东方财富 (涨幅排名) + 腾讯财经 (价格数据)

## 使用示例

### 获取全市场涨幅榜

```python
from realtime_monitor import get_full_market_scan

stocks = get_full_market_scan()
print(f"全市场共{len(stocks)}只股票")

# 显示前 10 名
for s in stocks[:10]:
    print(f"{s['code']} {s['name']}: +{s['change_pct']:.1f}%")
```

### 筛选指定涨幅范围

```python
from realtime_monitor import get_stocks_in_range

# 主升浪股票 (5-8%)
rising = get_stocks_in_range(5, 8)
print(f"主升浪股票：{len(rising)}只")
```

### 获取涨停股

```python
from realtime_monitor import get_limit_up_stocks

limit_up = get_limit_up_stocks()
print(f"今日涨停：{len(limit_up)}只")
```

## 返回格式

```python
[
    {
        'code': '600569',
        'name': '安阳钢铁',
        'current': 2.82,
        'change_pct': 10.2,
        'open': 2.56,
        'high': 2.82,
        'low': 2.56,
        'prev_close': 2.56,
        'amount': 123456789,
        'turnover': 8.5,
        'timestamp': '2026-03-21 11:55:00'
    },
    ...
]
```

## 缓存机制

- 默认缓存 **3 分钟**
- 可强制刷新：`get_full_market_scan(use_cache=False)`

## 注意事项

- 全市场扫描较慢，建议使用缓存
- 部分股票可能没有价格数据 (腾讯财经未覆盖)
- 数据有 15 分钟延迟
