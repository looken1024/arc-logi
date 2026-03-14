"""
产品经理技能 - 生成有建设性的产品方案

A skill for generating constructive product proposals and ideas.
"""

import json
import random
from typing import Dict, Any, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill


class ProductManagerSkill(BaseSkill):
    """产品经理技能 - 生成产品方案"""

    def get_name(self) -> str:
        return "product_manager"

    def get_description(self) -> str:
        return "生成针对特定领域、问题或创意的产品方案，提供产品概念、功能规划、市场定位等建设性建议。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "产品主题、领域或问题描述，例如：'社交应用'、'电商平台'、'健康管理'"
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["brief", "normal", "detailed"],
                    "description": "方案详细程度：brief（简要）、normal（正常）、detailed（详细）",
                    "default": "normal"
                },
                "target_audience": {
                    "type": "string",
                    "description": "目标用户群体，例如：'年轻人'、'上班族'、'老年人'",
                    "default": "一般消费者"
                },
                "innovation_level": {
                    "type": "string",
                    "enum": ["incremental", "breakthrough", "radical"],
                    "description": "创新程度：incremental（渐进式改进）、breakthrough（突破性创新）、radical（颠覆性创新）",
                    "default": "incremental"
                }
            },
            "required": ["topic"]
        }

    def execute(self, topic: str, detail_level: str = "normal", 
                target_audience: str = "一般消费者", innovation_level: str = "incremental", 
                **kwargs) -> Dict[str, Any]:
        """
        执行产品方案生成

        Args:
            topic: 产品主题
            detail_level: 详细程度
            target_audience: 目标用户
            innovation_level: 创新程度
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 产品方案
        """
        try:
            # 尝试使用OpenAI生成高质量方案
            try:
                return self._generate_with_ai(topic, detail_level, target_audience, innovation_level)
            except Exception as ai_error:
                print(f"AI生成失败，使用模板方案: {ai_error}")
                # 回退到模板方案
                return self._generate_with_template(topic, detail_level, target_audience, innovation_level)
                
        except Exception as e:
            return {
                "success": False,
                "error": f"生成产品方案失败: {str(e)}"
            }

    def _generate_with_ai(self, topic: str, detail_level: str, target_audience: str, 
                         innovation_level: str) -> Dict[str, Any]:
        """使用OpenAI生成产品方案"""
        import openai
        
        # 构建提示词
        prompt = self._build_prompt(topic, detail_level, target_audience, innovation_level)
        
        # 调用OpenAI API
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位资深产品经理，擅长提出有建设性的产品方案和创意。请严格按照指定的JSON格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # 解析JSON响应
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # 确保必要字段存在
        result.setdefault("success", True)
        result.setdefault("topic", topic)
        result.setdefault("target_audience", target_audience)
        
        return result

    def _build_prompt(self, topic: str, detail_level: str, target_audience: str, 
                     innovation_level: str) -> str:
        """构建生成产品方案的提示词"""
        
        detail_map = {
            "brief": "简要（3-5个关键点）",
            "normal": "正常（5-8个关键点）",
            "detailed": "详细（8-12个关键点，包含实施细节）"
        }
        
        innovation_map = {
            "incremental": "渐进式改进（在现有产品基础上优化）",
            "breakthrough": "突破性创新（引入新的技术或模式）",
            "radical": "颠覆性创新（完全改变行业规则）"
        }
        
        detail_desc = detail_map.get(detail_level, "正常")
        innovation_desc = innovation_map.get(innovation_level, "渐进式改进")
        
        prompt = f"""
请针对以下需求生成一个产品方案：

**主题**: {topic}
**目标用户**: {target_audience}
**详细程度**: {detail_desc}
**创新程度**: {innovation_desc}

请生成一个完整的产品方案，严格按照以下JSON格式输出：

{{
  "success": true,
  "topic": "{topic}",
  "target_audience": "{target_audience}",
  "product_name": "产品名称（富有创意且相关）",
  "product_concept": "产品核心理念（1-2句话描述）",
  "key_features": ["功能1", "功能2", "功能3", ...],
  "market_positioning": "市场定位描述（目标市场、差异化优势）",
  "innovation_points": ["创新点1", "创新点2", ...],
  "implementation_considerations": "实施注意事项（技术、市场、运营等方面）",
  "next_steps": ["下一步1", "下一步2", ...]
}}

要求：
1. 产品名称要有创意且与主题相关
2. 产品概念要清晰明确，解决用户痛点
3. 关键功能要具体可行，符合创新程度要求
4. 市场定位要准确，有差异化优势
5. 创新点要突出，符合指定的创新程度
6. 实施注意事项要实际可行
7. 下一步行动要具体可操作

请只输出JSON，不要有任何其他文字。
"""
        return prompt

    def _generate_with_template(self, topic: str, detail_level: str, 
                               target_audience: str, innovation_level: str) -> Dict[str, Any]:
        """使用模板生成产品方案（OpenAI不可用时的回退方案）"""
        
        # 根据主题选择模板
        templates = self._get_product_templates()
        
        # 找到最相关的模板
        matched_template = None
        for template in templates:
            if any(keyword in topic.lower() for keyword in template["keywords"]):
                matched_template = template
                break
        
        if not matched_template:
            matched_template = templates[0]  # 使用第一个模板
        
        # 根据详细程度调整功能数量
        feature_count = {"brief": 3, "normal": 5, "detailed": 8}[detail_level]
        innovation_count = {"brief": 1, "normal": 2, "detailed": 3}[detail_level]
        
        # 生成产品名称
        prefixes = ["智能", "智慧", "创新", "未来", "灵动", "卓越", "超级", "极致"]
        suffixes = ["平台", "系统", "助手", "管家", "引擎", "中心", "空间", "生态"]
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        product_name = f"{prefix}{topic}{suffix}"
        
        # 根据创新程度调整描述
        innovation_descriptions = {
            "incremental": f"在现有{topic}基础上进行优化改进，提供更好的用户体验和功能",
            "breakthrough": f"采用新技术或新模式重新定义{topic}，提供独特的价值主张",
            "radical": f"完全颠覆传统的{topic}方式，创造全新的市场机会"
        }
        
        product_concept = innovation_descriptions.get(innovation_level, matched_template["concept"])
        
        # 生成关键功能
        base_features = matched_template["features"]
        if len(base_features) > feature_count:
            key_features = random.sample(base_features, feature_count)
        else:
            key_features = base_features
            # 补充一些通用功能
            generic_features = [
                "用户个性化设置",
                "数据分析和报告",
                "多平台同步",
                "社交分享功能",
                "智能推荐系统",
                "实时通知提醒",
                "离线工作模式",
                "多语言支持"
            ]
            while len(key_features) < feature_count:
                extra = random.choice(generic_features)
                if extra not in key_features:
                    key_features.append(extra)
        
        # 生成创新点
        innovation_points = []
        innovation_templates = [
            f"创新的{random.choice(['交互设计', '算法模型', '商业模式', '用户体验'])}",
            f"整合{random.choice(['AI技术', '区块链', '物联网', '大数据分析'])}",
            f"独特的{random.choice(['盈利模式', '用户增长策略', '社区运营', '内容生态'])}",
            f"革命性的{random.choice(['性能优化', '成本控制', '效率提升', '安全防护'])}"
        ]
        for i in range(innovation_count):
            if i < len(innovation_templates):
                innovation_points.append(innovation_templates[i])
            else:
                innovation_points.append(f"创新方向{i+1}")
        
        # 生成市场定位
        market_positioning = f"面向{target_audience}的{topic}解决方案，提供{random.choice(['高效', '便捷', '智能', '经济', '可靠'])}的{random.choice(['服务', '体验', '工具', '平台'])}"
        
        # 实施注意事项
        implementation_considerations = random.choice([
            "需要关注数据隐私和安全合规",
            "初期需聚焦核心功能，快速迭代",
            "注重用户体验测试和反馈收集",
            "考虑技术栈的可扩展性和维护性",
            "制定明确的用户增长和留存策略"
        ])
        
        # 下一步行动
        next_steps = [
            "进行目标用户深度访谈",
            "完成竞品分析和市场调研",
            "设计产品原型和用户流程图",
            "制定技术架构和开发计划",
            "规划MVP版本功能范围"
        ]
        if detail_level == "brief":
            next_steps = next_steps[:2]
        elif detail_level == "normal":
            next_steps = next_steps[:4]
        
        return {
            "success": True,
            "topic": topic,
            "target_audience": target_audience,
            "product_name": product_name,
            "product_concept": product_concept,
            "key_features": key_features,
            "market_positioning": market_positioning,
            "innovation_points": innovation_points,
            "implementation_considerations": implementation_considerations,
            "next_steps": next_steps
        }

    def _get_product_templates(self) -> List[Dict[str, Any]]:
        """获取产品模板列表"""
        return [
            {
                "keywords": ["社交", "社区", "聊天", "交友", "沟通"],
                "concept": "连接人与人，创造有意义的社交体验",
                "features": [
                    "个人资料和兴趣标签",
                    "智能匹配算法",
                    "实时聊天和视频通话",
                    "兴趣小组和社区",
                    "内容分享和发现",
                    "隐私和安全控制",
                    "活动组织和参与",
                    "成就和奖励系统"
                ]
            },
            {
                "keywords": ["电商", "购物", "零售", "商城", "商品"],
                "concept": "提供便捷、智能、个性化的购物体验",
                "features": [
                    "个性化商品推荐",
                    "智能搜索和筛选",
                    "安全便捷的支付",
                    "订单跟踪和管理",
                    "客户评价和评分",
                    "促销和优惠活动",
                    "物流信息实时更新",
                    "售后服务和退换货"
                ]
            },
            {
                "keywords": ["健康", "医疗", "健身", "养生", "保健"],
                "concept": "帮助用户管理健康，提升生活质量",
                "features": [
                    "健康数据记录和追踪",
                    "个性化健康建议",
                    "运动计划和指导",
                    "饮食管理和推荐",
                    "医疗咨询和预约",
                    "症状自查和评估",
                    "用药提醒和管理",
                    "健康社区和分享"
                ]
            },
            {
                "keywords": ["教育", "学习", "培训", "课程", "知识"],
                "concept": "提供个性化、高效、有趣的学习体验",
                "features": [
                    "个性化学习路径",
                    "互动式课程内容",
                    "学习进度跟踪",
                    "知识点测试和评估",
                    "学习社区和讨论",
                    "教师辅导和答疑",
                    "学习资源推荐",
                    "学习成果认证"
                ]
            },
            {
                "keywords": ["工作", "办公", "效率", "协作", "管理"],
                "concept": "提升工作效率和团队协作效果",
                "features": [
                    "任务管理和分配",
                    "团队协作和沟通",
                    "文档共享和编辑",
                    "日程安排和会议",
                    "项目进度跟踪",
                    "工作报告和分析",
                    "文件存储和管理",
                    "工作流程自动化"
                ]
            }
        ]


if __name__ == "__main__":
    skill = ProductManagerSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"\n测试执行:")
    print(json.dumps(skill.execute(topic="社交应用"), ensure_ascii=False, indent=2))