# 🐙 GitHub 账号注册指南

**更新时间**: 2026-03-20 01:21  
**注册邮箱**: heqingyouxiang163@163.com

---

## 📋 注册步骤 (5 分钟)

### 步骤 1: 访问 GitHub 注册页面

**访问**: https://github.com/signup

或者直接访问 https://github.com 然后点击 "Sign up"

---

### 步骤 2: 输入邮箱

在 "Enter your email" 框中输入:
```
heqingyouxiang163@163.com
```

**点击**: "Continue"

---

### 步骤 3: 创建密码

**要求**:
- 至少 15 个字符
- 或者至少 8 个字符，包含数字和小写字母

**示例密码** (请自己修改):
```
Xiaoyi2026@OpenClaw
```

**点击**: "Continue"

---

### 步骤 4: 输入用户名

**用户名建议**:
```
xiaoyi-stock
xiaoyi-trading
heqingyouxiang
xiaoyi-openclaw
```

**注意**:
- 用户名必须唯一
- 只能包含字母、数字、连字符
- 不能以连字符开头或结尾

**点击**: "Continue"

---

### 步骤 5: 邮箱验证

**GitHub 会发送验证邮件到**:
```
heqingyouxiang163@163.com
```

**操作**:
1. 登录 163 邮箱
2. 查找来自 GitHub 的邮件
3. 点击邮件中的验证链接
4. 或者输入邮件中的 6 位验证码

**提示**: 如果没收到邮件，检查垃圾邮件箱

---

### 步骤 6: 回答几个问题 (可选)

GitHub 会问一些问题，可以直接跳过:
- "How do you prefer to work?" → Skip
- "What would you like to do today?" → Skip
- "How many developers..." → Skip

**点击**: "Skip" 或 "Submit"

---

### 步骤 7: 完成！

**恭喜！GitHub 账号已创建！**

**你的账号信息**:
- 用户名：`你设置的用户名`
- 邮箱：`heqingyouxiang163@163.com`
- 仓库：https://github.com/你的用户名

---

## 🔐 安全建议

### 1. 启用双重认证 (2FA)

**强烈建议启用**！

**步骤**:
1. 点击右上角头像 → Settings
2. 左侧菜单：Password and authentication
3. 找到 "Two-factor authentication"
4. 点击 "Enable"
5. 选择验证方式:
   - **推荐**: 使用手机 App (GitHub Mobile, Authy, Google Authenticator)
   - 或者：短信验证

**保存恢复码** (重要！):
- 下载或打印恢复码
- 存放在安全的地方
- 丢失手机时需要恢复码

---

### 2. 添加 SSH 密钥 (推荐)

**步骤**:

**1. 生成 SSH 密钥**:
```bash
ssh-keygen -t ed25519 -C "heqingyouxiang163@163.com"
# 一路回车即可
```

**2. 复制公钥**:
```bash
cat ~/.ssh/id_ed25519.pub
```

**3. 添加到 GitHub**:
1. 访问：https://github.com/settings/keys
2. 点击 "New SSH key"
3. Title: `My Computer`
4. Key: 粘贴刚才复制的公钥
5. 点击 "Add SSH key"

**4. 验证**:
```bash
ssh -T git@github.com
# 第一次会问是否继续，输入 yes
# 看到 "Hi xxx! You've successfully authenticated" 表示成功
```

---

## 📊 注册后下一步

### 1. 创建仓库

**访问**: https://github.com/new

**填写**:
- Repository name: `xiaoyi-system-backup`
- Description: `小艺·炒股龙虾 v17.0 系统备份`
- **Private**: ✅ (勾选，私有仓库)
- 其他：不勾选

**点击**: "Create repository"

**复制仓库 URL**:
```
https://github.com/你的用户名/xiaoyi-system-backup.git
```

---

### 2. 关联本地仓库

```bash
cd /home/admin/openclaw/workspace

# 替换 "你的用户名" 为你的实际 GitHub 用户名
git remote add origin https://github.com/你的用户名/xiaoyi-system-backup.git

# 验证
git remote -v
```

---

### 3. 推送到 GitHub

```bash
# 设置主分支
git branch -M main

# 首次推送
git push -u origin main

# 验证
git status
```

---

## 📞 常见问题

### Q1: 邮箱已被注册？

**A**: 如果你之前注册过 GitHub，可以直接登录:
```
https://github.com/login
```

或者使用其他邮箱重新注册。

---

### Q2: 用户名已被占用？

**A**: 尝试其他用户名:
```
xiaoyi-stock-2026
heqingyouxiang-stock
xiaoyi-trading-system
openclaw-xiaoyi
```

---

### Q3: 收不到验证邮件？

**A**: 
1. 检查垃圾邮件箱
2. 等待 5-10 分钟
3. 点击 "Resend email" 重新发送
4. 检查邮箱地址是否正确

---

### Q4: 忘记密码怎么办？

**A**: 
1. 访问：https://github.com/password_reset
2. 输入邮箱：heqingyouxiang163@163.com
3. 点击 "Send reset email"
4. 检查邮箱，点击重置链接

---

### Q5: 如何切换账号？

**A**: 
1. 点击右上角头像
2. 点击 "Sign out" 退出
3. 重新登录其他账号

---

## ✅ 注册检查清单

- [ ] 访问 https://github.com/signup
- [ ] 输入邮箱：heqingyouxiang163@163.com
- [ ] 设置密码 (至少 15 字符)
- [ ] 设置用户名 (如：xiaoyi-stock)
- [ ] 验证邮箱 (检查 163 邮箱)
- [ ] 启用双重认证 (推荐)
- [ ] 添加 SSH 密钥 (推荐)
- [ ] 创建仓库：xiaoyi-system-backup
- [ ] 设置为 Private (私有)
- [ ] 复制仓库 URL
- [ ] 关联本地仓库
- [ ] 推送到 GitHub

---

## 🎯 快速命令参考

```bash
# 查看当前 Git 用户
git config user.name
git config user.email

# 配置 Git 用户
git config --global user.name "小艺·炒股龙虾"
git config --global user.email "heqingyouxiang163@163.com"

# 关联远程仓库
git remote add origin https://github.com/你的用户名/xiaoyi-system-backup.git

# 推送
git push -u origin main

# 拉取
git pull origin main

# 查看状态
git status
```

---

## 📖 相关文档

- **备份指南**: `read Git 备份指南.md`
- **快速备份**: `read Git 快速备份.md`
- **恢复指南**: `read Git 恢复指南.md`
- **开始备份**: `read 开始备份.md`

---

**现在开始注册吧！注册完成后告诉我你的用户名！** 🦞✨
