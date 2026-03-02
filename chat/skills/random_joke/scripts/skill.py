"""
随机笑话技能 - 获取随机笑话

A skill for getting random jokes to add humor to conversations.
"""

import random
from typing import Dict, Any
import sys
import os

# Add project root to path for local testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import BaseSkill with fallback for standalone execution
try:
    from skills.base import BaseSkill
except ImportError:
    # Fallback for standalone execution
    from base import BaseSkill


class RandomJokeSkill(BaseSkill):
    """随机笑话技能"""

    def __init__(self):
        super().__init__()
        # 初始化笑话库
        self.jokes = [
            {
                "joke": "为什么程序员喜欢用黑色背景？因为亮色背景会吸引虫子！",
                "category": "程序员笑话",
                "length": 20
            },
            {
                "joke": "程序员去餐厅点餐：\"我要一份炒饭，不要放盐。\" 服务员：\"好的，不放盐。\" 程序员：\"等等，还是放盐吧，我刚刚说的是默认值。\"",
                "category": "程序员笑话",
                "length": 35
            },
            {
                "joke": "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 == Dec 25。",
                "category": "程序员笑话",
                "length": 25
            },
            {
                "joke": "键盘上哪个键最帅？F4，因为 F4 有四个！",
                "category": "程序员笑话",
                "length": 18
            },
            {
                "joke": "程序员的最爱：咖啡、代码、还有无限循环。",
                "category": "程序员笑话",
                "length": 15
            },
            {
                "joke": "为什么自行车不会自己摔倒？因为它有两轮（two-wheel）！",
                "category": "日常笑话",
                "length": 18
            },
            {
                "joke": "为什么数学书总是很忧伤？因为它有太多问题（problems）！",
                "category": "日常笑话",
                "length": 20
            },
            {
                "joke": "为什么番茄变红了？因为它看到了沙拉酱！",
                "category": "日常笑话",
                "length": 15
            },
            {
                "joke": "什么动物最爱上网？蜘蛛，因为它整天在网上！",
                "category": "儿童笑话",
                "length": 16
            },
            {
                "joke": "为什么小鸟不会用电脑？因为它的爪子太小，按不了键盘！",
                "category": "儿童笑话",
                "length": 19
            },
            {
                "joke": "什么鱼最聪明？金鱼，因为它住在金鱼缸（think tank）里！",
                "category": "儿童笑话",
                "length": 18
            },
            {
                "joke": "为什么香蕉总是打电话？因为它有手机（hand phone）！",
                "category": "谐音梗笑话",
                "length": 16
            },
            {
                "joke": "为什么西瓜那么重？因为它有籽（重量）！",
                "category": "谐音梗笑话",
                "length": 15
            },
            {
                "joke": "为什么电脑永远不会感冒？因为它有 Windows（窗户）！",
                "category": "谐音梗笑话",
                "length": 16
            },
            {
                "joke": "为什么海星总是那么受欢迎？因为它是个 star（明星）！",
                "category": "冷知识笑话",
                "length": 17
            },
            {
                "joke": "为什么恐龙不会用手机？因为它们的爪子太大了！",
                "category": "冷知识笑话",
                "length": 16
            },
            {
                "joke": "为什么书永远不会无聊？因为它总是有故事！",
                "category": "冷知识笑话",
                "length": 16
            },
            {
                "joke": "程序员对女朋友说：\"如果你能修复我的代码，我就嫁给你。\" 女朋友说：\"那我宁愿单身一辈子。\"",
                "category": "程序员笑话",
                "length": 28
            },
            {
                "joke": "为什么程序员讨厌大自然？因为那里有太多 bugs（虫子）！",
                "category": "程序员笑话",
                "length": 18
            },
            {
                "joke": "为什么程序员总是带着备用眼镜？因为他们害怕看不到代码！",
                "category": "程序员笑话",
                "length": 20
            }
        ]

    def get_name(self) -> str:
        return "random_joke"

    def get_description(self) -> str:
        return "获取一个随机笑话，为对话增添趣味性。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行获取随机笑话

        Args:
            **kwargs: 其他参数（此技能无需参数）

        Returns:
            Dict[str, Any]: 笑话信息
        """
        try:
            # 随机选择一个笑话
            selected_joke = random.choice(self.jokes)
            
            # 构建返回结果
            result = {
                "joke": selected_joke["joke"],
                "category": selected_joke["category"],
                "length": selected_joke["length"],
                "language": "zh-CN"
            }
            
            return result

        except Exception as e:
            return {
                "error": f"获取笑话失败: {str(e)}"
            }


if __name__ == "__main__":
    skill = RandomJokeSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"\n测试执行:")
    for i in range(3):
        print(f"\n笑话 {i+1}:")
        print(skill.execute())