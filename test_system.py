#!/usr/bin/env python3
"""测试脚本：测试文档上传和搜索功能"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.document_parser import DocumentParser
from app.core.text_splitter import TextSplitter
from app.core.index_manager import IndexManager


def create_test_file():
    """创建测试文档"""
    content = """# 企业知识库管理系统

## 第一章 系统概述

企业知识库管理系统是一个基于人工智能技术的智能知识管理平台，旨在帮助企业高效地组织、存储和检索内部知识资源。

### 1.1 系统目标

本系统的主要目标是实现文档的统一管理和存储，提供智能全文检索功能，支持多种文档格式的解析和处理，提高企业知识的利用效率。

### 1.2 核心功能

系统包含文档上传与管理、智能全文检索、关键词高亮显示等核心功能模块。支持 PDF、Word、Markdown、TXT 等多种格式的文档上传和管理。

## 第二章 技术架构

### 2.1 后端技术栈

后端采用 Python 语言开发，主要技术栈包括 Flask Web 框架、Whoosh 全文检索引擎、jieba 中文分词、PyPDF2 文档解析、python-docx Word 文档处理。

### 2.2 前端技术栈

前端采用 Vue 3 框架开发，主要技术栈包括 Vue 3 Composition API、Vite 构建工具、Vue Router 路由管理、Axios HTTP 客户端。

## 第三章 核心算法

### 3.1 BM25 算法

BM25 是一种基于概率检索模型的排序算法，它考虑了词频、逆文档频率和文档长度归一化等因素。BM25 算法能够提供精准的搜索结果排序。

### 3.2 文本切片策略

系统采用固定长度的文本切片策略，默认块大小为 512 字符，默认重叠大小为 50 字符，优先在句子结束处切分，确保语义连续性。

## 第四章 应用场景

### 4.1 企业内部知识库

企业可以将各类规章制度、技术文档、培训资料等上传到系统中，员工可以通过搜索快速找到所需信息。

### 4.2 客服知识库

客服团队可以将常见问题和解答整理成知识库，客服人员可以快速检索相关答案，提高服务效率。

### 4.3 研发知识库

研发团队可以将技术方案、API 文档、故障排查指南等存入知识库，方便团队成员查阅和学习。
"""
    filepath = '/tmp/test_kb_doc.md'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"测试文件已创建: {filepath}")
    print(f"文件大小: {len(content)} 字符")
    return filepath


def test_document_parser(filepath):
    """测试文档解析器"""
    print("\n=== 测试文档解析器 ===")
    parser = DocumentParser()
    result = parser.parse(filepath)
    
    print(f"文件名: {result['filename']}")
    print(f"全文长度: {len(result['full_text'])}")
    print(f"章节数量: {len(result['sections'])}")
    
    for i, sec in enumerate(result['sections']):
        print(f"  章节 {i+1}: {sec['title']} (长度: {len(sec['content'])})")
    
    return result


def test_text_splitter(sections):
    """测试文本切片器"""
    print("\n=== 测试文本切片器 ===")
    splitter = TextSplitter(chunk_size=200, chunk_overlap=30)
    chunks = splitter.split_sections(sections)
    
    print(f"切片数量: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"  块 {i+1}: 长度={len(chunk['text'])}, 章节={chunk['section'][:20]}...")
    
    if len(chunks) > 3:
        print(f"  ... 还有 {len(chunks) - 3} 个块")
    
    return chunks


def test_index_manager(chunks):
    """测试索引管理器"""
    print("\n=== 测试索引管理器 ===")
    
    index_dir = '/tmp/test_kb_index'
    if os.path.exists(index_dir):
        import shutil
        shutil.rmtree(index_dir)
    
    index_mgr = IndexManager(index_dir)
    
    # 添加文档
    added = index_mgr.add_document(
        doc_id='test_doc_001',
        filename='test_kb_doc.md',
        chunks=chunks
    )
    print(f"已添加 {added} 个文本块到索引")
    
    # 统计信息
    stats = index_mgr.get_stats()
    print(f"统计信息: {stats}")
    
    # 测试搜索
    print("\n--- 搜索测试 ---")
    
    test_queries = ['BM25 算法', '知识库', '技术架构', '客服']
    
    for query in test_queries:
        results = index_mgr.search(query, top_k=2)
        print(f"\n搜索: '{query}'")
        print(f"  找到 {len(results)} 个结果")
        for i, r in enumerate(results):
            print(f"  结果 {i+1}: 分数={r['score']:.4f}, 章节={r['section'][:30]}...")
            print(f"    匹配关键词: {r['matched_keywords']}")
    
    # 测试删除
    print("\n--- 删除测试 ---")
    deleted = index_mgr.delete_document('test_doc_001')
    print(f"已删除 {deleted} 个文本块")
    
    stats_after = index_mgr.get_stats()
    print(f"删除后统计: {stats_after}")


def main():
    print("=" * 60)
    print("企业知识库问答系统 - 功能测试")
    print("=" * 60)
    
    # 1. 创建测试文件
    filepath = create_test_file()
    
    # 2. 测试文档解析
    parsed = test_document_parser(filepath)
    
    # 3. 测试文本切片
    chunks = test_text_splitter(parsed['sections'])
    
    # 4. 测试索引管理
    test_index_manager(chunks)
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
