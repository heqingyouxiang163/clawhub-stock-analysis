# 🦞 炒股龙虾系统 - 迁移指南

## 📋 系统要求

### 基础要求
- **操作系统**: Linux / macOS / Windows (WSL)
- **Python**: 3.9+
- **Git**: 2.0+
- **内存**: 至少 2GB
- **磁盘**: 至少 1GB 可用空间

### 可选要求
- **OpenClaw**: 如果需要在 OpenClaw 环境中运行
- **Redis**: 用于数据缓存（可选）

---

## 🚀 快速迁移（推荐）

### 方法 1：一键迁移脚本

```bash
# 下载并运行迁移脚本
curl -o migrate.sh https://raw.githubusercontent.com/heqingyouxiang163/clawhub-stock-analysis/main/migrate.sh
chmod +x migrate.sh
./migrate.sh

# 或者指定安装目录
./migrate.sh /path/to/your/workspace
```

### 方法 2：手动克隆

```bash
# 1. 克隆仓库
git clone https://github.com/heqingyouxiang163/clawhub-stock-analysis.git
cd clawhub-stock-analysis

# 2. 安装依赖
pip3 install -r requirements.txt

# 3. 设置权限
chmod +x tools/*.py skills/*/tools/*.py

# 4. 创建必要目录
mkdir -p temp memory

# 5. 测试运行
python3 tools/高确定性推荐 - 定时任务.py
```

---

## 🔧 详细配置

### 1. 配置 Git 凭证（可选）

如果需要在迁移后推送代码：

```bash
# 配置凭证存储
git config --global credential.helper store

# 第一次推送时会提示输入用户名和密码
# 之后会自动保存
```

### 2. 配置持仓数据

编辑 `tools/持仓配置.py`：

```python
HOLDINGS = [
    {
        "code": "002692",
        "name": "法尔胜",
        "market_value": 2696.00,
        "current_price": 13.480,
        "cost_price": 13.385,
        "day_profit": 19.00,
    },
    # ... 添加你的持仓
]
```

### 3. 配置定时任务

如果使用 OpenClaw：

```bash
# 查看现有任务
openclaw cron list

# 导入任务配置（如果有备份）
openclaw cron import cron-jobs-backup.json
```

### 4. 配置 Python 虚拟环境（可选）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

---

## 📦 依赖说明

### Python 核心依赖

```txt
requests>=2.28.0      # HTTP 请求
pandas>=1.5.0         # 数据处理
numpy>=1.23.0         # 数值计算
akshare>=1.9.0        # A 股数据 (可选)
```

### 系统依赖

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3 python3-pip git

# CentOS/RHEL
sudo yum install -y python3 python3-pip git

# macOS
brew install python3 git
```

---

## 🧪 验证安装

### 测试数据获取

```bash
# 测试腾讯财经数据源
python3 skills/tencent-stock-rank/tencent_stock_rank.py

# 测试高确定性推荐
python3 tools/高确定性推荐 - 定时任务.py

# 测试持仓监控
python3 tools/持仓实时监控.py
```

### 预期输出

```
✅ 成功获取 100 只股票，耗时 98ms
✅ 观察池：91 只 (持仓 + 涨幅榜)
✅ 找到 5 只高确定性股票！
```

---

## ❓ 常见问题

### Q1: Git 克隆失败

**问题**: `fatal: unable to access repository`

**解决**:
```bash
# 检查网络连接
ping github.com

# 使用 HTTPS 代理
git config --global http.proxy http://proxy.example.com:8080

# 或使用 SSH
git clone git@github.com:heqingyouxiang163/clawhub-stock-analysis.git
```

### Q2: Python 依赖安装失败

**问题**: `pip3: command not found`

**解决**:
```bash
# 安装 pip
sudo apt-get install python3-pip  # Ubuntu/Debian
sudo yum install python3-pip      # CentOS
brew install python3              # macOS
```

### Q3: 权限错误

**问题**: `Permission denied`

**解决**:
```bash
# 设置执行权限
chmod +x tools/*.py
chmod +x migrate.sh
```

### Q4: 数据获取失败

**问题**: `Connection aborted`

**解决**:
```bash
# 检查网络连接
curl http://qt.gtimg.cn/q=sh600519

# 检查防火墙
sudo ufw status  # Ubuntu
sudo firewall-cmd --status  # CentOS

# 使用备用数据源（系统会自动切换）
```

---

## 📊 迁移后检查清单

- [ ] Git 仓库克隆成功
- [ ] Python 依赖安装完成
- [ ] 脚本执行权限设置
- [ ] 持仓配置更新
- [ ] 定时任务配置（如使用 OpenClaw）
- [ ] 数据获取测试通过
- [ ] 推荐系统测试通过

---

## 🔄 后续更新

### 从远程仓库同步

```bash
cd clawhub-stock-analysis

# 拉取最新代码
git pull origin main

# 如果有依赖更新
pip3 install -r requirements.txt --upgrade
```

### 查看更新日志

```bash
git log --oneline -10
```

---

## 📞 技术支持

- **GitHub Issues**: https://github.com/heqingyouxiang163/clawhub-stock-analysis/issues
- **仓库地址**: https://github.com/heqingyouxiang163/clawhub-stock-analysis

---

**最后更新**: 2026-03-27  
**版本**: v1.0
