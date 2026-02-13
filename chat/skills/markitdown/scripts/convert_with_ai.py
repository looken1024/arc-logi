#!/usr/bin/env python3
"""
使用 AI 增强的图像描述将文档转换为 Markdown。

此脚本演示如何使用 MarkItDown 结合 OpenRouter 为文档中的图像
（PowerPoint、含图像的 PDF 等）生成详细描述。
"""

import argparse
import os
import sys
from pathlib import Path
from markitdown import MarkItDown
from openai import OpenAI


# 不同用途的预定义提示词
PROMPTS = {
    'scientific': """
分析此科学图像或图表。请提供：
1. 可视化类型（图表、图形、显微镜图、示意图等）
2. 关键数据点、趋势或模式
3. 轴标签、图例和比例尺
4. 显著特征或发现
5. 科学背景和意义
请精确、专业、详细。
    """.strip(),
    
    'presentation': """
描述此演示文稿幻灯片图像。包括：
1. 主要视觉元素及其排列
2. 传达的关键要点或信息
3. 呈现的数据或信息
4. 视觉层次和重点
描述应清晰且信息丰富。
    """.strip(),
    
    'general': """
详细描述此图像。包括：
1. 主要主体和对象
2. 视觉构图和布局
3. 文字内容（如有）
4. 显著细节
5. 整体背景和用途
请全面且准确。
    """.strip(),
    
    'data_viz': """
分析此数据可视化。请提供：
1. 图表类型（柱状图、折线图、散点图、饼图等）
2. 变量和轴
3. 数据范围和比例
4. 关键模式、趋势或异常值
5. 统计洞察
注重定量准确性。
    """.strip(),
    
    'medical': """
描述此医学图像。包括：
1. 医学影像类型（X 光、MRI、CT、显微镜等）
2. 可见的解剖结构
3. 显著发现或异常
4. 图像质量和对比度
5. 临床相关性
请专业且精确。
    """.strip()
}


def convert_with_ai(
    input_file: Path,
    output_file: Path,
    api_key: str,
    model: str = "anthropic/claude-sonnet-4.5",
    prompt_type: str = "general",
    custom_prompt: str = None
) -> bool:
    """
    使用 AI 图像描述将文件转换为 Markdown。
    
    Args:
        input_file: 输入文件路径
        output_file: 输出 Markdown 文件路径
        api_key: OpenRouter API 密钥
        model: 模型名称（默认：anthropic/claude-sonnet-4.5）
        prompt_type: 提示词类型
        custom_prompt: 自定义提示词（覆盖 prompt_type）
        
    Returns:
        成功返回 True，否则返回 False
    """
    try:
        # 初始化 OpenRouter 客户端（兼容 OpenAI）
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # 选择提示词
        if custom_prompt:
            prompt = custom_prompt
        else:
            prompt = PROMPTS.get(prompt_type, PROMPTS['general'])
        
        print(f"使用模型：{model}")
        print(f"提示词类型：{prompt_type if not custom_prompt else '自定义'}")
        print(f"正在转换：{input_file}")
        
        # 创建带 AI 支持的 MarkItDown
        md = MarkItDown(
            llm_client=client,
            llm_model=model,
            llm_prompt=prompt
        )
        
        # 转换文件
        result = md.convert(str(input_file))
        
        # 创建带元数据的输出
        content = f"# {result.title or input_file.stem}\n\n"
        content += f"**来源**: {input_file.name}\n"
        content += f"**格式**: {input_file.suffix}\n"
        content += f"**AI 模型**: {model}\n"
        content += f"**提示词类型**: {prompt_type if not custom_prompt else '自定义'}\n\n"
        content += "---\n\n"
        content += result.text_content
        
        # 写入输出
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')
        
        print(f"✓ 转换成功：{output_file}")
        return True
        
    except Exception as e:
        print(f"✗ 错误：{str(e)}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="使用 AI 增强的图像描述将文档转换为 Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
可用的提示词类型：
  scientific    - 用于科学图表、图形和图表
  presentation  - 用于演示文稿幻灯片
  general       - 通用图像描述
  data_viz      - 用于数据可视化和图表
  medical       - 用于医学影像

示例：
  # 转换科学论文
  python convert_with_ai.py paper.pdf output.md --prompt-type scientific
  
  # 使用自定义模型转换演示文稿
  python convert_with_ai.py slides.pptx slides.md --model anthropic/claude-sonnet-4.5 --prompt-type presentation
  
  # 使用自定义提示词和高级视觉模型
  python convert_with_ai.py diagram.png diagram.md --model anthropic/claude-sonnet-4.5 --custom-prompt "描述此技术图表"
  
  # 通过环境变量设置 API 密钥
  export OPENROUTER_API_KEY="sk-or-v1-..."
  python convert_with_ai.py image.jpg image.md

环境变量：
  OPENROUTER_API_KEY    OpenRouter API 密钥（未通过 --api-key 传递时必需）

常用模型（通过 --model 使用）：
  anthropic/claude-sonnet-4.5 - 推荐用于科学视觉
  anthropic/claude-opus-4.5   - 高级视觉模型
  openai/gpt-4o              - GPT-4 Omni（支持视觉）
  openai/gpt-4-vision        - GPT-4 Vision
  google/gemini-pro-vision   - Gemini Pro Vision
        """
    )
    
    parser.add_argument('input', type=Path, help='输入文件')
    parser.add_argument('output', type=Path, help='输出 Markdown 文件')
    parser.add_argument(
        '--api-key', '-k',
        help='OpenRouter API 密钥（或设置 OPENROUTER_API_KEY 环境变量）'
    )
    parser.add_argument(
        '--model', '-m',
        default='anthropic/claude-sonnet-4.5',
        help='通过 OpenRouter 使用的模型（默认：anthropic/claude-sonnet-4.5）'
    )
    parser.add_argument(
        '--prompt-type', '-t',
        choices=list(PROMPTS.keys()),
        default='general',
        help='使用的提示词类型（默认：general）'
    )
    parser.add_argument(
        '--custom-prompt', '-p',
        help='自定义提示词（覆盖 --prompt-type）'
    )
    parser.add_argument(
        '--list-prompts', '-l',
        action='store_true',
        help='列出可用的提示词类型并退出'
    )
    
    args = parser.parse_args()
    
    # 列出提示词并退出
    if args.list_prompts:
        print("可用的提示词类型：\n")
        for name, prompt in PROMPTS.items():
            print(f"[{name}]")
            print(prompt)
            print("\n" + "="*60 + "\n")
        sys.exit(0)
    
    # 获取 API 密钥
    api_key = args.api_key or os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("错误：需要 OpenRouter API 密钥。请设置 OPENROUTER_API_KEY 环境变量或使用 --api-key")
        print("在此获取 API 密钥：https://openrouter.ai/keys")
        sys.exit(1)
    
    # 验证输入文件
    if not args.input.exists():
        print(f"错误：输入文件 '{args.input}' 不存在")
        sys.exit(1)
    
    # 转换文件
    success = convert_with_ai(
        input_file=args.input,
        output_file=args.output,
        api_key=api_key,
        model=args.model,
        prompt_type=args.prompt_type,
        custom_prompt=args.custom_prompt
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()


