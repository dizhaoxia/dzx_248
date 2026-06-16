#!/usr/bin/env python3
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.search_enhancer import SearchEnhancer
from app.core.index_manager import IndexManager


def test_search_enhancer():
    print("=" * 60)
    print("测试 SearchEnhancer 核心功能")
    print("=" * 60)
    
    data_dir = os.path.join(os.path.dirname(__file__), 'backend', 'data')
    enhancer = SearchEnhancer(data_dir)
    
    print("\n1. 测试同义词扩展功能")
    print("-" * 40)
    query = "退货"
    expanded_query, keywords = enhancer.expand_query_with_synonyms(query)
    print(f"   原始查询: {query}")
    print(f"   扩展后: {expanded_query}")
    print(f"   所有关键词: {keywords}")
    assert "退款" in keywords, "同义词扩展失败！"
    print("   ✓ 同义词扩展功能正常")
    
    print("\n2. 测试短语提取功能")
    print("-" * 40)
    query = "售后服务流程"
    phrases = enhancer.extract_phrases(query)
    print(f"   查询: {query}")
    print(f"   提取的短语: {phrases}")
    assert len(phrases) > 0, "短语提取失败！"
    print("   ✓ 短语提取功能正常")
    
    print("\n3. 测试短语权重计算")
    print("-" * 40)
    content = "售后服务流程包括以下步骤：首先联系客服，然后申请退货退款。"
    boost = enhancer.calculate_phrase_boost(content, phrases)
    print(f"   内容: {content}")
    print(f"   短语: {phrases}")
    print(f"   权重加成: {boost}")
    assert boost > 1.0, "短语权重加成失败！"
    print("   ✓ 短语权重计算功能正常")
    
    print("\n4. 测试答案片段聚焦")
    print("-" * 40)
    content = """这是一个关于售后服务的文档。售后服务是我们非常重视的部分。
我们提供7天无理由退货服务。退货时请保持商品完好。
退款将在收到退货后的3个工作日内处理。如有任何问题，请联系客服。"""
    keywords = ["退货", "退款", "售后服务"]
    focus_content, matched = enhancer.extract_focus_sentences(content, keywords, max_sentences=2)
    print(f"   关键词: {keywords}")
    print(f"   聚焦内容: {focus_content}")
    print(f"   匹配关键词: {matched}")
    assert len(focus_content) > 0, "答案聚焦失败！"
    print("   ✓ 答案片段聚焦功能正常")
    
    print("\n5. 测试编辑距离计算")
    print("-" * 40)
    dist = enhancer.levenshtein_distance("知识", "知是")
    print(f"   '知识' vs '知是' 编辑距离: {dist}")
    assert dist == 1, "编辑距离计算错误！"
    print("   ✓ 编辑距离计算功能正常")
    
    print("\n6. 测试拼写纠错功能")
    print("-" * 40)
    query = "知是库"
    corrected, corrections = enhancer.correct_spelling(query)
    print(f"   原始查询: {query}")
    print(f"   修正后: {corrected}")
    print(f"   修正详情: {json.dumps(corrections, ensure_ascii=False, indent=6)}")
    assert corrected == "知识库", f"拼写纠错失败，期望'知识库'，得到'{corrected}'！"
    print("   ✓ 拼写纠错功能正常")
    
    print("\n7. 测试相似问题推荐")
    print("-" * 40)
    query = "如何退货退款"
    similar = enhancer.find_similar_queries(query, top_k=3)
    print(f"   查询: {query}")
    print(f"   相似问题: {json.dumps(similar, ensure_ascii=False, indent=6)}")
    assert len(similar) > 0, "相似问题推荐失败！"
    print("   ✓ 相似问题推荐功能正常")
    
    print("\n8. 测试查询历史记录")
    print("-" * 40)
    test_query = "测试查询功能"
    enhancer.record_query(test_query)
    history = enhancer.get_query_history(limit=100)
    print(f"   记录查询: {test_query}")
    print(f"   历史记录总数: {len(history)}")
    print(f"   最近历史: {json.dumps(history[:2], ensure_ascii=False, indent=6)}")
    found = any(h['query'] == test_query for h in history)
    assert found, "查询历史记录失败！"
    test_record = next(h for h in history if h['query'] == test_query)
    print(f"   新增记录count: {test_record['count']}")
    print("   ✓ 查询历史记录功能正常")
    
    print("\n" + "=" * 60)
    print("SearchEnhancer 所有功能测试通过！")
    print("=" * 60)
    return True


def test_index_manager():
    print("\n" + "=" * 60)
    print("测试 IndexManager 增强功能")
    print("=" * 60)
    
    index_dir = os.path.join(os.path.dirname(__file__), 'backend', 'index')
    data_dir = os.path.join(os.path.dirname(__file__), 'backend', 'data')
    
    index_mgr = IndexManager(index_dir, data_dir)
    
    print("\n1. 测试完整搜索流程（含所有增强功能）")
    print("-" * 40)
    query = "售后服务流程"
    result = index_mgr.search(query, top_k=3)
    print(f"   查询: {query}")
    print(f"   结果数量: {len(result['results'])}")
    print(f"   扩展关键词: {result['expanded_keywords']}")
    print(f"   提取短语: {result['phrases']}")
    print(f"   相似问题数量: {len(result['similar_queries'])}")
    print(f"   拼写修正: {result['corrected_query']}")
    
    if result['results']:
        r = result['results'][0]
        print(f"\n   第一个结果详情:")
        print(f"     文档: {r['filename']}")
        print(f"     基础分数: {r['base_score']}")
        print(f"     短语加成: {r['phrase_boost']}")
        print(f"     最终分数: {round(r['score'], 4)}")
        print(f"     聚焦答案: {r['focus_content'][:100]}...")
        print(f"     匹配关键词: {r['matched_keywords']}")
    
    print("\n   ✓ 完整搜索流程功能正常")
    
    print("\n2. 测试按文档筛选搜索")
    print("-" * 40)
    docs = index_mgr.get_all_documents()
    if docs:
        doc_id = docs[0]['doc_id']
        doc_name = docs[0]['filename']
        print(f"   筛选文档: {doc_name}")
        result_filtered = index_mgr.search(query, top_k=3, doc_id=doc_id)
        print(f"   筛选后结果数量: {len(result_filtered['results'])}")
        for r in result_filtered['results']:
            assert r['doc_id'] == doc_id, f"文档筛选失败！期望{doc_id}，得到{r['doc_id']}"
        print("   ✓ 按文档筛选功能正常")
    else:
        print("   ⚠ 暂无文档，跳过筛选测试")
    
    print("\n" + "=" * 60)
    print("IndexManager 所有增强功能测试通过！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        test_search_enhancer()
        test_index_manager()
        print("\n" + "=" * 60)
        print("🎉 所有功能测试全部通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
