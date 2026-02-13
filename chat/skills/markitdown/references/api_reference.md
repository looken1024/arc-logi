# MarkItDown API 参考

## 核心类

### MarkItDown

用于将文件转换为 Markdown 的主类。

```python
from markitdown import MarkItDown

md = MarkItDown(
    llm_client=None,
    llm_model=None,
    llm_prompt=None,
    docintel_endpoint=None,
    enable_plugins=False
)
```

#### 参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `llm_client` | OpenAI client | `None` | 用于 AI 图像描述的 OpenAI 兼容客户端 |
| `llm_model` | str | `None` | 用于图像描述的模型名称（如 "anthropic/claude-sonnet-4.5"） |
| `llm_prompt` | str | `None` | 图像描述的自定义提示 |
| `docintel_endpoint` | str | `None` | Azure Document Intelligence 端点 |
| `enable_plugins` | bool | `False` | 启用第三方插件 |

#### 方法

##### convert()

将文件转换为 Markdown。

```python
result = md.convert(
    source,
    file_extension=None
)
```

**参数**：
- `source` (str)：要转换的文件路径
- `file_extension` (str, 可选)：覆盖文件扩展名检测

**返回**：`DocumentConverterResult` 对象

**示例**：
```python
result = md.convert("document.pdf")
print(result.text_content)
```

##### convert_stream()

从二进制文件流转换。

```python
result = md.convert_stream(
    stream,
    file_extension
)
```

**参数**：
- `stream` (BinaryIO)：二进制文件对象（如以 `"rb"` 模式打开的文件）
- `file_extension` (str)：用于确定转换方法的文件扩展名（如 ".pdf"）

**返回**：`DocumentConverterResult` 对象

**示例**：
```python
with open("document.pdf", "rb") as f:
    result = md.convert_stream(f, file_extension=".pdf")
    print(result.text_content)
```

**重要**：流必须以二进制模式（`"rb"`）打开，而非文本模式。

## 结果对象

### DocumentConverterResult

转换操作的结果。

#### 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `text_content` | str | 转换后的 Markdown 文本 |
| `title` | str | 文档标题（如果可用） |

#### 示例

```python
result = md.convert("paper.pdf")

# 访问内容
content = result.text_content

# 访问标题（如果可用）
title = result.title
```

## 自定义转换器

你可以通过实现 `DocumentConverter` 接口来创建自定义文档转换器。

### DocumentConverter 接口

```python
from markitdown import DocumentConverter

class CustomConverter(DocumentConverter):
    def convert(self, stream, file_extension):
        """
        从二进制流转换文档。
        
        参数：
            stream (BinaryIO)：二进制文件对象
            file_extension (str)：文件扩展名（如 ".custom"）
            
        返回：
            DocumentConverterResult：转换结果
        """
        # 你的转换逻辑
        pass
```

### 注册自定义转换器

```python
from markitdown import MarkItDown, DocumentConverter, DocumentConverterResult

class MyCustomConverter(DocumentConverter):
    def convert(self, stream, file_extension):
        content = stream.read().decode('utf-8')
        markdown_text = f"# 自定义格式\n\n{content}"
        return DocumentConverterResult(
            text_content=markdown_text,
            title="自定义文档"
        )

# 创建 MarkItDown 实例
md = MarkItDown()

# 为 .custom 文件注册自定义转换器
md.register_converter(".custom", MyCustomConverter())

# 使用
result = md.convert("myfile.custom")
```

## 插件系统

### 查找插件

在 GitHub 上搜索 `#markitdown-plugin` 标签。

### 使用插件

```python
from markitdown import MarkItDown

# 启用插件
md = MarkItDown(enable_plugins=True)
result = md.convert("document.pdf")
```

### 创建插件

插件是向 MarkItDown 注册转换器的 Python 包。

**插件结构**：
```
my-markitdown-plugin/
├── setup.py
├── my_plugin/
│   ├── __init__.py
│   └── converter.py
└── README.md
```

**setup.py**：
```python
from setuptools import setup

setup(
    name="markitdown-my-plugin",
    version="0.1.0",
    packages=["my_plugin"],
    entry_points={
        "markitdown.plugins": [
            "my_plugin = my_plugin.converter:MyConverter",
        ],
    },
)
```

**converter.py**：
```python
from markitdown import DocumentConverter, DocumentConverterResult

class MyConverter(DocumentConverter):
    def convert(self, stream, file_extension):
        # 你的转换逻辑
        content = stream.read()
        markdown = self.process(content)
        return DocumentConverterResult(
            text_content=markdown,
            title="我的文档"
        )
    
    def process(self, content):
        # 处理内容
        return "# 转换后的内容\n\n..."
```

