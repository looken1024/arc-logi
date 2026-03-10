"""
天气查询技能 - 获取指定城市的当前天气信息

A skill for getting current weather information for a specific city.
"""

import sys
import os
from typing import Dict, Any
import requests

# Add project root to path for local testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import BaseSkill with fallback for standalone execution
try:
    from skills.base import BaseSkill
except ImportError:
    # Fallback for standalone execution
    from base import BaseSkill


class WeatherSkill(BaseSkill):
    """获取指定城市当前天气信息的技能"""

    def get_name(self) -> str:
        return "get_weather"

    def get_description(self) -> str:
        return "获取指定城市的当前天气信息，包括温度、天气状况、风力、湿度、体感温度、能见度、气压等。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，例如：北京、上海、广州、深圳",
                }
            },
            "required": ["city"]
        }

    def execute(self, city: str, **kwargs) -> Dict[str, Any]:
        """
        执行天气查询

        Args:
            city: 城市名称
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 天气信息
        """
        try:
            api_key = 'eb4e86c2b456401cbae17a8d9eab0712'
            
            # 1. 获取城市位置ID
            geocode_url = f'https://geoapi.qweather.com/v2/city/lookup?location={city}&key={api_key}'
            geocode_response = requests.get(geocode_url, timeout=10)
            geocode_data = geocode_response.json()
            
            if geocode_data.get('code') != '200':
                return {
                    "error": f"城市 '{city}' 未找到，请检查城市名称是否正确"
                }
            
            location = geocode_data['location'][0]
            location_id = location['id']
            city_name = location['name']
            city_adm = location.get('adm2', location.get('adm1', ''))
            
            # 2. 获取当前天气
            weather_url = f'https://devapi.qweather.com/v7/weather/now?location={location_id}&key={api_key}'
            weather_response = requests.get(weather_url, timeout=10)
            weather_data = weather_response.json()
            
            if weather_data.get('code') != '200':
                return {
                    "error": "天气数据获取失败，请稍后重试"
                }
            
            now = weather_data['now']
            
            result = {
                "success": True,
                "city": city_name,
                "province": city_adm,
                "temp": now['temp'],
                "text": now['text'],
                "windDir": now['windDir'],
                "windScale": now['windScale'],
                "humidity": now['humidity'],
                "feelsLike": now['feelsLike'],
                "vis": now['vis'],
                "pressure": now['pressure'],
                "updateTime": weather_data.get('updateTime', ''),
                "description": self._get_human_description(city_name, now)
            }
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                "error": "请求超时，请检查网络连接"
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                "error": f"查询失败: {str(e)}"
            }

    def _get_human_description(self, city: str, weather_data: Dict[str, Any]) -> str:
        """生成人性化的天气描述"""
        temp = weather_data['temp']
        text = weather_data['text']
        wind_scale = weather_data['windScale']
        humidity = weather_data['humidity']
        
        # 温度描述
        temp_num = float(temp)
        if temp_num <= 0:
            temp_desc = "寒冷"
        elif temp_num <= 10:
            temp_desc = "较冷"
        elif temp_num <= 20:
            temp_desc = "凉爽"
        elif temp_num <= 28:
            temp_desc = "舒适"
        elif temp_num <= 35:
            temp_desc = "炎热"
        else:
            temp_desc = "酷热"
        
        # 风力描述
        wind_scale_num = int(wind_scale)
        if wind_scale_num <= 2:
            wind_desc = "微风"
        elif wind_scale_num <= 4:
            wind_desc = "和风"
        elif wind_scale_num <= 6:
            wind_desc = "强风"
        else:
            wind_desc = "大风"
        
        # 湿度描述
        humidity_num = int(humidity)
        if humidity_num < 30:
            humidity_desc = "干燥"
        elif humidity_num < 60:
            humidity_desc = "舒适"
        elif humidity_num < 80:
            humidity_desc = "潮湿"
        else:
            humidity_desc = "非常潮湿"
        
        return f"{city}当前天气：{text}，气温{temp}℃（{temp_desc}），{wind_desc}{wind_scale}级，湿度{humidity}%（{humidity_desc}）。"


# 独立测试
if __name__ == "__main__":
    skill = WeatherSkill()
    print(f"技能名称: {skill.name}")
    print(f"描述: {skill.description}")
    print(f"\n测试执行 - 北京:")
    print(skill.execute(city="北京"))
    print(f"\n测试执行 - 上海:")
    print(skill.execute(city="上海"))