"""
思维导图技能 - 总结文本关键点并以图形化方式展示

从输入文本中提取关键点，构建层次结构，并生成思维导图的可视化表示。
支持生成 Mermaid 代码、文本树状图和 JSON 结构。
"""

from typing import Dict, Any, List, Optional
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill


class MindMapSkill(BaseSkill):
    """生成文本的思维导图"""

    def get_name(self) -> str:
        return "mind_map"

    def get_description(self) -> str:
        return "从输入文本中提取关键点，构建层次结构，并生成思维导图的可视化表示（Mermaid 代码、文本树状图等）。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要分析的文本内容"
                },
                "language": {
                    "type": "string",
                    "enum": ["auto", "zh", "en"],
                    "description": "文本语言：auto(自动检测)、zh(中文)、en(英文)",
                    "default": "auto"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "思维导图最大深度",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 5
                },
                "generate_mermaid": {
                    "type": "boolean",
                    "description": "是否生成 Mermaid 代码",
                    "default": True
                },
                "generate_text_tree": {
                    "type": "boolean",
                    "description": "是否生成文本树状图",
                    "default": True
                }
            },
            "required": ["text"]
        }

    def execute(self, text: str, language: str = "auto", max_depth: int = 3,
                generate_mermaid: bool = True, generate_text_tree: bool = True, **kwargs) -> Dict[str, Any]:
        """
        执行思维导图生成

        Args:
            text: 要分析的文本
            language: 文本语言
            max_depth: 最大深度
            generate_mermaid: 是否生成 Mermaid 代码
            generate_text_tree: 是否生成文本树状图

        Returns:
            Dict[str, Any]: 思维导图结果
        """
        try:
            # 1. 提取关键点并构建层次结构
            hierarchy = self._extract_key_points(text, language, max_depth)
            
            # 2. 生成输出
            result = {
                "success": True,
                "hierarchy": hierarchy,
                "summary": self._generate_summary(hierarchy)
            }
            
            # 3. 生成 Mermaid 代码
            if generate_mermaid:
                result["mermaid_code"] = self._generate_mermaid(hierarchy)
                result["mermaid_diagram_type"] = "mindmap"
            
            # 4. 生成文本树状图
            if generate_text_tree:
                result["text_tree"] = self._generate_text_tree(hierarchy)
            
            # 5. 添加统计信息
            result["stats"] = self._compute_stats(hierarchy)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"生成思维导图失败: {str(e)}"
            }

    def _extract_key_points(self, text: str, language: str, max_depth: int) -> Dict[str, Any]:
        """
        使用 OpenAI API 提取关键点并构建层次结构
        
        Returns:
            层次结构字典，例如：
            {
                "id": "root",
                "label": "核心主题",
                "children": [...]
            }
        """
        try:
            import openai
            
            # 构建提示词
            prompt = self._build_extraction_prompt(text, language, max_depth)
            
            # 调用 OpenAI API
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的文本分析助手，擅长从文本中提取关键点并构建清晰的层次结构。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # 解析 JSON 响应
            content = response.choices[0].message.content
            hierarchy = json.loads(content)
            
            # 验证并标准化结构
            return self._validate_hierarchy(hierarchy)
            
        except ImportError:
            # OpenAI 库未安装，使用简单的启发式方法作为后备
            return self._fallback_extraction(text, language, max_depth)
        except Exception as e:
            # API 调用失败，使用后备方法
            print(f"OpenAI API 调用失败: {e}")
            return self._fallback_extraction(text, language, max_depth)

    def _build_extraction_prompt(self, text: str, language: str, max_depth: int) -> str:
        """构建用于关键点提取的提示词"""
        lang_instruction = "使用中文" if language == "zh" else "Use English" if language == "en" else "使用与文本相同的语言"
        
        prompt = f"""
请分析以下文本，提取关键点并构建一个层次清晰的思维导图结构。

要求：
1. {lang_instruction}
2. 最大深度不超过 {max_depth} 层
3. 每个节点包含 "id"（唯一标识符）、"label"（简短标签）和 "children"（子节点数组，可为空）字段
4. 根节点的 id 为 "root"，label 为文本的核心主题总结
5. 结构应该逻辑清晰，反映文本的主要观点和支持细节

文本内容：
```
{text}
```

请以 JSON 格式返回思维导图结构，例如：
{{
  "id": "root",
  "label": "核心主题",
  "children": [
    {{
      "id": "node1",
      "label": "主要观点1",
      "children": [...]
    }}
  ]
}}

只返回 JSON 数据，不要有其他内容。
"""
        return prompt.strip()

    def _validate_hierarchy(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """验证并标准化层次结构"""
        if not isinstance(hierarchy, dict):
            hierarchy = {"id": "root", "label": "文本主题", "children": []}
        
        # 确保必要字段存在
        hierarchy.setdefault("id", "root")
        hierarchy.setdefault("label", "文本主题")
        hierarchy.setdefault("children", [])
        
        # 递归验证子节点
        def validate_node(node):
            node.setdefault("id", f"node_{id(node)}")
            node.setdefault("label", "")
            node.setdefault("children", [])
            if isinstance(node["children"], list):
                for child in node["children"]:
                    if isinstance(child, dict):
                        validate_node(child)
                    else:
                        child = {"id": f"node_{id(child)}", "label": str(child), "children": []}
            else:
                node["children"] = []
        
        validate_node(hierarchy)
        return hierarchy

    def _fallback_extraction(self, text: str, language: str, max_depth: int) -> Dict[str, Any]:
        """
        后备的关键点提取方法
        使用简单的文本分割和关键词提取
        """
        # 简化实现：将文本分割为句子，取前几个作为关键点
        import re
        
        # 分割句子
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 限制句子数量
        max_sentences = min(len(sentences), 10)
        sentences = sentences[:max_sentences]
        
        # 构建简单层次结构
        children = []
        for i, sentence in enumerate(sentences):
            # 截断过长的句子
            label = sentence[:50] + "..." if len(sentence) > 50 else sentence
            children.append({
                "id": f"node_{i}",
                "label": label,
                "children": []
            })
        
        return {
            "id": "root",
            "label": "文本摘要",
            "children": children
        }

    def _generate_summary(self, hierarchy: Dict[str, Any]) -> str:
        """从层次结构生成文本摘要"""
        root_label = hierarchy.get("label", "文本主题")
        children_count = len(hierarchy.get("children", []))
        
        if children_count == 0:
            return f"文本主题: {root_label}"
        
        # 收集第一层子节点的标签
        first_level = [child.get("label", "") for child in hierarchy.get("children", [])[:3]]
        summary_parts = [f"主题: {root_label}"]
        
        if first_level:
            summary_parts.append(f"主要观点: {', '.join(first_level)}")
            if children_count > 3:
                summary_parts.append(f"共 {children_count} 个关键点")
        
        return " | ".join(summary_parts)

    def _generate_mermaid(self, hierarchy: Dict[str, Any]) -> str:
        """生成 Mermaid mindmap 代码"""
        def build_mermaid_node(node, indent=0):
            lines = []
            prefix = "  " * indent
            label = node["label"].replace('"', '\\"')
            
            if indent == 0:
                lines.append(f'{prefix}root("{label}")')
            else:
                lines.append(f'{prefix}{label}')
            
            for child in node.get("children", []):
                child_lines = build_mermaid_node(child, indent + 1)
                lines.extend(child_lines)
            
            return lines
        
        lines = ["mindmap"]
        lines.extend(build_mermaid_node(hierarchy))
        
        return "\n".join(lines)

    def _generate_text_tree(self, hierarchy: Dict[str, Any]) -> str:
        """生成文本树状图"""
        def build_text_node(node, prefix="", is_last=True):
            lines = []
            current_prefix = prefix + ("└── " if is_last else "├── ")
            lines.append(f"{current_prefix}{node['label']}")
            
            children = node.get("children", [])
            child_count = len(children)
            
            for i, child in enumerate(children):
                child_prefix = prefix + ("    " if is_last else "│   ")
                child_is_last = i == child_count - 1
                child_lines = build_text_node(child, child_prefix, child_is_last)
                lines.extend(child_lines)
            
            return lines
        
        lines = [hierarchy.get("label", "思维导图")]
        children = hierarchy.get("children", [])
        child_count = len(children)
        
        for i, child in enumerate(children):
            is_last = i == child_count - 1
            child_lines = build_text_node(child, "", is_last)
            lines.extend(child_lines)
        
        return "\n".join(lines)

    def _compute_stats(self, hierarchy: Dict[str, Any]) -> Dict[str, Any]:
        """计算思维导图统计信息"""
        def count_nodes(node):
            total = 1
            for child in node.get("children", []):
                total += count_nodes(child)
            return total
        
        def max_depth(node, current=1):
            depths = [current]
            for child in node.get("children", []):
                depths.append(max_depth(child, current + 1))
            return max(depths)
        
        total_nodes = count_nodes(hierarchy)
        depth = max_depth(hierarchy)
        
        return {
            "total_nodes": total_nodes,
            "max_depth": depth,
            "root_label": hierarchy.get("label", "")
        }


if __name__ == "__main__":
    skill = MindMapSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    
    # 测试执行
    test_text = """人工智能是计算机科学的一个分支，旨在创造能够执行通常需要人类智能的任务的机器。
这些任务包括视觉感知、语音识别、决策和语言翻译。
人工智能可以分为弱人工智能和强人工智能。
弱人工智能专注于特定任务，而强人工智能则具有通用智能，可以执行任何人类智能任务。
机器学习是人工智能的一个子领域，它使计算机能够在没有明确编程的情况下学习。
深度学习是机器学习的一种，使用神经网络模拟人脑的工作方式。"""
    
    print(f"\nTest execution:")
    result = skill.execute(text=test_text, max_depth=3)
    print(json.dumps(result, ensure_ascii=False, indent=2))