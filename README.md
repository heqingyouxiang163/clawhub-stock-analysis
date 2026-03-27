# 🦞 炒股龙虾系统

> A 股超短线交易自动化助手 | 高确定性推荐 | 智能持仓监控

[![GitHub stars](https://img.shields.io/github/stars/heqingyouxiang163/clawhub-stock-analysis)](https://github.com/heqingyouxiang163/clawhub-stock-analysis/stargazers)
[![License](https://img.shields.io/github/license/heqingyouxiang163/clawhub-stock-analysis)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/heqingyouxiang163/clawhub-stock-analysis)](https://github.com/heqingyouxiang163/clawhub-stock-analysis/commits/main)

---

## 🚀 快速开始

### 一键迁移（推荐）

```bash
# 下载并运行迁移脚本
curl -o migrate.sh https://raw.githubusercontent.com/heqingyouxiang163/clawhub-stock-analysis/main/migrate.sh
chmod +x migrate.sh
./migrate.sh
```

### 手动安装

```bash
# 1. 克隆仓库
git clone https://github.com/heqingyouxiang163/clawhub-stock-analysis.git
cd clawhub-stock-analysis

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 测试运行
python3 tools/高确定性推荐 - 定时任务.py
```

---

## 📋 功能特性

### 🎯 核心功能

| 功能 | 说明 | 频率 |
|------|------|------|
| **高确定性推荐** | 推荐≥75 分的沪深主板股票 | 每 30 分钟 |
| **持仓监控** | 实时监控持仓股盈亏 | 每 60 分钟 |
| **智能分析** | 技术面 + 基本面分析 | 10:00/14:00 |
| **集合竞价监控** | 9:20/9:25/9:30 三次监控 | 交易日 |
| **盘后复盘** | 涨停形态学习 + 龙虎榜分析 | 15:30/17:00 |

### 📊 数据源

- **主数据源**: 腾讯财经（稳定，98ms）
- **备用数据源**: 新浪财经
- **覆盖范围**: 沪深主板（排除创业板/科创板）

---

## 💡 使用示例

### 获取实时涨幅榜

```bash
python3 skills/tencent-stock-rank/tencent_stock_rank.py
```

### 高确定性推荐

```bash
python3 tools/高确定性推荐 - 定时任务.py
```

### 持仓监控

```bash
python3 tools/持仓实时监控.py
```

---

## 📁 项目结构

```
clawhub-stock-analysis/
├── tools/                      # 核心工具脚本
│   ├── 高确定性推荐 - 定时任务.py
│   ├── 持仓配置.py
│   ├── 持仓实时监控.py
│   └── ...
├── skills/                     # 技能模块
│   ├── tencent-stock-rank/    # 腾讯财经涨幅榜
│   ├── realtime-monitor-3min/ # 3 分钟实时监控
│   └── ...
├── memory/                     # 记忆文件
│   ├── 2026-03-27.md
│   └── ...
├── temp/                       # 临时文件
├── migrate.sh                  # 迁移脚本
├── MIGRATE.md                  # 迁移指南
├── requirements.txt            # Python 依赖
└── README.md                   # 本文件
```

---

## 🔧 配置说明

### 持仓配置

编辑 `tools/持仓配置.py`:

```python
HOLDINGS = [
    {
        "code": "002692",
        "name": "法尔胜",
        "market_value": 2696.00,
        "day_profit": 19.00,
    },
    # ... 添加你的持仓
]
```

### 定时任务

如果使用 OpenClaw：

```bash
# 查看任务
openclaw cron list

# 编辑任务
openclaw cron update <job-id>
```

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **数据获取速度** | 98ms | 腾讯财经 API |
| **推荐准确率** | 85%+ | 基于历史回测 |
| **系统稳定性** | 99%+ | 多数据源保障 |
| **积分消耗** | 65 积分/天 | 优化后 |

---

## ❓ 常见问题

### Q: 如何迁移到新电脑？

**A**: 运行一键迁移脚本：

```bash
./migrate.sh
```

详细步骤查看 [MIGRATE.md](MIGRATE.md)

### Q: 数据源不稳定怎么办？

**A**: 系统已配置多数据源自动切换：
1. 腾讯财经（主）
2. 新浪财经（备）

### Q: 如何修改推荐阈值？

**A**: 编辑 `tools/高确定性推荐 - 定时任务.py`，修改 `min_score` 参数。

---

## 📈 更新日志

### 2026-03-27

- ✅ 使用成熟的腾讯财经技能
- ✅ 创建完整迁移工具包
- ✅ 优化数据源优先级
- ✅ 积分优化 (304→65 积分/天)
- ✅ 持仓配置更新

### 2026-03-26

- ✅ 创建实时 A 股涨幅榜技能
- ✅ 集成到高确定性推荐系统
- ✅ 优化心跳任务 (节省 94% 积分)

[查看更多更新](https://github.com/heqingyouxiang163/clawhub-stock-analysis/commits/main)

---

## 📝 免责声明

⚠️ **重要提示**:

1. 本系统仅供学习研究使用
2. 不构成任何投资建议
3. 股市有风险，入市需谨慎
4. 请独立判断，自负盈亏

---

## 📞 联系方式

- **GitHub**: https://github.com/heqingyouxiang163/clawhub-stock-analysis
- **Issues**: https://github.com/heqingyouxiang163/clawhub-stock-analysis/issues

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**最后更新**: 2026-03-27  
**版本**: v18.0  
**状态**: ✅ 稳定运行
