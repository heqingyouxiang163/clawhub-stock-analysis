# 东方财富实时涨幅榜 Skill

## 用途
获取沪深 A 股实时涨幅榜，支持全市场 5000+ 股票，用于盘中实时监控和盘后统计分析。

## 功能
- 获取全市场实时涨幅排名
- 筛选指定涨幅范围股票
- 涨停股统计
- 沪深主板过滤
- 创业板/科创板过滤

## 安装
```bash
cd ~/.openclaw/workspace/skills
# 自动创建目录
```

## 使用
```python
from eastmoney_rank import get_full_rank, get_rank_range, get_limit_up_stocks

# 获取全市场涨幅榜
stocks = get_full_rank()

# 获取涨幅 5%-7% 的股票
target = get_rank_range(5, 7)

# 获取涨停股
limit_up = get_limit_up_stocks()
```

## 数据源
- 东方财富 API: push2.eastmoney.com
- 新浪财经：hq.sinajs.cn (备用)

## 性能
- 全市场获取：30-60 秒
- 缓存命中：<1ms (2 分钟 TTL)
