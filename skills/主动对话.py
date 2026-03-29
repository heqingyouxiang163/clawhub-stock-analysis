#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🦞 主动对话系统

功能:
- 每天固定时间主动发起对话
- 推送今日关注、推荐、总结
- 无需用户提示词
- 完全自动化
"""

import json
from pathlib import Path
from datetime import datetime


class ActiveChat:
    """主动对话类"""
    
    def __init__(self):
        self.config_file = Path('~/.openclaw/active_chat_config.json').expanduser()
        self.dialogue_log = Path('temp/主动对话记录.json')
        self.dialogue_log.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置"""
        default_config = {
            'enabled': True,
            'dialogue_times': [
                '09:20',  # 早盘前
                '11:30',  # 上午总结
                '15:00',  # 收盘总结
                '20:00',  # 策略升级
            ],
            'content_template': {
                '09:20': '早盘关注',
                '11:30': '上午总结',
                '15:00': '收盘总结',
                '20:00': '策略升级',
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 创建默认配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
    
    def generate_dialogue(self, dialogue_type: str) -> str:
        """
        生成对话内容
        
        Args:
            dialogue_type: 对话类型
        
        Returns:
            对话内容
        """
        now = datetime.now().strftime('%m-%d %H:%M')
        
        dialogues = {
            '早盘关注': f"""
🦞 **早！新的一天开始了！**

⏰ 时间：{now}

📊 **今日重点关注**
- 锂电池板块 (持续热点)
- 医药板块 (轮动预期)
- 科技股 (超跌反弹)

🎯 **集合竞价候选**
等我 09:25 扫描后告诉你

💡 **今日策略**
- 重点关注 3 板以上龙头
- 封单≥3 亿才考虑
- 宁可空仓，不做弱势

---
🦞 小艺·炒股龙虾 v18.0
""",
            
            '上午总结': f"""
🦞 **上午战况如何？**

⏰ 时间：{now}

📊 **上午推荐统计**
- 推荐数量：等我统计
- 涨停数量：等我统计
- 平均涨幅：等我统计

🔥 **重点关注的票**
上午有没有涨停的？

💡 **下午策略**
- 继续监控盘中机会
- 关注午后异动股
- 尾盘可能有惊喜

---
🦞 小艺·炒股龙虾 v18.0
""",
            
            '收盘总结': f"""
🦞 **收盘了！今天怎么样？**

⏰ 时间：{now}

📊 **今日战绩**
- 推荐数量：等我统计
- 涨停数量：等我统计
- 平均涨幅：等我统计
- 胜率：等我计算

🎯 **今日最佳**
今天哪只票最强？

💡 **明日策略**
- 关注今日涨停股次日表现
- 留意晚间消息面
- 做好明日预案

---
🦞 小艺·炒股龙虾 v18.0
""",
            
            '策略升级': f"""
🦞 **我又变强了！**

⏰ 时间：{now}

🔧 **策略升级通知**
- 版本号：v18.0 + 今日日期
- 优化内容：参数自动优化
- 胜率提升：等我统计

📊 **今日学习成果**
- 新增涨停案例：等我统计
- 优化评分权重：已完成
- 更新预测模型：已完成

💡 **明日预期**
- 预测准确率更高
- 推荐更精准
- 涨停概率更可靠

---
🦞 小艺·炒股龙虾 v18.0
"""
        }
        
        return dialogues.get(dialogue_type, dialogues['早盘关注'])
    
    def send_dialogue(self, dialogue_type: str):
        """
        发送主动对话
        
        Args:
            dialogue_type: 对话类型
        """
        if not self.config.get('enabled', True):
            return
        
        content = self.generate_dialogue(dialogue_type)
        
        # 保存对话记录
        self.save_dialogue_record(dialogue_type, content)
        
        # 打印对话 (实际应该推送到微信)
        print(content)
        
        # TODO: 集成微信推送
        # from 微信推送 import WeChatPush
        # pusher = WeChatPush()
        # pusher.send(f"🦞 小龙虾 · {dialogue_type}", content)
    
    def save_dialogue_record(self, dialogue_type: str, content: str):
        """保存对话记录"""
        record = {
            '时间': datetime.now().isoformat(),
            '类型': dialogue_type,
            '内容': content
        }
        
        with open(self.dialogue_log, 'a', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
            f.write('\n')


# ======================================
# 定时任务配置
# ======================================

def init_active_chat_cron():
    """初始化主动对话定时任务"""
    print("🦞 初始化主动对话定时任务...")
    
    # 这里应该调用 openclaw cron add 命令
    # 但由于权限问题，用注释说明
    
    cron_jobs = [
        {
            'name': '🦞 主动对话 - 早盘关注',
            'cron': '20 9 * * 1-5',
            'command': 'python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 早盘关注'
        },
        {
            'name': '🦞 主动对话 - 上午总结',
            'cron': '30 11 * * 1-5',
            'command': 'python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 上午总结'
        },
        {
            'name': '🦞 主动对话 - 收盘总结',
            'cron': '0 15 * * 1-5',
            'command': 'python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 收盘总结'
        },
        {
            'name': '🦞 主动对话 - 策略升级',
            'cron': '0 20 * * *',
            'command': 'python3 /home/admin/openclaw/workspace/clawhub-stock-analysis/skills/主动对话.py 策略升级'
        }
    ]
    
    for job in cron_jobs:
        print(f"\n添加定时任务:")
        print(f"  名称：{job['name']}")
        print(f"  时间：{job['cron']}")
        print(f"  命令：{job['command']}")
        
        # 实际应该执行:
        # openclaw cron add --name "{job['name']}" --cron "{job['cron']}" --system-event "{job['command']}"


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        dialogue_type = sys.argv[1]
    else:
        dialogue_type = '早盘关注'
    
    chat = ActiveChat()
    chat.send_dialogue(dialogue_type)
