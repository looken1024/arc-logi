"""
日期时间技能 - 获取当前日期和时间信息
"""

from datetime import datetime, timezone
from typing import Dict, Any
import locale
import sys
import os

# 添加父目录到 Python 路径（用于导入 base）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base import BaseSkill


class DateSkill(BaseSkill):
    """获取当前日期和时间的技能"""
    
    def get_name(self) -> str:
        return "get_current_date"
    
    def get_description(self) -> str:
        return "获取当前日期和时间信息，包括年、月、日、星期、时间等。用户询问今天几号、现在几点、星期几等问题时调用此技能。"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "format": {
                    "type": "string",
                    "enum": ["full", "date", "time", "datetime", "timestamp"],
                    "description": "返回格式：full(完整信息)、date(仅日期)、time(仅时间)、datetime(日期时间)、timestamp(时间戳)",
                    "default": "full"
                },
                "timezone": {
                    "type": "string",
                    "description": "时区，例如：Asia/Shanghai, UTC, America/New_York",
                    "default": "Asia/Shanghai"
                }
            },
            "required": []
        }
    
    def execute(self, format: str = "full", timezone: str = "Asia/Shanghai", **kwargs) -> Dict[str, Any]:
        """
        执行获取日期时间
        
        Args:
            format: 返回格式
            timezone: 时区
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 日期时间信息
        """
        try:
            # 获取当前时间
            now = datetime.now()
            
            # 设置中文 locale（如果可用）
            try:
                locale.setlocale(locale.LC_TIME, 'zh_CN.UTF-8')
            except:
                try:
                    locale.setlocale(locale.LC_TIME, 'Chinese')
                except:
                    pass  # 使用默认 locale
            
            # 星期映射
            weekdays_cn = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
            weekday_cn = weekdays_cn[now.weekday()]
            
            # 构建返回数据
            result = {
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "weekday": weekday_cn,
                "weekday_number": now.weekday() + 1,  # 1-7
                "timezone": timezone
            }
            
            # 根据格式返回不同内容
            if format == "date":
                result["formatted"] = now.strftime("%Y年%m月%d日")
                result["iso_format"] = now.strftime("%Y-%m-%d")
            elif format == "time":
                result["formatted"] = now.strftime("%H:%M:%S")
                result["iso_format"] = now.strftime("%H:%M:%S")
            elif format == "datetime":
                result["formatted"] = now.strftime("%Y年%m月%d日 %H:%M:%S")
                result["iso_format"] = now.isoformat()
            elif format == "timestamp":
                result["timestamp"] = int(now.timestamp())
                result["timestamp_ms"] = int(now.timestamp() * 1000)
            else:  # full
                result["formatted"] = f"{now.year}年{now.month}月{now.day}日 {weekday_cn} {now.strftime('%H:%M:%S')}"
                result["iso_format"] = now.isoformat()
                result["timestamp"] = int(now.timestamp())
            
            # 添加人性化描述
            result["description"] = self._get_human_description(now, weekday_cn)
            
            return result
            
        except Exception as e:
            return {
                "error": f"获取日期时间失败: {str(e)}"
            }
    
    def _get_human_description(self, dt: datetime, weekday: str) -> str:
        """生成人性化的时间描述"""
        hour = dt.hour
        
        # 时段判断
        if 5 <= hour < 12:
            time_period = "上午"
            greeting = "早上好"
        elif 12 <= hour < 14:
            time_period = "中午"
            greeting = "中午好"
        elif 14 <= hour < 18:
            time_period = "下午"
            greeting = "下午好"
        elif 18 <= hour < 22:
            time_period = "晚上"
            greeting = "晚上好"
        else:
            time_period = "深夜"
            greeting = "夜深了"
        
        return f"现在是{dt.year}年{dt.month}月{dt.day}日，{weekday}，{time_period}{hour}点{dt.minute}分。{greeting}！"


# 用于独立测试
if __name__ == "__main__":
    skill = DateSkill()
    print(f"技能名称: {skill.name}")
    print(f"技能描述: {skill.description}")
    print(f"\n测试执行:")
    print(skill.execute())
