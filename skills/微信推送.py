#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 微信推送脚本

支持:
- 企业微信机器人
- 微信测试号
- Server 酱
"""

import requests
import json
from pathlib import Path
from datetime import datetime


class WeChatPush:
    """微信推送类"""
    
    def __init__(self):
        self.config_file = Path('~/.openclaw/wechat_config.json').expanduser()
        self.log_file = Path('temp/微信推送日志.txt')
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("⚠️ 配置文件不存在，请先配置 ~/.openclaw/wechat_config.json")
            return {}
    
    def log(self, message):
        """写入日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)
        
        print(log_line.strip())
    
    def send_enterprise_wechat(self, title, content):
        """
        企业微信机器人推送
        
        Args:
            title: 标题
            content: 内容 (支持 Markdown)
        """
        webhook = self.config.get('webhook', '')
        
        if not webhook:
            self.log("❌ 企业微信 Webhook 未配置")
            return False
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"### {title}\n\n{content}"
            }
        }
        
        try:
            resp = requests.post(webhook, json=data, timeout=10)
            if resp.json().get('errcode') == 0:
                self.log("✅ 企业微信推送成功")
                return True
            else:
                self.log(f"❌ 企业微信推送失败：{resp.text}")
                return False
        except Exception as e:
            self.log(f"❌ 推送异常：{e}")
            return False
    
    def send_serverchan(self, title, content):
        """
        Server 酱推送
        
        Args:
            title: 标题
            content: 内容
        """
        sendkey = self.config.get('serverchan_sendkey', '')
        
        if not sendkey:
            self.log("❌ Server 酱 SendKey 未配置")
            return False
        
        url = f"https://sctapi.ftqq.com/{sendkey}.send"
        data = {
            "title": title,
            "desp": content
        }
        
        try:
            resp = requests.post(url, data=data, timeout=10)
            if resp.json().get('code') == 0:
                self.log("✅ Server 酱推送成功")
                return True
            else:
                self.log(f"❌ Server 酱推送失败：{resp.text}")
                return False
        except Exception as e:
            self.log(f"❌ 推送异常：{e}")
            return False
    
    def send(self, title, content, platform=None):
        """
        统一推送接口
        
        Args:
            title: 标题
            content: 内容
            platform: 平台 (企业微信/serverchan)
        """
        if platform is None:
            platform = self.config.get('platform', '企业微信')
        
        self.log(f"📱 准备推送：{title}")
        
        if platform == '企业微信':
            return self.send_enterprise_wechat(title, content)
        elif platform == 'Server 酱':
            return self.send_serverchan(title, content)
        else:
            self.log(f"⚠️ 未知平台：{platform}")
            return False


# ======================================
# 快捷推送函数
# ======================================

def push_recommendation(targets):
    """推送打板推荐"""
    if not targets:
        return
    
    content = f"""⏰ 时间：{datetime.now().strftime('%m-%d %H:%M')}

🔥 **重点推荐**
"""
    
    for i, t in enumerate(targets[:3], 1):
        content += f"""
{i}. **{t['代码']} {t['名称']}**
   - 综合评分：{t['综合评分']}
   - 涨停概率：{t['涨停概率']}%
   - 封单：{t['封单额']}亿
   - 连板：{t['连板数']}板
"""
    
    content += """
---
⚠️ **风险提示**
- 炸板立即止损
- 回撤≥4% 坚决卖出
- 仅供参考，不构成投资建议
"""
    
    pusher = WeChatPush()
    pusher.send("🦞 小龙虾 · 打板推荐", content)


def push_summary(summary):
    """推送总结报告"""
    content = f"""⏰ 时间：{datetime.now().strftime('%m-%d %H:%M')}

📊 **{summary['类型']}**

✅ 推荐：{summary['推荐数']}只
🔥 涨停：{summary['涨停数']}只
📈 平均涨幅：{summary['平均涨幅']}%
🎯 胜率：{summary['胜率']}%

---
🦞 模型版本：v18.0
"""
    
    pusher = WeChatPush()
    pusher.send(f"🦞 小龙虾 · {summary['标题']}", content)


if __name__ == '__main__':
    # 测试推送
    pusher = WeChatPush()
    
    # 测试消息
    test_content = """
⏰ 时间：03-29 11:20

✅ 系统测试推送

这是一条测试消息，用于验证微信推送功能是否正常。

---
🦞 小龙虾 v18.0
"""
    
    success = pusher.send("🦞 小龙虾 · 测试推送", test_content)
    
    if success:
        print("\n✅ 推送成功！请检查微信")
    else:
        print("\n❌ 推送失败，请检查配置")
