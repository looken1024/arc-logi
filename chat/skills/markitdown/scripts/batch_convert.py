#!/usr/bin/env python3
"""
使用 MarkItDown 批量将多个文件转换为 Markdown。

此脚本演示如何高效地将目录中的多个文件批量转换为 Markdown 格式。
"""

import argparse
from pathlib import Path
from typing import List, Optional
from markitdown import MarkItDown
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys


def convert_file(md: MarkItDown, file_path: Path, output_dir: Path, verbose: bool = False) -> tuple[bool, str, str]:
    """
    将单个文件转换为 Markdown。
    
    Args:
        md: MarkItDown 实例
        file_path: 输入文件路径
        output_dir: 输出文件目录
        verbose: 是否打印详细信息
        
    Returns:
        元组 (是否成功, 输入路径, 消息)
    """
    try:
        if verbose:
            print(f"正在转换：{file_path}")
        
        result = md.convert(str(file_path))
        
        # 创建输出路径
        output_file = output_dir / f"{file_path.stem}.md"
        
        # 写入带元数据头的内容
        content = f"# {result.title or file_path.stem}\n\n"
        content += f"**来源**: {file_path.name}\n"
        content += f"**格式**: {file_path.suffix}\n\n"
        content += "---\n\n"
        content += result.text_content
        
        output_file.write_text(content, encoding='utf-8')
        
        return True, str(file_path), f"✓ 已转换为 {output_file.name}"
        
    except Exception as e:
        return False, str(file_path), f"✗ 错误：{str(e)}"


def batch_convert(
    input_dir: Path,
    output_dir: Path,
    extensions: Optional[List[str]] = None,
    recursive: bool = False,
    workers: int = 4,
    verbose: bool = False,
    enable_plugins: bool = False
) -> dict:
    """
    批量转换目录中的文件。
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        extensions: 要转换的文件扩展名列表（例如 ['.pdf', '.docx']）
        recursive: 是否搜索子目录
        workers: 并行工作线程数
        verbose: 是否打印详细信息
        enable_plugins: 是否启用 MarkItDown 插件
        
    Returns:
        包含转换统计信息的字典
    """
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 未指定时使用默认扩展名
    if extensions is None:
        extensions = ['.pdf', '.docx', '.pptx', '.xlsx', '.html', '.jpg', '.png']
    
    # 查找文件
    files = []
    if recursive:
        for ext in extensions:
            files.extend(input_dir.rglob(f"*{ext}"))
    else:
        for ext in extensions:
            files.extend(input_dir.glob(f"*{ext}"))
    
    if not files:
        print(f"未找到扩展名为 {', '.join(extensions)} 的文件")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    print(f"找到 {len(files)} 个待转换文件")
    
    # 创建 MarkItDown 实例
    md = MarkItDown(enable_plugins=enable_plugins)
    
    # 并行转换文件
    results = {
        'total': len(files),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(convert_file, md, file_path, output_dir, verbose): file_path
            for file_path in files
        }
        
        for future in as_completed(futures):
            success, path, message = future.result()
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'file': path,
                'success': success,
                'message': message
            })
            
            print(message)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="使用 MarkItDown 批量将文件转换为 Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 转换目录中的所有 PDF
  python batch_convert.py papers/ output/ --extensions .pdf
  
  # 递归转换多种格式
  python batch_convert.py documents/ markdown/ --extensions .pdf .docx .pptx -r
  
  # 使用 8 个并行工作线程
  python batch_convert.py input/ output/ --workers 8
  
  # 启用插件
  python batch_convert.py input/ output/ --plugins
        """
    )
    
    parser.add_argument('input_dir', type=Path, help='输入目录')
    parser.add_argument('output_dir', type=Path, help='输出目录')
    parser.add_argument(
        '--extensions', '-e',
        nargs='+',
        help='要转换的文件扩展名（例如 .pdf .docx）'
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='递归搜索子目录'
    )
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='并行工作线程数（默认：4）'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    parser.add_argument(
        '--plugins', '-p',
        action='store_true',
        help='启用 MarkItDown 插件'
    )
    
    args = parser.parse_args()
    
    # 验证输入目录
    if not args.input_dir.exists():
        print(f"错误：输入目录 '{args.input_dir}' 不存在")
        sys.exit(1)
    
    if not args.input_dir.is_dir():
        print(f"错误：'{args.input_dir}' 不是目录")
        sys.exit(1)
    
    # 执行批量转换
    results = batch_convert(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        extensions=args.extensions,
        recursive=args.recursive,
        workers=args.workers,
        verbose=args.verbose,
        enable_plugins=args.plugins
    )
    
    # 打印摘要
    print("\n" + "="*50)
    print("转换摘要")
    print("="*50)
    print(f"总文件数：     {results['total']}")
    print(f"成功：         {results['success']}")
    print(f"失败：         {results['failed']}")
    print(f"成功率：       {results['success']/results['total']*100:.1f}%" if results['total'] > 0 else "N/A")
    
    # 显示失败的文件
    if results['failed'] > 0:
        print("\n转换失败的文件：")
        for detail in results['details']:
            if not detail['success']:
                print(f"  - {detail['file']}: {detail['message']}")
    
    sys.exit(0 if results['failed'] == 0 else 1)


if __name__ == '__main__':
    main()


