# MarkItDown 使用示例

本文档提供了在各种场景中使用 MarkItDown 的实际示例。

## 基础示例

### 1. 简单文件转换

```python
from markitdown import MarkItDown

md = MarkItDown()

# 转换 PDF
result = md.convert("research_paper.pdf")
print(result.text_content)

# 转换 Word 文档
result = md.convert("manuscript.docx")
print(result.text_content)

# 转换 PowerPoint
result = md.convert("presentation.pptx")
print(result.text_content)
```

### 2. 保存到文件

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")

with open("output.md", "w", encoding="utf-8") as f:
    f.write(result.text_content)
```

### 3. 从流转换

```python
from markitdown import MarkItDown

md = MarkItDown()

with open("document.pdf", "rb") as f:
    result = md.convert_stream(f, file_extension=".pdf")
    print(result.text_content)
```

## 科学工作流程

### 转换研究论文

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()

# 转换目录中的所有论文
papers_dir = Path("research_papers/")
output_dir = Path("markdown_papers/")
output_dir.mkdir(exist_ok=True)

for paper in papers_dir.glob("*.pdf"):
    result = md.convert(str(paper))
    
    # 使用原始文件名保存
    output_file = output_dir / f"{paper.stem}.md"
    output_file.write_text(result.text_content)
    
    print(f"已转换：{paper.name}")
```

### 从 Excel 提取表格

```python
from markitdown import MarkItDown

md = MarkItDown()

# 将 Excel 转换为 Markdown 表格
result = md.convert("experimental_data.xlsx")

# 结果包含 Markdown 格式的表格
print(result.text_content)

# 保存以供进一步处理
with open("data_tables.md", "w") as f:
    f.write(result.text_content)
```

### 处理演示文稿幻灯片

```python
from markitdown import MarkItDown
from openai import OpenAI

# 使用 AI 描述图像
client = OpenAI()
md = MarkItDown(
    llm_client=client,
    llm_model="anthropic/claude-sonnet-4.5",
    llm_prompt="描述此科学幻灯片，重点关注数据和关键发现"
)

result = md.convert("conference_talk.pptx")

# 带元数据保存
output = f"""# 会议演讲

{result.text_content}
"""

with open("talk_notes.md", "w") as f:
    f.write(output)
```

## AI 增强转换

### 详细图像描述

```python
from markitdown import MarkItDown
from openai import OpenAI

# 初始化 OpenRouter 客户端
client = OpenAI(
    api_key="your-openrouter-api-key",
    base_url="https://openrouter.ai/api/v1"
)

# 科学图表分析
scientific_prompt = """
分析此科学图表。描述：
- 可视化类型（图表、显微镜图像、示意图等）
- 关键数据点和趋势
- 坐标轴、标签和图例
- 科学意义
请保持技术性和精确性。
"""

md = MarkItDown(
    llm_client=client,
    llm_model="anthropic/claude-sonnet-4.5",  # 推荐用于科学视觉
    llm_prompt=scientific_prompt
)

# 转换带图表的论文
result = md.convert("paper_with_figures.pdf")
print(result.text_content)
```

### 不同文件使用不同提示

```python
from markitdown import MarkItDown
from openai import OpenAI

# 初始化 OpenRouter 客户端
client = OpenAI(
    api_key="your-openrouter-api-key",
    base_url="https://openrouter.ai/api/v1"
)

# 科学论文 - 使用 Claude 进行技术分析
scientific_md = MarkItDown(
    llm_client=client,
    llm_model="anthropic/claude-sonnet-4.5",
    llm_prompt="以技术精度描述科学图表"
)

# 演示文稿 - 使用 GPT-4o 进行视觉理解
presentation_md = MarkItDown(
    llm_client=client,
    llm_model="anthropic/claude-sonnet-4.5",
    llm_prompt="总结幻灯片内容和关键视觉元素"
)

# 为每个文件使用适当的实例
paper_result = scientific_md.convert("research.pdf")
slides_result = presentation_md.convert("talk.pptx")
```

## 批量处理

### 处理多个文件

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()

files_to_convert = [
    "paper1.pdf",
    "data.xlsx",
    "presentation.pptx",
    "notes.docx"
]

for file in files_to_convert:
    try:
        result = md.convert(file)
        output = Path(file).stem + ".md"
        
        with open(output, "w") as f:
            f.write(result.text_content)
        
        print(f"✓ {file} -> {output}")
    except Exception as e:
        print(f"✗ 转换 {file} 出错：{e}")
```

### 并行处理

```python
from markitdown import MarkItDown
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def convert_file(filepath):
    md = MarkItDown()
    result = md.convert(filepath)
    
    output = Path(filepath).stem + ".md"
    with open(output, "w") as f:
        f.write(result.text_content)
    
    return filepath, output

files = list(Path("documents/").glob("*.pdf"))

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(convert_file, [str(f) for f in files])
    
    for input_file, output_file in results:
        print(f"已转换：{input_file} -> {output_file}")
