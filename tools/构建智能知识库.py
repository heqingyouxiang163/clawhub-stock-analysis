#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🦞 智能知识库构建工具

功能:
- 加载所有策略文档到缓存
- 加载历史教训
- 加载形态库
- 提供统一查询接口

使用:
    python3 tools/构建智能知识库.py
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class KnowledgeBase:
    """智能知识库"""
    
    def __init__(self):
        self.cache_dir = Path('data_cache/knowledge_base')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 知识库内容
        self.knowledge = {
            'strategies': {},      # 策略文档
            'lessons': [],         # 历史教训
            'morphologies': [],    # 形态库
            'risk_cases': [],      # 风险案例
        }
    
    def load_strategies(self) -> Dict:
        """加载所有策略文档"""
        strategies_dir = Path('skills/trading')
        strategies = {}
        
        for md_file in strategies_dir.glob('*.md'):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取关键信息
                strategies[md_file.stem] = {
                    'name': md_file.stem,
                    'content': content[:5000],  # 限制长度
                    'loaded_at': datetime.now().isoformat()
                }
                print(f"✅ 加载策略：{md_file.stem}")
        
        self.knowledge['strategies'] = strategies
        return strategies
    
    def load_lessons(self) -> List:
        """加载历史教训"""
        lessons_dir = Path('memory/强化学习')
        lessons = []
        
        if lessons_dir.exists():
            for md_file in lessons_dir.glob('*.md'):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lessons.append({
                        'file': md_file.stem,
                        'content': content,
                        'loaded_at': datetime.now().isoformat()
                    })
                    print(f"✅ 加载教训：{md_file.stem}")
        
        # 从其他 memory 文件加载教训
        memory_dir = Path('memory')
        for md_file in memory_dir.glob('*.md'):
            if '教训' in md_file.stem or '错误' in md_file.stem:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '错误' in content or '教训' in content:
                        lessons.append({
                            'file': md_file.stem,
                            'content': content[:3000],
                            'loaded_at': datetime.now().isoformat()
                        })
                        print(f"✅ 加载教训：{md_file.stem}")
        
        self.knowledge['lessons'] = lessons
        return lessons
    
    def load_morphologies(self) -> List:
        """加载形态库"""
        # 从缓存加载
        morphology_cache = Path('data_cache/morphology_lib.json')
        if morphology_cache.exists():
            with open(morphology_cache, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.knowledge['morphologies'] = data.get('morphologies', [])
                print(f"✅ 加载形态库：{len(self.knowledge['morphologies'])} 个形态")
        
        return self.knowledge['morphologies']
    
    def load_risk_cases(self) -> List:
        """加载风险案例"""
        risk_dir = Path('memory/风险提示库')
        risk_cases = []
        
        if risk_dir.exists():
            for md_file in risk_dir.glob('*.md'):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    risk_cases.append({
                        'file': md_file.stem,
                        'content': content[:3000],
                        'loaded_at': datetime.now().isoformat()
                    })
                    print(f"✅ 加载风险案例：{md_file.stem}")
        
        self.knowledge['risk_cases'] = risk_cases
        return risk_cases
    
    def build(self):
        """构建完整知识库"""
        print("=" * 60)
        print("🦞 构建智能知识库")
        print("=" * 60)
        print()
        
        # 加载所有知识
        self.load_strategies()
        self.load_lessons()
        self.load_morphologies()
        self.load_risk_cases()
        
        # 保存到缓存
        self.save()
        
        # 显示统计
        self.show_stats()
    
    def save(self):
        """保存知识库到缓存"""
        cache_file = self.cache_dir / 'knowledge_base.json'
        
        # 创建精简版 (移除大段内容，只保留索引)
        lite_version = {
            'built_at': datetime.now().isoformat(),
            'stats': {
                'strategies_count': len(self.knowledge['strategies']),
                'lessons_count': len(self.knowledge['lessons']),
                'morphologies_count': len(self.knowledge['morphologies']),
                'risk_cases_count': len(self.knowledge['risk_cases']),
            },
            'indexes': {
                'strategies': list(self.knowledge['strategies'].keys()),
                'lessons': [l['file'] for l in self.knowledge['lessons']],
                'morphologies': [m.get('name', '') for m in self.knowledge['morphologies']],
                'risk_cases': [r['file'] for r in self.knowledge['risk_cases']],
            }
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(lite_version, f, ensure_ascii=False, indent=2)
        
        # 保存完整版
        full_file = self.cache_dir / 'knowledge_base_full.json'
        with open(full_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"✅ 知识库已保存:")
        print(f"   精简版：{cache_file}")
        print(f"   完整版：{full_file}")
    
    def show_stats(self):
        """显示统计信息"""
        print()
        print("=" * 60)
        print("📊 知识库统计")
        print("=" * 60)
        print(f"策略文档：{len(self.knowledge['strategies'])} 个")
        print(f"历史教训：{len(self.knowledge['lessons'])} 条")
        print(f"形态库：  {len(self.knowledge['morphologies'])} 个")
        print(f"风险案例：{len(self.knowledge['risk_cases'])} 个")
        print()


def query_knowledge(keyword: str) -> Dict:
    """查询知识库
    
    Args:
        keyword: 关键词
    
    Returns:
        匹配的结果
    """
    cache_file = Path('data_cache/knowledge_base/knowledge_base_full.json')
    
    if not cache_file.exists():
        return {'error': '知识库不存在，先运行构建脚本'}
    
    with open(cache_file, 'r', encoding='utf-8') as f:
        knowledge = json.load(f)
    
    results = {
        'strategies': [],
        'lessons': [],
        'morphologies': [],
        'risk_cases': []
    }
    
    # 搜索策略
    for name, strategy in knowledge.get('strategies', {}).items():
        if keyword.lower() in name.lower() or keyword in strategy.get('content', ''):
            results['strategies'].append(strategy)
    
    # 搜索教训
    for lesson in knowledge.get('lessons', []):
        if keyword in lesson.get('content', ''):
            results['lessons'].append(lesson)
    
    return results


if __name__ == '__main__':
    kb = KnowledgeBase()
    kb.build()
    
    print()
    print("=" * 60)
    print("✅ 知识库构建完成！")
    print("=" * 60)
    print()
    print("使用方法:")
    print("  from 构建智能知识库 import query_knowledge")
    print("  results = query_knowledge('止损')")
    print()