## AI 增强转换

### 使用 OpenRouter 进行图像描述

```python
from markitdown import MarkItDown
from openai import OpenAI

# 初始化 OpenRouter 客户端（OpenAI 兼容 API）
client = OpenAI(
    api_key="your-openrouter-api-key",
    base_url="https://openrouter.ai/api/v1"
)

# 创建带 AI 支持的 MarkItDown
md = MarkItDown(
    llm_client=client,
    llm_model="anthropic/claude-sonnet-4.5",  # 推荐用于科学视觉
    llm_prompt="详细描述此图像以用于科学文档"
)

# 转换包含图像的文件
result = md.convert("presentation.pptx")
```

### 通过 OpenRouter 可用的模型

具有视觉能力的热门模型：
- `anthropic/claude-sonnet-4.5` - **推荐用于科学视觉**
- `anthropic/claude-opus-4.5` - 高级视觉模型
- `openai/gpt-4o` - GPT-4 Omni
- `openai/gpt-4-vision` - GPT-4 Vision
- `google/gemini-pro-vision` - Gemini Pro Vision

完整列表请见 https://openrouter.ai/models。

### 自定义提示

```python
# 用于科学图表
scientific_prompt = """
分析此科学图表或图形。描述：
1. 可视化类型（图表、图形、示意图等）
2. 关键数据点或趋势
3. 标签和坐标轴
4. 科学意义
请保持精确和技术性。
"""

md = MarkItDown(
    llm_client=client,
    llm_model="anthropic/claude-sonnet-4.5",
    llm_prompt=scientific_prompt
)
```

## Azure Document Intelligence

### 设置

1. 创建 Azure Document Intelligence 资源
2. 获取端点 URL
3. 配置认证

### 使用

```python
from markitdown import MarkItDown

md = MarkItDown(
    docintel_endpoint="https://YOUR-RESOURCE.cognitiveservices.azure.com/"
)

result = md.convert("complex_document.pdf")
```

### 认证

设置环境变量：
```bash
export AZURE_DOCUMENT_INTELLIGENCE_KEY="your-key"
```

或以编程方式传入凭据。

## 错误处理

```python
from markitdown import MarkItDown

md = MarkItDown()

try:
    result = md.convert("document.pdf")
    print(result.text_content)
except FileNotFoundError:
    print("文件未找到")
except ValueError as e:
    print(f"无效的文件格式：{e}")
except Exception as e:
    print(f"转换错误：{e}")
```

## 性能提示

### 1. 复用 MarkItDown 实例

```python
# 好的做法：创建一次，多次使用
md = MarkItDown()

for file in files:
    result = md.convert(file)
    process(result)
```

### 2. 大文件使用流式处理

```python
# 用于大文件
with open("large_file.pdf", "rb") as f:
    result = md.convert_stream(f, file_extension=".pdf")
```

### 3. 批量处理

```python
from concurrent.futures import ThreadPoolExecutor

md = MarkItDown()

def convert_file(filepath):
    return md.convert(filepath)

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(convert_file, file_list)
```

## 破坏性变更（v0.0.1 到 v0.1.0）

1. **依赖项**：现在按可选功能组组织
   ```bash
   # 旧版
   pip install markitdown
   
   # 新版
   pip install 'markitdown[all]'
   ```

2. **convert_stream()**：现在需要二进制文件对象
   ```python
   # 旧版（也接受文本）
   with open("file.pdf", "r") as f:  # 文本模式
       result = md.convert_stream(f)
   
   # 新版（仅二进制）
   with open("file.pdf", "rb") as f:  # 二进制模式
       result = md.convert_stream(f, file_extension=".pdf")
   ```

3. **DocumentConverter 接口**：改为从流而非文件路径读取
   - 不再创建临时文件
   - 更节省内存
   - 插件需要更新

## 版本兼容性

- **Python**：需要 3.10 或更高版本
- **依赖项**：请参阅 `setup.py` 的版本约束
- **OpenAI**：兼容 OpenAI Python SDK v1.0+

## 环境变量

| 变量 | 描述 | 示例 |
|------|------|------|
| `OPENROUTER_API_KEY` | 用于图像描述的 OpenRouter API 密钥 | `sk-or-v1-...` |
| `AZURE_DOCUMENT_INTELLIGENCE_KEY` | Azure DI 认证密钥 | `key123...` |
| `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | Azure DI 端点 | `https://...` |
