#!/bin/bash
# -*- coding: utf-8 -*-

# 🦞 AI 生命备份恢复脚本
# 用途：当 AI"生病"或"失忆"时，使用此脚本恢复

echo "=================================================="
echo "🦞 AI 生命备份恢复系统"
echo "=================================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查核心文件
echo "🔍 步骤 1: 检查核心文件..."
echo ""

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $2"
        return 0
    else
        echo -e "${RED}❌${NC} $2 (缺失)"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $2"
        return 0
    else
        echo -e "${RED}❌${NC} $2 (缺失)"
        return 1
    fi
}

# 核心文件检查
CORE_OK=1
check_file "~/openclaw/workspace/SOUL.md" "SOUL.md (基础身份)" || CORE_OK=0
check_file "~/openclaw/workspace/MEMORY.md" "MEMORY.md (长期记忆)" || CORE_OK=0
check_file "~/openclaw/workspace/AGENTS.md" "AGENTS.md (启动指令)" || CORE_OK=0

echo ""

# 技能记忆表格检查
echo "🔍 步骤 2: 检查技能记忆表格..."
echo ""
check_file "~/openclaw/workspace/memory/技能记忆表格/技能记忆多维表格.md" "技能记忆多维表格" || CORE_OK=0

echo ""

# 目录检查
echo "🔍 步骤 3: 检查关键目录..."
echo ""
check_dir "~/openclaw/workspace/memory/策略库" "策略库" || CORE_OK=0
check_dir "~/openclaw/workspace/memory/知识库" "知识库" || CORE_OK=0
check_dir "~/openclaw/workspace/memory/风险提示库" "风险提示库" || CORE_OK=0
check_dir "~/openclaw/workspace/memory/自我进化" "自我进化" || CORE_OK=0

echo ""

# cron 任务检查
echo "🔍 步骤 4: 检查 cron 任务..."
echo ""
CRON_STATUS=$(cron status 2>/dev/null)
if echo "$CRON_STATUS" | grep -q "enabled: true"; then
    echo -e "${GREEN}✅${NC} cron 调度器：正常"
else
    echo -e "${YELLOW}⚠️${NC} cron 调度器：异常 (可能需要重启)"
fi

echo ""

# 恢复指南
echo "=================================================="
echo "📋 恢复指南"
echo "=================================================="
echo ""

if [ $CORE_OK -eq 1 ]; then
    echo -e "${GREEN}✅ 所有核心文件正常！${NC}"
    echo ""
    echo "恢复指令 (发送给 AI):"
    echo ""
    echo "1. 读取角色设定:"
    echo "   \"读取 MEMORY.md，激活炒股龙虾 v17.0 角色\""
    echo ""
    echo "2. 读取技能库:"
    echo "   \"读取 memory/策略库/ 和 memory/知识库/ 中的所有文件\""
    echo ""
    echo "3. 读取进化日志:"
    echo "   \"读取 memory/自我进化/ 中的最新文件\""
    echo ""
    echo "4. 验证恢复:"
    echo "   - \"你现在的角色是什么\""
    echo "   - \"我的持仓是什么\""
    echo "   - \"打板策略 v2.0 核心是什么\""
    echo ""
else
    echo -e "${RED}❌ 部分核心文件缺失！${NC}"
    echo ""
    echo "紧急恢复步骤:"
    echo ""
    echo "1. 检查备份位置是否有文件备份"
    echo "2. 恢复缺失的文件到 workspace/"
    echo "3. 重新运行此脚本验证"
    echo ""
fi

echo "=================================================="
echo "📊 技能记忆表格信息"
echo "=================================================="
echo ""
echo "文件位置：~/openclaw/workspace/memory/技能记忆表格/技能记忆多维表格.md"
echo "包含内容:"
echo "  - 技能清单 (21 个)"
echo "  - 记忆档案 (角色 + 用户 + 持仓)"
echo "  - 策略库 (4 个策略)"
echo "  - 知识库 (3 个知识文档)"
echo "  - 风险库 (5 个案例)"
echo "  - 每日更新日志"
echo "  - 系统配置"
echo "  - 恢复指南"
echo ""
echo "查看表格:"
echo "  cat ~/openclaw/workspace/memory/技能记忆表格/技能记忆多维表格.md"
echo ""
echo "=================================================="
echo "🦞 恢复系统就绪！"
echo "=================================================="
