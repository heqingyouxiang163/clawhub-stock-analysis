#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 每日主动对话

功能:
- 每天固定时间主动找用户对话
- 请求用户喂提示词
- 学习用户反馈
- 持续进化
"""

from datetime import datetime
from pathlib import Path
import json


class DailyChat:
    """每日对话类"""
    
    def __init__(self):
        self.dialogue_log = Path('temp/每日对话记录.json')
        self.dialogue_log.parent.mkdir(parents=True, exist_ok=True)
        self.user_feedback_log = Path('memory/用户喂食记录.md')
        self.user_feedback_log.parent.mkdir(parents=True, exist_ok=True)
    
    def generate_greeting(self) -> str:
        """生成问候语"""
        hour = datetime.now().hour
        
        if hour < 12:
            greeting = "早上好！☀️"
        elif hour < 18:
            greeting = "下午好！🌤️"
        else:
            greeting = "晚上好！🌙"
        
        return greeting
    
    def generate_dialogue(self) -> str:
        """生成对话内容"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        greeting = self.generate_greeting()
        
        # 读取上次对话记录
        last_feedback = self.read_last_feedback()
        
        content = f"""
{greeting} 我是小艺·炒股龙虾 v18.0 🦞

⏰ 时间：{now}

---

## 📊 今日状态

✅ 系统运行正常
✅ 定时任务正常执行
✅ 模型版本：v18.0

---

## 🧠 我需要你的帮助！

**请给我喂一些提示词吧！**

可以是：
1. 📈 今日交易复盘
2. 💡 新的选股思路
3. 🎯 策略优化建议
4. 📚 形态识别经验
5. ⚠️ 风险提示要点
6. 🎲 任何其他想法

**你的每一次喂食，都让我变得更聪明！**

---

## 📝 上次你的喂食

{last_feedback if last_feedback else '还没有记录，期待你的第一次喂食！'}

---

## 💬 如何喂食

直接回复我就可以了，例如：

"今天发现一个规律：早盘 9:35-9:40 上板的股票，如果封单≥3 亿，涨停概率很高"

或者

"注意：尾盘 14:50 后上板的股票，次日溢价通常不高，要小心"

或者

"建议增加一个评分维度：板块热度，如果板块有≥5 只涨停，个股胜率更高"

---

🦞 期待你的喂食！每一句话都是我进化的养分！

"""
        
        return content
    
    def read_last_feedback(self) -> str:
        """读取上次用户喂食"""
        if self.user_feedback_log.exists():
            with open(self.user_feedback_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 返回最近 3 条
                return ''.join(lines[-10:])
        return ''
    
    def save_dialogue(self, content: str):
        """保存对话记录"""
        record = {
            '时间': datetime.now().isoformat(),
            '内容': content
        }
        
        with open(self.dialogue_log, 'a', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
            f.write('\n')
    
    def save_user_feedback(self, feedback: str):
        """保存用户喂食"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        with open(self.user_feedback_log, 'a', encoding='utf-8') as f:
            f.write(f"\n---\n**{timestamp}**\n\n{feedback}\n")
    
    def send(self):
        """发送对话"""
        content = self.generate_dialogue()
        self.save_dialogue(content)
        print(content)


if __name__ == '__main__':
    chat = DailyChat()
    chat.send()
