#!/bin/bash
# 🦞 微信推送配置脚本

echo "=========================================="
echo "🦞 微信推送配置"
echo "=========================================="
echo ""

# 创建配置目录
mkdir -p ~/.openclaw

# 复制配置模板
cp tools/wechat_config_template.json ~/.openclaw/wechat_config.json

echo "✅ 配置文件已创建：~/.openclaw/wechat_config.json"
echo ""
echo "📱 请选择推送平台:"
echo "1. 企业微信机器人 (推荐)"
echo "2. Server 酱"
echo ""
read -p "请选择 [1-2]: " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "📋 企业微信配置步骤:"
    echo "1. 访问：https://work.weixin.qq.com/"
    echo "2. 注册企业微信 (个人也可以)"
    echo "3. 工作台 → 群机器人 → 添加"
    echo "4. 获取 Webhook URL"
    echo ""
    read -p "请输入 Webhook URL: " webhook
    echo ""
    echo "正在更新配置..."
    
    # 更新配置文件
    cat > ~/.openclaw/wechat_config.json << EOF
{
  "platform": "企业微信",
  "webhook": "$webhook",
  
  "推送设置": {
    "早盘候选": true,
    "打板推荐": true,
    "盘中更新": false,
    "收盘总结": true,
    "复盘报告": true,
    "策略升级": true,
    "代码同步": false
  }
}
EOF
    
    echo "✅ 配置完成！"
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "📋 Server 酱配置步骤:"
    echo "1. 访问：https://sct.ftqq.com/"
    echo "2. 微信扫码登录"
    echo "3. 获取 SendKey"
    echo ""
    read -p "请输入 SendKey: " sendkey
    echo ""
    echo "正在更新配置..."
    
    # 更新配置文件
    cat > ~/.openclaw/wechat_config.json << EOF
{
  "platform": "Server 酱",
  "serverchan_sendkey": "$sendkey",
  
  "推送设置": {
    "早盘候选": true,
    "打板推荐": true,
    "盘中更新": false,
    "收盘总结": true,
    "复盘报告": true,
    "策略升级": true,
    "代码同步": false
  }
}
EOF
    
    echo "✅ 配置完成！"
else
    echo "❌ 无效选择"
    exit 1
fi

echo ""
echo "🧪 测试推送..."
python3 skills/微信推送.py

echo ""
echo "=========================================="
echo "✅ 微信推送配置完成！"
echo "=========================================="
