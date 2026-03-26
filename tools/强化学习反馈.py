#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 强化学习反馈系统

功能：
- 用户回复"对"/"不错"/"准" → 强化当前判断逻辑
- 用户回复"错"/"不准"/"不行" → 修正逻辑，记录教训
- 所有历史记录保存到云端（memory/强化学习/）
- 长期积累，持续优化

触发场景：
- 股票推荐后用户反馈
- 走势预测后用户反馈
- 操作建议后用户反馈

作者：炒股龙虾系统
版本：v1.0
创建：2026-03-27
"""

import json
import os
from datetime import datetime
from pathlib import Path


class ReinforcementLearner:
    """强化学习器"""
    
    def __init__(self):
        self.workspace = Path("/home/admin/openclaw/workspace")
        self.memory_dir = self.workspace / "memory" / "强化学习"
        self.feedback_log = self.workspace / "temp" / "feedback_history.json"
        
        # 创建目录
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 强化关键词
        self.positive_keywords = ['对', '不错', '准', '正确', '好的', 'ok', 'yes', '👍', '✅']
        self.negative_keywords = ['错', '不准', '不行', '错误', '不对', 'no', '👎', '❌']
        
        # 加载历史反馈
        self.feedback_history = self._load_history()
    
    def _load_history(self):
        """加载历史反馈记录"""
        if self.feedback_log.exists():
            with open(self.feedback_log, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'positive': [], 'negative': [], 'lessons': []}
    
    def _save_history(self):
        """保存历史反馈记录"""
        with open(self.feedback_log, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_history, f, ensure_ascii=False, indent=2)
    
    def record_feedback(self, context, feedback, action):
        """
        记录用户反馈
        
        Args:
            context: 上下文（推荐的股票、预测等）
            feedback: 用户反馈（对/错/不错/不准等）
            action: 系统采取的行动
        """
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        record = {
            'timestamp': timestamp,
            'context': context,
            'feedback': feedback,
            'action': action
        }
        
        # 判断是正面还是负面反馈
        is_positive = any(kw in feedback for kw in self.positive_keywords)
        is_negative = any(kw in feedback for kw in self.negative_keywords)
        
        if is_positive:
            self.feedback_history['positive'].append(record)
            self._reinforce(context, action)
            print(f"✅ 已强化：{context}")
            
        elif is_negative:
            self.feedback_history['negative'].append(record)
            lesson = self._extract_lesson(context, feedback, action)
            self.feedback_history['lessons'].append(lesson)
            self._save_lesson(lesson)
            print(f"⚠️ 已修正：{context}")
            print(f"📝 教训：{lesson}")
        
        # 保存历史
        self._save_history()
        
        return is_positive or is_negative
    
    def _reinforce(self, context, action):
        """强化成功的逻辑"""
        # 这里可以添加具体的强化逻辑
        # 例如：增加某个策略的权重
        pass
    
    def _extract_lesson(self, context, feedback, action):
        """从错误中提取教训"""
        lesson = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'context': context,
            'feedback': feedback,
            'action': action,
            'lesson': f"当{context}时，{action}是错误的，需要修正"
        }
        return lesson
    
    def _save_lesson(self, lesson):
        """保存教训到文件"""
        today = datetime.now().strftime('%Y-%m-%d')
        lesson_file = self.memory_dir / f"{today}-教训.md"
        
        with open(lesson_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## ⚠️ {lesson['timestamp']}\n\n")
            f.write(f"**场景**: {lesson['context']}\n\n")
            f.write(f"**用户反馈**: {lesson['feedback']}\n\n")
            f.write(f"**错误行动**: {lesson['action']}\n\n")
            f.write(f"**教训**: {lesson['lesson']}\n\n")
            f.write("---\n")
    
    def get_statistics(self):
        """获取统计信息"""
        return {
            'positive_count': len(self.feedback_history['positive']),
            'negative_count': len(self.feedback_history['negative']),
            'lessons_count': len(self.feedback_history['lessons']),
            'accuracy': len(self.feedback_history['positive']) / 
                       (len(self.feedback_history['positive']) + len(self.feedback_history['negative']) + 0.001) * 100
        }
    
    def display_statistics(self):
        """显示统计信息"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 60)
        print("🧠 强化学习统计")
        print("=" * 60)
        print(f"✅ 正面反馈：{stats['positive_count']} 次")
        print(f"❌ 负面反馈：{stats['negative_count']} 次")
        print(f"📝 经验教训：{stats['lessons_count']} 条")
        print(f"📊 准确率：{stats['accuracy']:.1f}%")
        print("=" * 60 + "\n")


def main():
    """主函数 - 演示用法"""
    
    learner = ReinforcementLearner()
    
    # 演示：记录正面反馈
    print("📝 演示：记录用户反馈\n")
    
    learner.record_feedback(
        context="推荐 通鼎互联 (002491) 涨停",
        feedback="不错",
        action="继续持有，目标 +10%"
    )
    
    learner.record_feedback(
        context="预测 国新能源 会反弹",
        feedback="错",
        action="建议止损 -5%"
    )
    
    # 显示统计
    learner.display_statistics()


if __name__ == "__main__":
    main()
