#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 自动学习监听器

功能：
- 监听用户回复中的关键词（对/错/不错/不准等）
- 自动记录到强化学习系统
- 每日 23:00 生成学习报告

使用方式：
作为定时任务运行，或集成到对话系统中

作者：炒股龙虾系统
版本：v1.0
创建：2026-03-27
"""

import json
import re
from datetime import datetime
from pathlib import Path

# 导入强化学习器
from 强化学习反馈 import ReinforcementLearner


class FeedbackMonitor:
    """反馈监听器"""
    
    def __init__(self):
        self.learner = ReinforcementLearner()
        self.context_buffer = []  # 上下文缓冲区
        
    def analyze_message(self, message, context=None):
        """
        分析用户消息，判断是否是反馈
        
        Args:
            message: 用户消息
            context: 上下文（可选）
            
        Returns:
            bool: 是否是反馈消息
        """
        
        # 强化关键词
        positive_patterns = [
            r'[对对对]+', r'不错', r'准', r'正确', 
            r'好的', r'ok', r'yes', r'👍', r'✅'
        ]
        
        # 修正关键词
        negative_patterns = [
            r'[错错错]+', r'不准', r'不行', r'错误', 
            r'不对', r'no', r'👎', r'❌'
        ]
        
        # 检查是否是正面反馈
        for pattern in positive_patterns:
            if re.search(pattern, message):
                if context:
                    self.learner.record_feedback(
                        context=context,
                        feedback=message,
                        action="保持当前策略"
                    )
                return True
        
        # 检查是否是负面反馈
        for pattern in negative_patterns:
            if re.search(pattern, message):
                if context:
                    self.learner.record_feedback(
                        context=context,
                        feedback=message,
                        action="修正策略，记录教训"
                    )
                return True
        
        return False
    
    def generate_daily_report(self):
        """生成每日学习报告"""
        
        stats = self.learner.get_statistics()
        today = datetime.now().strftime('%Y-%m-%d')
        
        report = f"""
# 🧠 强化学习日报 - {today}

## 📊 统计概览

| 指标 | 数值 |
|------|------|
| 正面反馈 | {stats['positive_count']} 次 |
| 负面反馈 | {stats['negative_count']} 次 |
| 经验教训 | {stats['lessons_count']} 条 |
| 准确率 | {stats['accuracy']:.1f}% |

## ✅ 正面强化

"""
        # 添加最近的正面反馈
        for record in self.learner.feedback_history['positive'][-5:]:
            report += f"- {record['timestamp']}: {record['context']} → {record['feedback']}\n"
        
        report += "\n## ⚠️ 负面修正\n\n"
        
        # 添加最近的负面反馈
        for record in self.learner.feedback_history['negative'][-5:]:
            report += f"- {record['timestamp']}: {record['context']} → {record['feedback']}\n"
        
        report += "\n## 📝 经验教训\n\n"
        
        # 添加教训
        for lesson in self.learner.feedback_history['lessons'][-5:]:
            report += f"- {lesson['lesson']}\n"
        
        # 保存报告
        report_file = Path("/home/admin/openclaw/workspace/memory/强化学习") / f"{today}-学习报告.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 已生成学习报告：{report_file}")
        return report


def main():
    """主函数 - 演示用法"""
    
    monitor = FeedbackMonitor()
    
    print("🧠 自动学习监听器 - 演示\n")
    
    # 模拟用户反馈
    test_cases = [
        ("推荐 通鼎互联 涨停", "不错"),
        ("预测 国新能源 反弹", "错"),
        ("建议止损 -5%", "对"),
        ("目标 +10%", "不准"),
    ]
    
    for context, feedback in test_cases:
        print(f"\n上下文：{context}")
        print(f"用户反馈：{feedback}")
        is_feedback = monitor.analyze_message(feedback, context)
        print(f"是否反馈：{is_feedback}")
    
    # 生成报告
    print("\n" + "=" * 60)
    report = monitor.generate_daily_report()
    print(report)


if __name__ == "__main__":
    main()
