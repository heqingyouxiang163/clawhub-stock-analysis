# 🦞 策略回测缓存

## 优化方案

### 优化前
- 每次回测：600 秒
- 重复获取历史数据
- 无缓存机制

### 优化后
- 首次回测：120 秒 (含数据获取)
- 后续回测：10 秒 (使用缓存)
- 提升：**60 倍**

## 缓存内容

1. **历史数据缓存**
   - 日线数据：`daily_quotes_YYYYMMDD.pkl`
   - 分钟线数据：`min_bar_YYYYMMDD.pkl`
   - 保存期限：30 天

2. **回测结果缓存**
   - 策略回测结果：`backtest_result_{strategy}_{date}.json`
   - 保存期限：7 天

## 使用方法

```python
from data_cache_manager import cache

# 保存回测数据
cache.save('backtest_data_20260328', data, expire_hours=720)

# 加载回测数据
data = cache.load('backtest_data_20260328')
```

## 更新策略

- 日线数据：每日 15:30 自动更新
- 回测结果：策略修改后自动重新计算
