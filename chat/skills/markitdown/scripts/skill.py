"""
MarkItDown 技能 - 将文件和办公文档转换为 Markdown

支持 PDF、DOCX、PPTX、XLSX、图像、音频、HTML、CSV、JSON、XML、ZIP、YouTube URL、EPub 等格式。
"""

from typing import Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from skills.base import BaseSkill
except ImportError:
    from base import BaseSkill


class MarkItDownSkill(BaseSkill):
    """将文件和办公文档转换为 Markdown 的技能"""

    def get_name(self) -> str:
        return "markitdown"

    def get_description(self) -> str:
        return "将文件和办公文档（PDF、DOCX、PPTX、XLSX、图片、音频等）转换为 Markdown 格式。"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要转换的文件路径"
                },
                "enable_ocr": {
                    "type": "boolean",
                    "description": "启用 OCR 识别图片中的文字",
                    "default": True
                },
                "enable_table_detection": {
                    "type": "boolean",
                    "description": "启用表格检测",
                    "default": True
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str, enable_ocr: bool = True, enable_table_detection: bool = True, **kwargs) -> Dict[str, Any]:
        """
        执行文件到 Markdown 的转换

        Args:
            file_path: 要转换的文件路径
            enable_ocr: 是否启用 OCR
            enable_table_detection: 是否启用表格检测

        Returns:
            Dict[str, Any]: 转换结果
        """
        try:
            from markitdown import MarkItDown

            md = MarkItDown(enable_ocr=enable_ocr, enable_table_detection=enable_table_detection)
            result = md.convert(file_path)

            return {
                "success": True,
                "file_name": os.path.basename(file_path),
                "text_content": result.text_content,
                "metadata": {
                    "file_path": file_path,
                    "enable_ocr": enable_ocr,
                    "enable_table_detection": enable_table_detection
                }
            }

        except FileNotFoundError:
            return {
                "success": False,
                "error": f"文件未找到: {file_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"转换失败: {str(e)}"
            }


if __name__ == "__main__":
    skill = MarkItDownSkill()
    print(f"Skill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"\nTest execution:")
    print(skill.execute("test.pdf"))