```

## 集成示例

### 文献综述管线

```python
from markitdown import MarkItDown
from pathlib import Path
import json

md = MarkItDown()

# 转换论文并创建元数据
papers_dir = Path("literature/")
output_dir = Path("literature_markdown/")
output_dir.mkdir(exist_ok=True)

catalog = []

for paper in papers_dir.glob("*.pdf"):
    result = md.convert(str(paper))
    
    # 保存 Markdown
    md_file = output_dir / f"{paper.stem}.md"
    md_file.write_text(result.text_content)
    
    # 存储元数据
    catalog.append({
        "title": result.title or paper.stem,
        "source": paper.name,
        "markdown": str(md_file),
        "word_count": len(result.text_content.split())
    })

# 保存目录
with open(output_dir / "catalog.json", "w") as f:
    json.dump(catalog, f, indent=2)
```

### 数据提取管线

```python
from markitdown import MarkItDown
import re

md = MarkItDown()

# 将 Excel 数据转换为 Markdown
result = md.convert("experimental_results.xlsx")

# 提取表格（Markdown 表格以 | 开头）
tables = []
current_table = []
in_table = False

for line in result.text_content.split('\n'):
    if line.strip().startswith('|'):
        in_table = True
        current_table.append(line)
    elif in_table:
        if current_table:
            tables.append('\n'.join(current_table))
            current_table = []
        in_table = False

# 处理每个表格
for i, table in enumerate(tables):
    print(f"表格 {i+1}：")
    print(table)
    print("\n" + "="*50 + "\n")
```

### YouTube 文字稿分析

```python
from markitdown import MarkItDown

md = MarkItDown()

# 获取文字稿
video_url = "https://www.youtube.com/watch?v=VIDEO_ID"
result = md.convert(video_url)

# 保存文字稿
with open("lecture_transcript.md", "w") as f:
    f.write(f"# 讲座文字稿\n\n")
    f.write(f"**来源**：{video_url}\n\n")
    f.write(result.text_content)
```

## 错误处理

### 健壮的转换

```python
from markitdown import MarkItDown
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

md = MarkItDown()

def safe_convert(filepath):
    """带错误处理的文件转换。"""
    try:
        result = md.convert(filepath)
        output = Path(filepath).stem + ".md"
        
        with open(output, "w") as f:
            f.write(result.text_content)
        
        logger.info(f"成功转换 {filepath}")
        return True
    
    except FileNotFoundError:
        logger.error(f"文件未找到：{filepath}")
        return False
    
    except ValueError as e:
        logger.error(f"{filepath} 的文件格式无效：{e}")
        return False
    
    except Exception as e:
        logger.error(f"转换 {filepath} 时发生意外错误：{e}")
        return False

# 使用
files = ["paper.pdf", "data.xlsx", "slides.pptx"]
results = [safe_convert(f) for f in files]

print(f"成功转换 {sum(results)}/{len(files)} 个文件")
```

## 高级用例

### 自定义元数据提取

```python
from markitdown import MarkItDown
import re
from datetime import datetime

md = MarkItDown()

def convert_with_metadata(filepath):
    result = md.convert(filepath)
    
    # 从内容中提取元数据
    metadata = {
        "file": filepath,
        "title": result.title,
        "converted_at": datetime.now().isoformat(),
        "word_count": len(result.text_content.split()),
        "char_count": len(result.text_content)
    }
    
    # 尝试查找作者
    author_match = re.search(r'(?:Author|By):\s*(.+?)(?:\n|$)', result.text_content)
    if author_match:
        metadata["author"] = author_match.group(1).strip()
    
    # 创建格式化输出
    output = f"""---
title: {metadata['title']}
author: {metadata.get('author', '未知')}
source: {metadata['file']}
converted: {metadata['converted_at']}
words: {metadata['word_count']}
---

{result.text_content}
"""
    
    return output, metadata

# 使用
content, meta = convert_with_metadata("paper.pdf")
print(meta)
```

### 按格式处理

```python
from markitdown import MarkItDown
from pathlib import Path

md = MarkItDown()

def process_by_format(filepath):
    path = Path(filepath)
    result = md.convert(filepath)
    
    if path.suffix == '.pdf':
        # 添加 PDF 特定元数据
        output = f"# PDF 文档：{path.stem}\n\n"
        output += result.text_content
    
    elif path.suffix == '.xlsx':
        # 添加表格计数
        table_count = result.text_content.count('|---')
        output = f"# Excel 数据：{path.stem}\n\n"
        output += f"**表格数**：{table_count}\n\n"
        output += result.text_content
    
    elif path.suffix == '.pptx':
        # 添加幻灯片计数
        slide_count = result.text_content.count('## Slide')
        output = f"# 演示文稿：{path.stem}\n\n"
        output += f"**幻灯片数**：{slide_count}\n\n"
        output += result.text_content
    
    else:
        output = result.text_content
    
    return output

# 使用
content = process_by_format("presentation.pptx")
print(content)
```
