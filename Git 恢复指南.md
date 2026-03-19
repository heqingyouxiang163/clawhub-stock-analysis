# 🦞 从 Git 仓库恢复系统指南

**更新时间**: 2026-03-20 01:13  
**适用场景**: 在其他电脑上恢复系统

---

## 📋 目录

1. [GitHub 恢复](#github-恢复)
2. [GitLab 恢复](#gitlab-恢复)
3. [Gitee 恢复 (国内)](#gitee-恢复国内)
4. [恢复后配置](#恢复后配置)
5. [验证恢复](#验证恢复)
6. [常见问题](#常见问题)

---

## 🐙 GitHub 恢复

### 步骤 1: 安装 Git

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install git
git --version
```

**macOS**:
```bash
# 安装 Xcode 命令行工具
xcode-select --install
git --version
```

**Windows**:
```
下载：https://gitforwindows.org/
安装后打开 Git Bash
```

### 步骤 2: 克隆仓库

```bash
# 创建目录
mkdir -p ~/openclaw
cd ~/openclaw

# 克隆仓库 (替换为你的 GitHub 用户名)
git clone https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git workspace

# 进入工作目录
cd workspace

# 验证文件
ls -la
```

### 步骤 3: 验证恢复

```bash
# 检查关键文件
ls 系统文档/
ls tools/
ls memory/

# 查看 MEMORY.md
head -20 MEMORY.md
```

---

## 🦊 GitLab 恢复

### 步骤 1: 克隆仓库

```bash
mkdir -p ~/openclaw
cd ~/openclaw

# 从 GitLab 克隆
git clone https://gitlab.com/YOUR_USERNAME/xiaoyi-system-backup.git workspace

cd workspace
```

### 步骤 2: 验证恢复

```bash
ls -la
git log --oneline
```

---

## 🇨🇳 Gitee 恢复 (国内)

### 步骤 1: 克隆仓库

```bash
mkdir -p ~/openclaw
cd ~/openclaw

# 从 Gitee 克隆 (国内访问快)
git clone https://gitee.com/YOUR_USERNAME/xiaoyi-system-backup.git workspace

cd workspace
```

### 步骤 2: 验证恢复

```bash
ls -la
git log --oneline
```

---

## 🔧 恢复后配置

### 1️⃣ 配置 Git 用户信息

```bash
cd ~/openclaw/workspace

git config --global user.email "xiaoyi@openclaw.local"
git config --global user.name "小艺·炒股龙虾"
```

### 2️⃣ 配置 OpenClaw 环境

```bash
# 检查 OpenClaw 是否已安装
openclaw --version

# 如果未安装，需要安装 OpenClaw
# 参考：https://docs.openclaw.ai
```

### 3️⃣ 恢复定时任务配置

```bash
# 检查 cron 配置
openclaw cron list

# 如果配置丢失，需要重新导入
# 从备份的 cron 配置恢复
```

### 4️⃣ 验证工具脚本

```bash
# 测试脚本执行
cd ~/openclaw/workspace/tools
python3 定时任务全自动化监控.py --help
```

---

## ✅ 验证恢复

### 完整验证清单

```bash
cd ~/openclaw/workspace

echo "=== 验证文件结构 ==="
ls -la 系统文档/
ls -la tools/ | head -10
ls -la memory/

echo ""
echo "=== 验证关键文件 ==="
test -f MEMORY.md && echo "✅ MEMORY.md 存在" || echo "❌ MEMORY.md 缺失"
test -f USER.md && echo "✅ USER.md 存在" || echo "❌ USER.md 缺失"
test -f HEARTBEAT.md && echo "✅ HEARTBEAT.md 存在" || echo "❌ HEARTBEAT.md 缺失"

echo ""
echo "=== 验证 Git 状态 ==="
git status
git log --oneline | head -5

echo ""
echo "=== 验证系统文档 ==="
head -30 系统文档/README-系统完整文档.md
```

### 预期输出

```
=== 验证文件结构 ===
✅ 系统文档/存在
✅ tools/存在 (30+ 个文件)
✅ memory/存在

=== 验证关键文件 ===
✅ MEMORY.md 存在
✅ USER.md 存在
✅ HEARTBEAT.md 存在

=== 验证 Git 状态 ===
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean

=== 验证系统文档 ===
# 🦞 小艺·炒股龙虾 v17.0 - 系统完整文档
...
```

---

## 🔄 从备份更新

### 拉取最新备份

```bash
cd ~/openclaw/workspace

# 拉取最新代码
git pull origin main

# 查看更新
git log --oneline -5

# 验证更新
git status
```

### 解决冲突

```bash
# 如果有冲突
git status  # 查看冲突文件

# 手动解决冲突后
git add <文件名>
git commit -m "解决冲突"
git push origin main
```

---

## 📊 多设备同步

### 设备 A (主设备)

```bash
# 修改后提交
cd ~/openclaw/workspace
git add -A
git commit -m "🦞 更新配置"
git push origin main
```

### 设备 B (其他设备)

```bash
# 拉取更新
cd ~/openclaw/workspace
git pull origin main
```

### 自动同步脚本

**文件**: `~/openclaw/workspace/同步到云端.sh`

```bash
#!/bin/bash

# 同步到 Git 仓库
cd ~/openclaw/workspace

echo "🦞 开始同步..."

# 添加变更
git add -A

# 检查是否有变化
if git diff --staged --quiet; then
    echo "✅ 无变化，已是最新"
else
    # 提交
    git commit -m "🦞 同步 $(date +'%Y-%m-%d %H:%M')"
    
    # 推送
    git push origin main
    
    echo "✅ 同步完成！"
fi
```

**使用方法**:
```bash
chmod +x ~/openclaw/workspace/同步到云端.sh
./同步到云端.sh
```

---

## 📞 常见问题

### Q1: 克隆失败 "Repository not found"

**A**: 检查仓库名和权限
```bash
# 检查仓库是否存在
# 访问：https://github.com/YOUR_USERNAME/xiaoyi-system-backup

# 如果是私有仓库，需要认证
git clone https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git
# 输入 GitHub 用户名和密码
```

### Q2: 克隆失败 "Permission denied"

**A**: 使用 SSH 密钥
```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥
cat ~/.ssh/id_ed25519.pub

# 添加到 GitHub: Settings → SSH and GPG keys

# 使用 SSH URL 克隆
git clone git@github.com:YOUR_USERNAME/xiaoyi-system-backup.git
```

### Q3: 恢复后工具脚本无法执行

**A**: 添加执行权限
```bash
cd ~/openclaw/workspace/tools
chmod +x *.py
```

### Q4: 恢复后定时任务丢失

**A**: 重新导入定时任务
```bash
# 检查 cron 配置
openclaw cron list

# 如果配置在备份中
# 从备份的 cron 配置恢复
```

### Q5: 如何在多个设备间保持同步？

**A**: 使用自动同步
```bash
# 设备 A (修改后)
./同步到云端.sh

# 设备 B (拉取更新)
cd ~/openclaw/workspace
git pull origin main
```

---

## 🎯 最佳实践

### 1. 使用 SSH 密钥

```bash
# 生成密钥
ssh-keygen -t ed25519 -C "xiaoyi@openclaw.local"

# 添加到所有 Git 平台
# GitHub: Settings → SSH and GPG keys
# GitLab: Settings → SSH Keys
# Gitee: 设置 → 安全设置 → SSH 公钥
```

### 2. 设置自动同步

```bash
# 编辑 crontab
crontab -e

# 每小时自动同步
0 * * * * cd ~/openclaw/workspace && git pull origin main
```

### 3. 使用分支管理

```bash
# 主分支：main (稳定版本)
# 开发分支：dev (开发中)

# 创建开发分支
git checkout -b dev

# 切换回主分支
git checkout main
```

### 4. 定期备份

```bash
# 每周日自动备份
crontab -e
0 23 * * 0 cd ~/openclaw/workspace && ./自动备份.sh
```

---

## 📋 完整恢复流程

### 新电脑恢复步骤

```bash
# 1. 安装 Git
sudo apt install git  # Ubuntu/Debian

# 2. 配置 Git
git config --global user.email "xiaoyi@openclaw.local"
git config --global user.name "小艺·炒股龙虾"

# 3. 创建目录
mkdir -p ~/openclaw
cd ~/openclaw

# 4. 克隆仓库
git clone https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git workspace

# 5. 进入工作目录
cd workspace

# 6. 验证恢复
ls -la
./自动备份.sh  # 测试脚本

# 7. 配置 OpenClaw (如果未安装)
# 参考：https://docs.openclaw.ai

# 8. 验证系统
openclaw gateway status
openclaw cron list

echo "✅ 恢复完成！"
```

---

## ✅ 恢复检查清单

### 基础检查

- [ ] Git 已安装
- [ ] 仓库已克隆
- [ ] 文件完整
- [ ] Git 配置正确

### 功能检查

- [ ] 工具脚本可执行
- [ ] 系统文档可读
- [ ] MEMORY.md 完整
- [ ] 定时任务配置存在

### 同步检查

- [ ] 可以 pull 最新代码
- [ ] 可以 push 修改
- [ ] SSH 密钥配置 (可选)
- [ ] 自动同步设置 (可选)

---

**恢复完成！多设备同步无忧！** 🦞✨
