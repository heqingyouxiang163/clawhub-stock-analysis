# 🦞 Git 快速备份指南

**更新时间**: 2026-03-20 01:09

---

## 🚀 快速开始 (5 分钟完成)

### 步骤 1: 创建 GitHub 仓库 (2 分钟)

1. 登录 https://github.com
2. 点击右上角 "+" → "New repository"
3. 填写:
   - Repository name: `xiaoyi-system-backup`
   - 选择：**Private** (私有)
4. 点击 "Create repository"
5. 复制仓库 URL (例如：`https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git`)

### 步骤 2: 关联仓库 (1 分钟)

```bash
cd /home/admin/openclaw/workspace
git remote add origin https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git
git remote -v  # 验证
```

### 步骤 3: 推送备份 (2 分钟)

```bash
# 首次推送
git branch -M main
git push -u origin main

# 验证
git status
```

**完成！** ✅ 系统已备份到 GitHub

---

## 🔄 日常备份

### 手动备份

```bash
cd /home/admin/openclaw/workspace
./自动备份.sh
```

### 自动备份 (推荐)

**每日凌晨 2 点自动备份**:

```bash
# 编辑 crontab
crontab -e

# 添加以下行
0 2 * * * cd /home/admin/openclaw/workspace && ./自动备份.sh
```

---

## 📥 恢复方法

### 从 GitHub 恢复

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git /tmp/xiaoyi-restore

# 2. 复制文件
cp -r /tmp/xiaoyi-restore/* /home/admin/openclaw/workspace/

# 3. 验证
ls /home/admin/openclaw/workspace/系统文档/
```

---

## 🔐 使用 SSH 密钥 (推荐)

### 生成 SSH 密钥

```bash
ssh-keygen -t ed25519 -C "xiaoyi@openclaw.local"
# 一路回车即可
```

### 添加到 GitHub

1. 复制公钥：
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

2. 登录 GitHub → Settings → SSH and GPG keys → New SSH key

3. 粘贴公钥，保存

### 切换到 SSH URL

```bash
git remote set-url origin git@github.com:YOUR_USERNAME/xiaoyi-system-backup.git
git remote -v  # 验证
```

---

## 📊 三地备份 (最佳实践)

### 推荐方案

| 平台 | URL | 用途 |
|------|-----|------|
| GitHub | https://github.com | 主备份 |
| GitLab | https://gitlab.com | 备份 1 |
| Gitee | https://gitee.com | 备份 2 (国内) |

### 关联所有仓库

```bash
cd /home/admin/openclaw/workspace

# GitHub (主)
git remote add origin https://github.com/YOUR_USERNAME/xiaoyi-system-backup.git

# GitLab (备份 1)
git remote add gitlab https://gitlab.com/YOUR_USERNAME/xiaoyi-system-backup.git

# Gitee (备份 2)
git remote add gitee https://gitee.com/YOUR_USERNAME/xiaoyi-system-backup.git

# 验证
git remote -v
```

### 推送到所有仓库

```bash
# 推送到所有远程
git push origin main
git push gitlab main
git push gitee main
```

**自动备份脚本会自动推送到所有仓库！** ✅

---

## ⚠️ 注意事项

### 不要提交的文件

**已配置 .gitignore 自动忽略**:
- ✅ temp/ 临时文件
- ✅ *.log 日志文件
- ✅ *.pyc Python 缓存
- ✅ *.key 密钥文件
- ✅ .env 环境变量

### 仓库大小限制

| 平台 | 单文件限制 | 仓库限制 |
|------|-----------|---------|
| GitHub | 100MB | 1GB |
| GitLab | 100MB | 无限 |
| Gitee | 100MB | 1GB |

**如果文件太大**:
```bash
# 查看大文件
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {if ($3 > 10485760) print $3/1024/1024 "MB " $4}'

# 使用 Git LFS
git lfs install
git lfs track "*.zip"
```

---

## 📞 常见问题

### Q1: 推送失败 "Permission denied"

**A**: 认证问题
```bash
# 使用 HTTPS
git config --global credential.helper store
git push

# 或使用 SSH
git remote set-url origin git@github.com:YOUR_USERNAME/xiaoyi-system-backup.git
git push
```

### Q2: 如何查看备份历史？

**A**: 
```bash
# 查看提交历史
git log --oneline

# 查看文件变化
git diff HEAD~1 HEAD
```

### Q3: 如何恢复特定版本？

**A**:
```bash
# 查看历史版本
git log --oneline

# 恢复到特定版本
git checkout COMMIT_HASH

# 或创建新分支
git checkout -b backup-2026-03-20 COMMIT_HASH
```

---

## ✅ 检查清单

### 首次备份

- [ ] 创建 GitHub 仓库
- [ ] 关联远程仓库
- [ ] 推送到 GitHub
- [ ] 验证推送成功

### 日常备份

- [ ] 设置自动备份 (crontab)
- [ ] 验证自动备份运行
- [ ] 定期检查 GitHub 仓库

### 安全配置

- [ ] 使用私有仓库
- [ ] 配置 SSH 密钥
- [ ] 不提交敏感信息

---

**备份完成！系统安全有保障！** 🦞✨
