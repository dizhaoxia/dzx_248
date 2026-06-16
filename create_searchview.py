#!/usr/bin/env python3
import os

template_path = os.path.join(os.path.dirname(__file__), 'test_doc.md')
output_path = '/Users/feixuan/Desktop/solo/dzx_248/frontend/src/views/SearchView.vue'

content = r'''<template>
  <div class="search-page">
    <div class="container">
      <div class="search-header">
        <h1 class="page-title">
          <span class="title-icon">&#128269;</span>
          智能知识库检索
        </h1>
        <p class="page-subtitle">基于 BM25 算法的全文检索，精准定位您需要的信息</p>
      </div>

      <div class="search-box card">
        <div class="search-input-wrapper">
          <input
            v-model="query"
            type="text"
            class="search-input"
            placeholder="请输入您的问题或关键词..."
            @keyup.enter="handleSearch"
            @input="handleInputChange"
          />
          <select v-model="selectedDocId" class="doc-filter-select">
            <option value="">全部文档</option>
            <option v-for="doc in documents" :key="doc.doc_id" :value="doc.doc_id">
              {{ doc.filename }}
            </option>
          </select>
          <select v-model="topK" class="topk-select">
            <option :value="1">Top 1</option>
            <option :value="3">Top 3</option>
            <option :value="5">Top 5</option>
            <option :value="10">Top 10</option>
          </select>
          <button class="btn btn-primary search-btn" @click="handleSearch" :disabled="loading">
            {{ loading ? '搜索中...' : '&#128269; 搜索' }}
          </button>
        </div>

        <div v-if="correctedQuery" class="spell-correction card">
          <span class="correction-icon">&#128161;</span>
          <span class="correction-text">
            您是不是要找：<span @click="applyCorrection" class="correction-link">{{ correctedQuery }}</span>
          </span>
          <span class="correction-hint">(点击使用修正词搜索)</span>
        </div>

        <div class="example-queries">
          <span class="example-label">示例：</span>
          <button
            v-for="example in exampleQueries"
            :key="example"
            class="example-tag"
            @click="quickSearch(example)"
          >
            {{ example }}
          </button>
        </div>

        <div v-if="expandedKeywords.length > 0" class="expanded-keywords">
          <span class="keywords-label">&#128257; 同义词扩展：</span>
          <span
            v-for="kw in expandedKeywords"
            :key="kw"
            class="expand-tag"
          >
            {{ kw }}
          </span>
        </div>
      </div>

      <div v-if="loading" class="loading card">
        <div class="spinner"></div>
        <span style="margin-left: 12px;">正在搜索...</span>
      </div>

      <div v-else-if="hasSearched && results.length === 0" class="no-results card">
        <div class="no-results-icon">&#128546;</div>
        <h3>未找到相关结果</h3>
        <p>请尝试使用其他关键词搜索，或先上传一些文档</p>
        <router-link to="/documents" class="btn btn-primary">
          &#128196; 去上传文档
        </router-link>
      </div>

      <div v-else-if="results.length > 0" class="results-container">
        <div class="results-header card">
          <span>
            找到 <strong>{{ totalResults }}</strong> 个相关结果
            <span v-if="searchQuery">（关键词：{{ searchQuery }}）</span>
            <span v-if="selectedDocId" class="filter-badge">
              &#128193; {{ selectedDocName }}
              <span class="remove-filter" @click="clearDocFilter">x</span>
            </span>
          </span>
        </div>

        <div v-if="similarQueries.length > 0" class="similar-queries card">
          <div class="similar-header">
            <span class="similar-icon">&#128161;</span>
            <span class="similar-title">相似问题推荐</span>
          </div>
          <div class="similar-list">
            <button
              v-for="(sq, index) in similarQueries"
              :key="sq.query"
              class="similar-item"
              @click="quickSearch(sq.query)"
            >
              <span class="similar-rank">{{ index + 1 }}</span>
              <span class="similar-text">{{ sq.query }}</span>
              <span class="similar-count">{{ sq.count }}次查询</span>
            </button>
          </div>
        </div>

        <div
          v-for="(result, index) in results"
          :key="result.chunk_id"
          class="result-item card"
        >
          <div class="result-rank">{{ index + 1 }}</div>
          <div class="result-content">
            <div class="result-meta">
              <span class="result-score">
                相似度: {{ (result.score * 100).toFixed(1) }}%
              </span>
              <span v-if="result.phrase_boost > 1" class="result-boost">
                &#128640; 短语加成: x{{ result.phrase_boost }}
              </span>
              <span class="result-filename">&#128196; {{ result.filename }}</span>
              <span v-if="result.section" class="result-section">
                &#128193; {{ result.section }}
              </span>
              <span class="result-position">
                位置: 第 {{ result.chunk_index + 1 }}/{{ result.total_chunks }} 块
              </span>
            </div>

            <div class="result-focus">
              <div class="focus-label">&#127919; 答案摘要</div>
              <div class="focus-text" v-html="result.highlighted_focus"></div>
            </div>

            <div class="result-expand-toggle" @click="toggleExpand(result.chunk_id)">
              <span v-if="!expandedChunks.includes(result.chunk_id)">
                &#9660; 查看完整内容
              </span>
              <span v-else>
                &#9650; 收起完整内容
              </span>
            </div>

            <div v-if="expandedChunks.includes(result.chunk_id)" class="result-full">
              <div class="full-label">&#128221; 完整内容</div>
              <div class="result-text" v-html="highlightText(result.content, result.matched_keywords)"></div>
            </div>

            <div class="result-keywords">
              <span class="keywords-label">匹配关键词：</span>
              <span
                v-for="keyword in result.matched_keywords"
                :key="keyword"
                class="keyword-tag"
              >
                {{ keyword }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!hasSearched" class="stats-cards">
        <div class="stat-card card">
          <div class="stat-icon">&#128193;</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.document_count }}</div>
            <div class="stat-label">文档总数</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">&#128221;</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.chunk_count }}</div>
            <div class="stat-label">文本块数</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { search as searchApi, getStats, getDocuments } from '../api'

const query = ref('')
const topK = ref(3)
const selectedDocId = ref('')
const loading = ref(false)
const results = ref([])
const totalResults = ref(0)
const hasSearched = ref(false)
const searchQuery = ref('')
const stats = ref({
  document_count: 0,
  chunk_count: 0
})
const documents = ref([])
const expandedKeywords = ref([])
const similarQueries = ref([])
const correctedQuery = ref('')
const spellCorrections = ref([])
const expandedChunks = ref([])

const exampleQueries = [
  '售后服务流程',
  '退货退款政策',
  '知识库',
  '文档管理',
  '人工智能',
  '机器学习'
]

const selectedDocName = computed(() => {
  if (!selectedDocId.value) return ''
  const doc = documents.value.find(d => d.doc_id === selectedDocId.value)
  return doc ? doc.filename : ''
})

const loadStats = async () => {
  try {
    const response = await getStats()
    if (response.data.success) {
      stats.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const loadDocuments = async () => {
  try {
    const response = await getDocuments()
    if (response.data.success) {
      documents.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to load documents:', error)
  }
}

const handleSearch = async () => {
  if (!query.value.trim()) {
    return
  }

  loading.value = true
  hasSearched.value = true
  searchQuery.value = query.value.trim()

  try {
    const response = await searchApi(query.value.trim(), topK.value, selectedDocId.value)
    if (response.data.success) {
      const data = response.data.data
      results.value = data.results
      totalResults.value = data.total
      expandedKeywords.value = data.expanded_keywords || []
      similarQueries.value = data.similar_queries || []
      correctedQuery.value = data.corrected_query || ''
      spellCorrections.value = data.spell_corrections || []
      expandedChunks.value = []
    }
  } catch (error) {
    console.error('Search failed:', error)
    results.value = []
    totalResults.value = 0
    expandedKeywords.value = []
    similarQueries.value = []
    correctedQuery.value = ''
  } finally {
    loading.value = false
  }
}

const handleInputChange = () => {
  if (correctedQuery.value) {
    correctedQuery.value = ''
  }
}

const quickSearch = (text) => {
  query.value = text
  handleSearch()
}

const applyCorrection = () => {
  if (correctedQuery.value) {
    query.value = correctedQuery.value
    correctedQuery.value = ''
    handleSearch()
  }
}

const clearDocFilter = () => {
  selectedDocId.value = ''
  if (hasSearched.value && query.value.trim()) {
    handleSearch()
  }
}

const toggleExpand = (chunkId) => {
  const index = expandedChunks.value.indexOf(chunkId)
  if (index === -1) {
    expandedChunks.value.push(chunkId)
  } else {
    expandedChunks.value.splice(index, 1)
  }
}

const highlightText = (text, keywords) => {
  if (!keywords || keywords.length === 0) {
    return escapeHtml(text)
  }

  let result = escapeHtml(text)
  const sortedKeywords = [...keywords].sort((a, b) => b.length - a.length)

  for (const keyword of sortedKeywords) {
    if (!keyword) continue
    const regex = new RegExp(escapeRegExp(keyword), 'gi')
    result = result.replace(regex, '<span class="highlight">$&</span>')
  }

  return result
}

const escapeHtml = (text) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

onMounted(() => {
  loadStats()
  loadDocuments()
})
</script>

<style scoped>
.search-page {
  min-height: 100%;
}

.search-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 36px;
  color: white;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 42px;
}

.page-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
}

.search-box {
  margin-bottom: 24px;
}

.search-input-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-input {
  flex: 1;
  padding: 14px 18px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s ease;
}

.search-input:focus {
  border-color: #667eea;
}

.doc-filter-select,
.topk-select {
  padding: 14px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
  background: white;
  transition: border-color 0.2s ease;
  min-width: 120px;
}

.doc-filter-select {
  min-width: 180px;
}

.doc-filter-select:focus,
.topk-select:focus {
  border-color: #667eea;
}

.search-btn {
  padding: 14px 28px;
  font-size: 16px;
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.spell-correction {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
  border: 1px solid #ffeaa7;
  border-radius: 10px;
  margin-bottom: 16px;
}

.correction-icon {
  font-size: 20px;
}

.correction-text {
  flex: 1;
  color: #856404;
  font-size: 14px;
}

.correction-link {
  color: #667eea;
  cursor: pointer;
  text-decoration: underline;
  font-weight: 600;
}

.correction-link:hover {
  color: #5a6fd8;
}

.correction-hint {
  color: #999;
  font-size: 12px;
}

.example-queries {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.example-label {
  color: #999;
  font-size: 14px;
}

.example-tag {
  padding: 6px 14px;
  background: #f5f7fa;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.example-tag:hover {
  background: #e8edff;
  border-color: #667eea;
  color: #667eea;
}

.expanded-keywords {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.expanded-keywords .keywords-label {
  color: #999;
  font-size: 13px;
}

.expand-tag {
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.results-header {
  padding: 16px 24px;
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.results-header strong {
  color: #667eea;
  font-size: 18px;
}

.filter-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  padding: 4px 12px;
  background: #e8edff;
  color: #667eea;
  border-radius: 12px;
  font-size: 12px;
}

.remove-filter {
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  line-height: 1;
}

.remove-filter:hover {
  color: #e74c3c;
}

.similar-queries {
  padding: 20px 24px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border: 1px solid #e0e7ff;
}

.similar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.similar-icon {
  font-size: 18px;
}

.similar-title {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.similar-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.similar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.similar-item:hover {
  background: #f5f7fa;
  border-color: #667eea;
  transform: translateX(4px);
}

.similar-rank {
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.similar-text {
  flex: 1;
  color: #333;
  font-size: 14px;
}

.similar-count {
  color: #999;
  font-size: 12px;
}

.result-item {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.result-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.result-rank {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
}

.result-content {
  flex: 1;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #666;
}

.result-score {
  color: #667eea;
  font-weight: 600;
}

.result-boost {
  color: #e67e22;
  font-weight: 500;
}

.result-filename,
.result-section,
.result-position {
  color: #888;
}

.result-focus {
  background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
  border: 1px solid #ffeaa7;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.focus-label {
  font-size: 13px;
  font-weight: 600;
  color: #856404;
  margin-bottom: 8px;
}

.focus-text {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
}

.result-expand-toggle {
  text-align: center;
  color: #667eea;
  font-size: 13px;
  cursor: pointer;
  padding: 8px;
  margin-bottom: 12px;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.result-expand-toggle:hover {
  background: #f5f7fa;
}

.result-full {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.full-label {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}

.result-text {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
  margin-bottom: 12px;
}

.result-keywords {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.keywords-label {
  font-size: 13px;
  color: #999;
}

.keyword-tag {
  padding: 4px 10px;
  background: #fff3cd;
  color: #856404;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.no-results {
  text-align: center;
  padding: 60px 24px;
}

.no-results-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.no-results h3 {
  color: #333;
  margin-bottom: 8px;
}

.no-results p {
  color: #888;
  margin-bottom: 24px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 40px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 30px;
}

.stat-icon {
  font-size: 48px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  color: #888;
  font-size: 14px;
  margin-top: 4px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 28px;
  }

  .search-input-wrapper {
    flex-direction: column;
  }

  .doc-filter-select,
  .topk-select {
    width: 100%;
  }

  .search-btn {
    width: 100%;
  }

  .stats-cards {
    grid-template-columns: 1fr;
  }

  .result-item {
    flex-direction: column;
    gap: 12px;
  }

  .spell-correction {
    flex-direction: column;
    text-align: center;
  }
}
</style>
'''

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'File written successfully: {output_path}')
print(f'File size: {os.path.getsize(output_path)} bytes')
