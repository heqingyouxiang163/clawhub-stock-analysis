# 快速查询接口

## 用途
快速获取指定股票的实时数据，适用于持仓监控、关注股跟踪等场景。

## 速度
- **100-300ms** 完成查询
- 数据源：腾讯财经 API

## 使用示例

```python
from realtime_monitor import get_realtime_data

# 查询持仓股
codes = ['002342', '603778', '002828']
data = get_realtime_data(codes)

for s in data:
    print(f"{s['code']} {s['name']}: ¥{s['current']:.2f} ({s['change_pct']:+.1f}%)")
```

## 返回格式

```python
[
    {
        'code': '002342',
        'name': '巨力索具',
        'current': 13.48,
        'prev_close': 13.80,
        'change_pct': -2.3,
        'amount': 123456789,
        'turnover': 5.6,
        'timestamp': '2026-03-21 11:55:00'
    },
    ...
]
```

## 注意事项

- 腾讯财经覆盖约 200 只重点股票
- 不在覆盖范围内的股票可能返回空数据
- 建议用于已知在覆盖范围内的股票
