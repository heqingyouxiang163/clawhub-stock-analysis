# 🦞 Git 仓库备份指南

**创建时间**: 2026-03-20 01:09  
**系统版本**: v17.0

---

## 📋 目录

1. [GitHub 备份](#github-备份)
2. [GitLab 备份](#gitlab-备份)
3. [Gitee 备份 (国内)](#gitee-备份国内)
4. [自动备份脚本](#自动备份脚本)
5. [恢复方法](#恢复方法)

---

## 🐙 GitHub 备份

### 步骤 1: 创建 GitHub 仓库

1. 登录 https://github.com
2. 点击右上角 "+" → "New repository"
3. 填写仓库名：`xiaoyi-system-backup`
4. 选择 "Private" (私有仓库)
5. 点击 "Create repository"

### 步骤 2: 关联远程仓库

```bash
# 进入工作目录
cd /home/admin/openclaw/workspace

# 添加远程仓库 (替换为你的 GitHub 用户名)
git remote add origin https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git

# 验证
git remote -v
```

### 步骤 3: 推送到 GitHub

```bash
# 推送主分支
git branch -M main
git push -u origin main

# 验证
git status
```

### 步骤 4: 设置自动同步 (可选)

**创建定时任务** (每周日 23:00 自动推送):

```bash
# 编辑 crontab
crontab -e

# 添加以下行
0 23 * * 0 cd /home/admin/openclaw/workspace && git add -A && git commit -m "🦞 自动备份 $(date +'%Y-%m-%d')" && git push origin main
```

---

## 🦊 GitLab 备份

### 步骤 1: 创建 GitLab 仓库

1. 登录 https://gitlab.com
2. 点击 "New project"
3. 填写项目名：`xiaoyi-system-backup`
4. 选择 "Private"
5. 点击 "Create project"

### 步骤 2: 关联远程仓库

```bash
cd /home/admin/openclaw/workspace

# 添加 GitLab 远程仓库
git remote add gitlab https://gitlab.com/YOUR_USERNAME/xiaoyi-system-backup.git

# 验证
git remote -v
```

### 步骤 3: 推送到 GitLab

```bash
git push -u gitlab main
```

---

## 🇨🇳 Gitee 备份 (国内)

### 步骤 1: 创建 Gitee 仓库

1. 登录 https://gitee.com
2. 点击右上角 "+" → "新建仓库"
3. 填写仓库名：`xiaoyi-system-backup`
4. 选择 "私有"
5. 点击 "创建"

### 步骤 2: 关联远程仓库

```bash
cd /home/admin/openclaw/workspace

# 添加 Gitee 远程仓库
git remote add gitee https://gitee.com/YOUR_USERNAME/xiaoyi-system-backup.git

# 验证
git remote -v
```

### 步骤 3: 推送到 Gitee

```bash
git push -u gitee main
```

---

## 🔄 自动备份脚本

### 创建备份脚本

**文件**: `/home/admin/openclaw/workspace/自动备份.sh`

```bash
#!/bin/bash

# 小艺系统自动备份脚本
# 用法：./自动备份.sh [commit_message]

cd /home/admin/openclaw/workspace

# 添加所有文件
git add -A

# 检查是否有变化
if git diff --staged --quiet; then
    echo "✅ 无变化，跳过备份"
    exit 0
fi

# 提交变化
MESSAGE="${1:-🦞 自动备份 $(date +'%Y-%m-%d %H:%M')}"
git commit -m "$MESSAGE"

# 推送到所有远程仓库
echo "📤 推送到 GitHub..."
git push origin main 2>&1 | grep -E "Updating|error"

echo "📤 推送到 GitLab..."
git push gitlab main 2>&1 | grep -E "Updating|error"

echo "📤 推送到 Gitee..."
git push gitee main 2>&1 | grep -E "Updating|error"

echo "✅ 备份完成！"
```

**使用方法**:
```bash
# 添加执行权限
chmod +x /home/admin/openclaw/workspace/自动备份.sh

# 手动执行
./自动备份.sh

# 带自定义消息
./自动备份.sh "🦞 手动备份 - 重要配置更新"
```

### 设置定时任务

```bash
# 编辑 crontab
crontab -e

# 每日凌晨 2 点自动备份
0 2 * * * /home/admin/openclaw/workspace/自动备份.sh

# 每周日 23:00 自动备份
0 23 * * 0 /home/admin/openclaw/workspace/自动备份.sh
```

---

## 📥 恢复方法

### 从 GitHub 恢复

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git /tmp/xiaoyi-restore

# 2. 复制文件到工作目录
cp -r /tmp/xiaoyi-restore/* /home/admin/openclaw/workspace/

# 3. 验证
ls /home/admin/openclaw/workspace/系统文档/
```

### 从 GitLab 恢复

```bash
git clone https://gitlab.com/YOUR_USERNAME/xiaoyi-system-backup.git /tmp/xiaoyi-restore
# 后续步骤同上
```

### 从 Gitee 恢复

```bash
git clone https://gitee.com/YOUR_USERNAME/xiaoyi-system-backup.git /tmp/xiaoyi-restore
# 后续步骤同上
```

---

## 🔐 安全建议

### 1. 使用 SSH 密钥 (推荐)

**生成 SSH 密钥**:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

**添加到 GitHub/GitLab/Gitee**:
1. 复制公钥：`cat ~/.ssh/id_ed25519.pub`
2. 登录 GitHub/GitLab/Gitee
3. 设置 → SSH Keys → 添加公钥

**使用 SSH  URL**:
```bash
# GitHub
git remote set-url origin git@github.com:YOUR_USERNAME/xiaoyi-system-backup.git

# GitLab
git remote set-url gitlab git@gitlab.com:YOUR_USERNAME/xiaoyi-system-backup.git

# Gitee
git remote set-url gitee git@gitee.com:YOUR_USERNAME/xiaoyi-system-backup.git
```

### 2. 不要提交敏感信息

**已配置 .gitignore 忽略**:
- ✅ `*.key` - 密钥文件
- ✅ `*.secret` - 机密文件
- ✅ `.env` - 环境变量
- ✅ `temp/` - 临时文件
- ✅ `*.log` - 日志文件

### 3. 使用私有仓库

**强烈建议**:
- ✅ 选择 "Private" (私有仓库)
- ✅ 只添加信任的协作者
- ✅ 定期更换访问令牌

---

## 📊 备份检查清单

### 首次备份

- [ ] 创建 Git 仓库 (GitHub/GitLab/Gitee)
- [ ] 初始化本地仓库 (`git init`)
- [ ] 创建 .gitignore
- [ ] 添加所有文件 (`git add -A`)
- [ ] 创建初始提交 (`git commit`)
- [ ] 关联远程仓库 (`git remote add`)
- [ ] 推送到远程 (`git push`)
- [ ] 验证推送成功

### 日常备份

- [ ] 设置自动备份脚本
- [ ] 设置定时任务 (cron)
- [ ] 验证自动备份运行
- [ ] 定期检查远程仓库

### 恢复测试

- [ ] 测试从 GitHub 恢复
- [ ] 测试从 GitLab 恢复
- [ ] 测试从 Gitee 恢复
- [ ] 验证恢复后系统正常

---

## 🎯 推荐方案

### 最佳实践

**推荐**: **三地备份** (GitHub + GitLab + Gitee)

**优点**:
- ✅ GitHub: 全球最大，稳定可靠
- ✅ GitLab: 免费私有仓库 unlimited
- ✅ Gitee: 国内访问快，备份容灾

**推送顺序**:
```bash
# 主仓库：GitHub
git push origin main

# 备份 1: GitLab
git push gitlab main

# 备份 2: Gitee
git push gitee main
```

### 备份频率

| 类型 | 频率 | 说明 |
|------|------|------|
| 自动备份 | 每日 2:00 | 增量备份 |
| 完整备份 | 每周日 23:00 | 完整提交 |
| 手动备份 | 重大变更后 | 立即备份 |

---

## 📞 常见问题

### Q1: 推送失败怎么办？

**A**: 检查网络和认证
```bash
# 检查网络
ping github.com

# 检查认证
git config --global credential.helper store

# 重新推送
git push -u origin main
```

### Q2: 仓库太大怎么办？

**A**: 使用 Git LFS 或排除大文件
```bash
# 安装 Git LFS
git lfs install

# 跟踪大文件
git lfs track "*.zip"
git lfs track "*.tar.gz"
```

### Q3: 如何查看备份历史？

**A**: 查看 Git 日志
```bash
# 查看提交历史
git log --oneline

# 查看文件变化
git diff HEAD~1 HEAD
```

---

**备份完成！系统安全有保障！** 🦞✨
