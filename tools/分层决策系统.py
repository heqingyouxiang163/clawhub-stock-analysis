#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 分层决策系统

决策流程:
1. 规则匹配 (0 Token) ← 80% 决策
2. 简单推理 (低 Token) ← 15% 决策
3. AI 深度分析 (高 Token) ← 5% 决策

使用:
    from 分层决策系统 import make_decision
    result = make_decision(股票数据)
"""

import json
from pathlib import Path
from typing import Dict, Optional


class DecisionEngine:
    """分层决策引擎"""
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge()
        self.stats = {
            'layer1_count': 0,  # 规则匹配
            'layer2_count': 0,  # 简单推理
            'layer3_count': 0,  # AI 分析
            'total': 0
        }
    
    def _load_knowledge(self) -> Dict:
        """加载知识库"""
        cache_file = Path('data_cache/knowledge_base/knowledge_base_full.json')
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def make_decision(self, stock_data: Dict) -> Dict:
        """分层决策
        
        Args:
            stock_data: 股票数据
        
        Returns:
            决策结果
        """
        self.stats['total'] += 1
        
        # 第一层：规则匹配
        result = self._layer1_rule_match(stock_data)
        if result['confidence'] >= 0.8:
            self.stats['layer1_count'] += 1
            result['layer'] = 1
            result['method'] = '规则匹配'
            return result
        
        # 第二层：简单推理
        result = self._layer2_simple_reasoning(stock_data)
        if result['confidence'] >= 0.6:
            self.stats['layer2_count'] += 1
            result['layer'] = 2
            result['method'] = '简单推理'
            return result
        
        # 第三层：AI 深度分析
        self.stats['layer3_count'] += 1
        result = self._layer3_ai_analysis(stock_data)
        result['layer'] = 3
        result['method'] = 'AI 深度分析'
        return result
    
    def _layer1_rule_match(self, stock_data: Dict) -> Dict:
        """第一层：规则匹配 (0 Token)"""
        result = {
            'recommend': False,
            'score': 0,
            'confidence': 0,
            'reasons': []
        }
        
        # 规则 1: 检查历史教训
        lessons = self.knowledge_base.get('lessons', [])
        for lesson in lessons:
            content = lesson.get('content', '')
            stock_name = stock_data.get('name', '')
            if stock_name in content and '错误' in content:
                result['confidence'] = 0.9
                result['reasons'].append(f"⚠️ 历史教训：{stock_name} 有过错误记录")
                result['recommend'] = False
                return result
        
        # 规则 2: 检查风险案例
        risk_cases = self.knowledge_base.get('risk_cases', [])
        for case in risk_cases:
            content = case.get('content', '')
            # 检查是否匹配风险模式
            if '高位缩量' in content and stock_data.get('position', 0) > 0.8:
                result['confidence'] = 0.85
                result['reasons'].append("⚠️ 风险案例：高位缩量，避免满仓")
                result['recommend'] = False
                return result
        
        # 规则 3: 止损止盈策略
        strategies = self.knowledge_base.get('strategies', {})
        if '止损止盈策略' in strategies:
            strategy_content = strategies['止损止盈策略'].get('content', '')
            # 应用止损规则
            if stock_data.get('loss_pct', 0) < -5:
                result['confidence'] = 0.8
                result['reasons'].append("📉 触发止损规则 (-5%)")
                result['recommend'] = False
                return result
        
        # 规则 4: 涨停形态匹配
        # TODO: 实现形态匹配逻辑
        
        return result
    
    def _layer2_simple_reasoning(self, stock_data: Dict) -> Dict:
        """第二层：简单推理 (低 Token)"""
        result = {
            'recommend': False,
            'score': 0,
            'confidence': 0,
            'reasons': []
        }
        
        # 简单评分系统
        score = 0
        
        # 涨幅评分 (0-30 分)
        price_change = stock_data.get('price_change_pct', 0)
        if 3 <= price_change <= 7:
            score += 25  # 适中涨幅
            result['reasons'].append(f"✅ 涨幅适中 ({price_change}%)")
        elif price_change > 9:
            score += 5  # 涨停，风险高
            result['reasons'].append(f"⚠️ 涨幅过大 ({price_change}%)")
        
        # 量能评分 (0-30 分)
        volume_ratio = stock_data.get('volume_ratio', 1)
        if 1.5 <= volume_ratio <= 3:
            score += 25  # 温和放量
            result['reasons'].append(f"✅ 量能健康 ({volume_ratio}x)")
        
        # 位置评分 (0-40 分)
        position = stock_data.get('position', 0.5)
        if position < 0.3:
            score += 35  # 低位
            result['reasons'].append("✅ 低位")
        elif position > 0.8:
            score += 10  # 高位
            result['reasons'].append("⚠️ 高位")
        
        result['score'] = score
        result['confidence'] = score / 100
        result['recommend'] = score >= 70
        
        return result
    
    def _layer3_ai_analysis(self, stock_data: Dict) -> Dict:
        """第三层：AI 深度分析 (高 Token)"""
        # 这里调用 AI 分析
        # 为了节省 Token，只传入必要数据
        
        result = {
            'recommend': False,
            'score': 0,
            'confidence': 0,
            'reasons': [],
            'ai_analysis': True
        }
        
        # TODO: 调用 AI 分析
        # 精简输出格式:
        # {
        #     'recommend': True/False,
        #     'score': 0-100,
        #     'reasons': ['理由 1', '理由 2', '理由 3'],
        #     'risk': '高/中/低'
        # }
        
        return result
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.stats['total']
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            'layer1_ratio': f"{self.stats['layer1_count']/total*100:.1f}%",
            'layer2_ratio': f"{self.stats['layer2_count']/total*100:.1f}%",
            'layer3_ratio': f"{self.stats['layer3_count']/total*100:.1f}%",
        }


# 全局决策引擎实例
engine = DecisionEngine()


def make_decision(stock_data: Dict) -> Dict:
    """快速决策接口"""
    return engine.make_decision(stock_data)


def get_decision_stats() -> Dict:
    """获取决策统计"""
    return engine.get_stats()


if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("🦞 分层决策系统测试")
    print("=" * 60)
    print()
    
    # 测试数据
    test_stock = {
        'code': '000001',
        'name': '平安银行',
        'price_change_pct': 5.2,
        'volume_ratio': 2.1,
        'position': 0.3,
        'loss_pct': -2.0
    }
    
    # 决策
    result = make_decision(test_stock)
    
    print(f"股票：{test_stock['name']} ({test_stock['code']})")
    print(f"决策：{'✅ 推荐' if result['recommend'] else '❌ 不推荐'}")
    print(f"评分：{result['score']}")
    print(f"置信度：{result['confidence']*100:.1f}%")
    print(f"决策层：L{result.get('layer', '?')} - {result.get('method', '?')}")
    print(f"理由:")
    for reason in result.get('reasons', []):
        print(f"  {reason}")
    
    print()
    print("决策统计:")
    stats = get_decision_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
