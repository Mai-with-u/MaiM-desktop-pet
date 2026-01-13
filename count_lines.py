#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统计代码行数"""

import os
from pathlib import Path

def count_lines_in_file(filepath):
    """统计单个文件的行数"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"无法读取文件 {filepath}: {e}")
        return 0

def count_lines_in_directory(directory):
    """统计目录中的代码行数"""
    total_lines = 0
    file_stats = {}
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                lines = count_lines_in_file(filepath)
                total_lines += lines
                
                # 获取相对于目录的路径
                rel_path = os.path.relpath(filepath, directory)
                file_stats[rel_path] = lines
    
    return total_lines, file_stats

def main():
    """主函数"""
    print("=" * 60)
    print("代码行数统计")
    print("=" * 60)
    
    # 统计 src 目录
    src_lines, src_stats = count_lines_in_directory('src')
    print(f"\nsrc 目录总行数: {src_lines}")
    
    # 显示每个文件的行数
    print("\n各文件行数详情:")
    print("-" * 60)
    for filepath, lines in sorted(src_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{lines:6d} 行 - {filepath}")
    
    # 统计其他文件
    other_files = []
    for file in ['main.py', 'config.py', 'requirements.txt']:
        if os.path.exists(file):
            lines = count_lines_in_file(file)
            other_files.append((file, lines))
    
    print("\n其他重要文件:")
    print("-" * 60)
    other_total = 0
    for file, lines in other_files:
        print(f"{lines:6d} 行 - {file}")
        other_total += lines
    
    # 总计
    grand_total = src_lines + other_total
    print("\n" + "=" * 60)
    print(f"总计: {grand_total} 行")
    print(f"  - src 目录: {src_lines} 行")
    print(f"  - 其他文件: {other_total} 行")
    print("=" * 60)

if __name__ == '__main__':
    main()
