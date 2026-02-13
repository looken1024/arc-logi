#!/usr/bin/env python3
"""
将科学文献 PDF 转换为 Markdown，用于分析和审阅。

此脚本专门用于转换学术论文、整理文献，
并为文献综述工作流做准备。
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional
from markitdown import MarkItDown
from datetime import datetime


def extract_metadata_from_filename(filename: str) -> Dict[str, str]:
    """
    尝试从文件名中提取元数据。
    支持的模式：Author_Year_Title.pdf
    """
    metadata = {}
    
    # 移除扩展名
    name = Path(filename).stem
    
    # 尝试提取年份
    year_match = re.search(r'\b(19|20)\d{2}\b', name)
    if year_match:
        metadata['year'] = year_match.group()
    
    # 按下划线或连字符分割
    parts = re.split(r'[_\-]', name)
    if len(parts) >= 2:
        metadata['author'] = parts[0].replace('_', ' ')
        metadata['title'] = ' '.join(parts[1:]).replace('_', ' ')
    else:
        metadata['title'] = name.replace('_', ' ')
    
    return metadata


def convert_paper(
    md: MarkItDown,
    input_file: Path,
    output_dir: Path,
    organize_by_year: bool = False
) -> tuple[bool, Dict]:
    """
    将单篇论文转换为带元数据提取的 Markdown。
    
    Args:
        md: MarkItDown 实例
        input_file: PDF 文件路径
        output_dir: 输出目录
        organize_by_year: 是否按年份归类到子目录
        
    Returns:
        元组 (是否成功, 元数据字典)
    """
    try:
        print(f"正在转换：{input_file.name}")
        
        # 转换为 Markdown
        result = md.convert(str(input_file))
        
        # 从文件名提取元数据
        metadata = extract_metadata_from_filename(input_file.name)
        metadata['source_file'] = input_file.name
        metadata['converted_date'] = datetime.now().isoformat()
        
        # 如果文件名中没有标题，尝试从内容中提取
        if 'title' not in metadata and result.title:
            metadata['title'] = result.title
        
        # 创建输出路径
        if organize_by_year and 'year' in metadata:
            output_subdir = output_dir / metadata['year']
            output_subdir.mkdir(parents=True, exist_ok=True)
        else:
            output_subdir = output_dir
            output_subdir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_subdir / f"{input_file.stem}.md"
        
        # 创建带 front matter 的格式化 Markdown
        content = "---\n"
        content += f"title: \"{metadata.get('title', input_file.stem)}\"\n"
        if 'author' in metadata:
            content += f"author: \"{metadata['author']}\"\n"
        if 'year' in metadata:
            content += f"year: {metadata['year']}\n"
        content += f"source: \"{metadata['source_file']}\"\n"
        content += f"converted: \"{metadata['converted_date']}\"\n"
        content += "---\n\n"
        
        # 添加标题
        content += f"# {metadata.get('title', input_file.stem)}\n\n"
        
        # 添加文档信息部分
        content += "## 文档信息\n\n"
        if 'author' in metadata:
            content += f"**作者**: {metadata['author']}\n"
        if 'year' in metadata:
            content += f"**年份**: {metadata['year']}\n"
        content += f"**源文件**: {metadata['source_file']}\n"
        content += f"**转换时间**: {metadata['converted_date']}\n\n"
        content += "---\n\n"
        
        # 添加内容
        content += result.text_content
        
        # 写入文件
        output_file.write_text(content, encoding='utf-8')
        
        print(f"✓ 已保存到：{output_file}")
        
        return True, metadata
        
    except Exception as e:
        print(f"✗ 转换 {input_file.name} 时出错：{str(e)}")
        return False, {'source_file': input_file.name, 'error': str(e)}


def create_index(papers: List[Dict], output_dir: Path):
    """创建所有已转换论文的索引/目录。"""
    
    # 按年份（如有）和标题排序
    papers_sorted = sorted(
        papers,
        key=lambda x: (x.get('year', '9999'), x.get('title', ''))
    )
    
    # 创建 Markdown 索引
    index_content = "# 文献综述索引\n\n"
    index_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    index_content += f"**论文总数**: {len(papers)}\n\n"
    index_content += "---\n\n"
    
    # 按年份分组
    by_year = {}
    for paper in papers_sorted:
        year = paper.get('year', '未知')
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(paper)
    
    # 按年份输出
    for year in sorted(by_year.keys()):
        index_content += f"## {year}\n\n"
        for paper in by_year[year]:
            title = paper.get('title', paper.get('source_file', '未知'))
            author = paper.get('author', '未知作者')
            source = paper.get('source_file', '')
            
            # 创建 Markdown 文件链接
            md_file = Path(source).stem + ".md"
            if 'year' in paper and paper['year'] != '未知':
                md_file = f"{paper['year']}/{md_file}"
            
            index_content += f"- **{title}**\n"
            index_content += f"  - 作者：{author}\n"
            index_content += f"  - 源文件：{source}\n"
            index_content += f"  - [阅读 Markdown]({md_file})\n\n"
    
    # 写入索引
    index_file = output_dir / "INDEX.md"
    index_file.write_text(index_content, encoding='utf-8')
    print(f"\n✓ 已创建索引：{index_file}")
    
    # 同时创建 JSON 目录
    catalog_file = output_dir / "catalog.json"
    with open(catalog_file, 'w', encoding='utf-8') as f:
        json.dump(papers_sorted, f, indent=2, ensure_ascii=False)
    print(f"✓ 已创建目录：{catalog_file}")


def main():
    parser = argparse.ArgumentParser(
        description="将科学文献 PDF 转换为 Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 转换目录中的所有 PDF
  python convert_literature.py papers/ output/
  
  # 按年份归类
  python convert_literature.py papers/ output/ --organize-by-year
  
  # 创建所有论文的索引
  python convert_literature.py papers/ output/ --create-index
  
文件名命名规范：
  为获得最佳效果，请使用以下模式命名 PDF：
    Author_Year_Title.pdf
    
  示例：
    Smith_2023_Machine_Learning_Applications.pdf
    Jones_2022_Climate_Change_Analysis.pdf
        """
    )
    
    parser.add_argument('input_dir', type=Path, help='包含 PDF 文件的目录')
    parser.add_argument('output_dir', type=Path, help='Markdown 文件输出目录')
    parser.add_argument(
        '--organize-by-year', '-y',
        action='store_true',
        help='将输出按年份归类到子目录'
    )
    parser.add_argument(
        '--create-index', '-i',
        action='store_true',
        help='创建所有论文的索引/目录'
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='递归搜索子目录'
    )
    
    args = parser.parse_args()
    
    # 验证输入
    if not args.input_dir.exists():
        print(f"错误：输入目录 '{args.input_dir}' 不存在")
        sys.exit(1)
    
    if not args.input_dir.is_dir():
        print(f"错误：'{args.input_dir}' 不是目录")
        sys.exit(1)
    
    # 查找 PDF 文件
    if args.recursive:
        pdf_files = list(args.input_dir.rglob("*.pdf"))
    else:
        pdf_files = list(args.input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("未找到 PDF 文件")
        sys.exit(1)
    
    print(f"找到 {len(pdf_files)} 个 PDF 文件")
    
    # 创建 MarkItDown 实例
    md = MarkItDown()
    
    # 转换所有论文
    results = []
    success_count = 0
    
    for pdf_file in pdf_files:
        success, metadata = convert_paper(
            md,
            pdf_file,
            args.output_dir,
            args.organize_by_year
        )
        
        if success:
            success_count += 1
            results.append(metadata)
    
    # 如请求则创建索引
    if args.create_index and results:
        create_index(results, args.output_dir)
    
    # 打印摘要
    print("\n" + "="*50)
    print("转换摘要")
    print("="*50)
    print(f"论文总数：     {len(pdf_files)}")
    print(f"成功：         {success_count}")
    print(f"失败：         {len(pdf_files) - success_count}")
    print(f"成功率：       {success_count/len(pdf_files)*100:.1f}%")
    
    sys.exit(0 if success_count == len(pdf_files) else 1)


if __name__ == '__main__':
    main()


