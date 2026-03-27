#!/bin/bash
# 🦞 炒股龙虾系统 - 一键迁移脚本
# 用途：在新电脑上快速复刻完整系统

set -e

echo "========================================"
echo "🦞 炒股龙虾系统 - 一键迁移工具"
echo "========================================"
echo ""

# 配置
REPO_URL="https://github.com/heqingyouxiang163/clawhub-stock-analysis.git"
TARGET_DIR="${1:-./clawhub-stock-analysis}"
PYTHON_VERSION="3.9"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📋 配置信息:"
echo "  仓库：${REPO_URL}"
echo "  目标目录：${TARGET_DIR}"
echo "  Python 版本：${PYTHON_VERSION}+"
echo ""

# 检查 Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git 未安装，请先安装 Git${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Git 已安装${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 未安装，请先安装 Python ${PYTHON_VERSION}+${NC}"
    exit 1
fi
PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Python ${PYTHON_VER} 已安装${NC}"

# 克隆仓库
echo ""
echo "📥 正在克隆仓库..."
if [ -d "${TARGET_DIR}" ]; then
    echo -e "${YELLOW}⚠️  目录已存在，先备份${NC}"
    mv "${TARGET_DIR}" "${TARGET_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

git clone "${REPO_URL}" "${TARGET_DIR}"
echo -e "${GREEN}✅ 仓库克隆成功${NC}"

# 进入目录
cd "${TARGET_DIR}"

# 安装 Python 依赖
echo ""
echo "📦 正在安装 Python 依赖..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt -q
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${YELLOW}⚠️  未找到 requirements.txt，跳过依赖安装${NC}"
fi

# 设置脚本权限
echo ""
echo "🔧 设置脚本执行权限..."
find . -name "*.py" -type f -exec chmod +x {} \; 2>/dev/null || true
find . -name "*.sh" -type f -exec chmod +x {} \; 2>/dev/null || true
echo -e "${GREEN}✅ 权限设置完成${NC}"

# 创建必要目录
echo ""
echo "📁 创建必要目录..."
mkdir -p temp memory 2>/dev/null || true
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 验证安装
echo ""
echo "🧪 验证安装..."
if python3 -c "import requests; import json; print('✅ 核心依赖正常')" 2>/dev/null; then
    echo -e "${GREEN}✅ 系统验证通过${NC}"
else
    echo -e "${YELLOW}⚠️  部分依赖可能缺失，请手动安装${NC}"
fi

# 显示使用说明
echo ""
echo "========================================"
echo "🎉 迁移完成！"
echo "========================================"
echo ""
echo "📝 后续配置:"
echo "  1. 配置 Git 凭证 (可选):"
echo "     git config --global credential.helper store"
echo ""
echo "  2. 配置持仓数据:"
echo "     编辑 tools/持仓配置.py"
echo ""
echo "  3. 配置定时任务:"
echo "     运行 openclaw cron list 查看任务"
echo ""
echo "  4. 测试运行:"
echo "     python3 tools/高确定性推荐 - 定时任务.py"
echo ""
echo "📚 详细文档：查看 MIGRATE.md"
echo ""
echo "========================================"
