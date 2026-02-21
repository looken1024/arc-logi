"""
联网新闻搜索技能 - 搜索最新新闻和事件

A skill for searching latest news and current events online.
"""

import requests
from typing import Dict, Any, List, Optional
import sys
import os
from datetime import datetime
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill


class WebSearchNewsSkill(BaseSkill):
    """联网搜索最新新闻和事件的技能"""

    def get_name(self) -> str:
        return "web_search_news"

    def get_description(self) -> str:
        return "联网搜索最新新闻、热点事件和时事信息。适用于用户询问最新消息、新闻事件等场景。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词或新闻主题，例如：'科技新闻'、'今日热点'、'2026年重大事件'"
                },
                "num_results": {
                    "type": "integer",
                    "description": "返回的新闻数量，默认为5条",
                    "default": 5
                },
                "category": {
                    "type": "string",
                    "enum": ["general", "tech", "business", "sports", "entertainment", "science", "health"],
                    "description": "新闻分类：general(综合)、tech(科技)、business(商业)、sports(体育)、entertainment(娱乐)、science(科学)、health(健康)",
                    "default": "general"
                },
                "language": {
                    "type": "string",
                    "enum": ["zh", "en"],
                    "description": "搜索语言：zh(中文)、en(英文)",
                    "default": "zh"
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, num_results: int = 5, category: str = "general", language: str = "zh", **kwargs) -> Dict[str, Any]:
        """
        执行联网新闻搜索

        Args:
            query: 搜索关键词
            num_results: 返回结果数量
            category: 新闻分类
            language: 搜索语言
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 搜索结果
        """
        try:
            search_query = self._build_search_query(query, category, language)
            
            results = self._search_news(search_query, num_results, language)
            
            if not results:
                return {
                    "success": True,
                    "query": query,
                    "category": category,
                    "language": language,
                    "count": 0,
                    "message": "未找到相关新闻，请尝试其他关键词",
                    "results": []
                }
            
            return {
                "success": True,
                "query": query,
                "category": category,
                "language": language,
                "count": len(results),
                "search_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}",
                "query": query
            }

    def _build_search_query(self, query: str, category: str, language: str) -> str:
        """构建搜索查询"""
        category_keywords = {
            "general": "",
            "tech": "科技",
            "business": "商业 财经",
            "sports": "体育",
            "entertainment": "娱乐",
            "science": "科学",
            "health": "健康 医疗"
        }
        
        category_suffix = category_keywords.get(category, "")
        
        if language == "zh":
            if category != "general" and category_suffix:
                return f"{query} {category_suffix} 新闻 最新"
            return f"{query} 新闻 最新"
        else:
            if category != "general" and category_suffix:
                return f"{query} {category_suffix} news latest"
            return f"{query} news latest"

    def _search_news(self, query: str, num_results: int, language: str) -> List[Dict[str, Any]]:
        """执行新闻搜索"""
        try:
            search_url = "https://html.duckduckgo.com/html/"
            params = {
                "q": query,
                "b": ""
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                import re
                results = []
                
                result_pattern = r'<a rel="nofollow" class="result__a" href="([^"]*)"[^>]*>([^<]*)</a>'
                snippet_pattern = r'<a class="result__snippet"[^>]*>([^<]*)</a>'
                
                titles = re.findall(result_pattern, response.text)
                snippets = re.findall(snippet_pattern, response.text)
                
                for i, (url, title) in enumerate(titles[:num_results]):
                    snippet = snippets[i] if i < len(snippets) else ""
                    results.append({
                        "title": title.strip(),
                        "url": url.strip(),
                        "snippet": snippet.strip() if snippet else ""
                    })
                
                if results:
                    return results
            
            return self._fallback_search(query, num_results, language)
            
        except Exception as e:
            return self._fallback_search(query, num_results, language)

    def _fallback_search(self, query: str, num_results: int, language: str) -> List[Dict[str, Any]]:
        """备用搜索方案 - 使用Bing API或返回提示"""
        try:
            if language == "zh":
                url = "https://www.bing.com/news/search"
            else:
                url = "https://www.bing.com/news/search"
            
            params = {
                "q": query,
                "format": "rss"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return [{
                    "title": f"关于 '{query}' 的最新新闻",
                    "url": f"https://www.bing.com/news/search?q={requests.utils.quote(query)}",
                    "snippet": "点击链接查看更多新闻详情"
                }]
            
        except:
            pass
        
        return [{
            "title": f"搜索: {query}",
            "url": f"https://www.google.com/search?q={requests.utils.quote(query)}&tbm=nws",
            "snippet": "点击链接查看最新新闻"
        }]


if __name__ == "__main__":
    skill = WebSearchNewsSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"\nTest execution:")
    print(skill.execute(query="人工智能"))
