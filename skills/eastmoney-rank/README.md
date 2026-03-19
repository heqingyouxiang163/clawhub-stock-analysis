# 东方财富实时涨幅榜 Skill

## 用途
获取沪深 A 股全市场实时涨幅榜，支持 5000+ 股票，用于盘中实时监控和盘后统计分析。

## 功能
- ✅ 全市场涨幅排名 (东方财富)
- ✅ 实时价格数据 (腾讯财经)
- ✅ 涨幅范围筛选
- ✅ 涨停股统计
- ✅ 市场情绪分析
- ✅ 2 分钟缓存加速

## 安装
技能位置：`/home/admin/openclaw/workspace/skills/eastmoney-rank/`

## 使用
```python
from eastmoney_rank import get_full_rank, get_rank_range, get_market_stats

# 获取全市场涨幅榜
stocks = get_full_rank()

# 获取涨幅 5%-7% 的股票
target = get_rank_range(5, 7)

# 获取市场统计
stats = get_market_stats()
```

## 性能
- 首次获取：1-2 秒
- 缓存命中：<1ms (2 分钟 TTL)
- 覆盖率：95%+ (有价格数据)

## 数据源
- 东方财富 API: push2.eastmoney.com (涨幅排名)
- 腾讯财经 API: qt.gtimg.cn (实时价格)

## 文件
- `eastmoney_rank.py` - 主模块
- `SKILL.md` - 技能文档
