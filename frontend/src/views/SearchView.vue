<template>
  <div class="search-page">
    <div class="container">
      <div class="search-header">
        <h1 class="page-title">
          <span class="title-icon">🔍</span>
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
          />
          <select v-model="topK" class="topk-select">
            <option :value="1">Top 1</option>
            <option :value="3">Top 3</option>
            <option :value="5">Top 5</option>
            <option :value="10">Top 10</option>
          </select>
          <button class="btn btn-primary search-btn" @click="handleSearch" :disabled="loading">
            {{ loading ? '搜索中...' : '🔍 搜索' }}
          </button>
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
      </div>

      <div v-if="loading" class="loading card">
        <div class="spinner"></div>
        <span style="margin-left: 12px;">正在搜索...</span>
      </div>

      <div v-else-if="hasSearched && results.length === 0" class="no-results card">
        <div class="no-results-icon">😔</div>
        <h3>未找到相关结果</h3>
        <p>请尝试使用其他关键词搜索，或先上传一些文档</p>
        <router-link to="/documents" class="btn btn-primary">
          📄 去上传文档
        </router-link>
      </div>

      <div v-else-if="results.length > 0" class="results-container">
        <div class="results-header card">
          <span>
            找到 <strong>{{ totalResults }}</strong> 个相关结果
            <span v-if="searchQuery">（关键词：{{ searchQuery }}）</span>
          </span>
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
              <span class="result-filename">📄 {{ result.filename }}</span>
              <span v-if="result.section" class="result-section">
                📑 {{ result.section }}
              </span>
              <span class="result-position">
                位置: 第 {{ result.chunk_index + 1 }}/{{ result.total_chunks }} 块
              </span>
            </div>

            <div class="result-text" v-html="highlightText(result.content, result.matched_keywords)"></div>

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
          <div class="stat-icon">📁</div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.document_count }}</div>
            <div class="stat-label">文档总数</div>
          </div>
        </div>
        <div class="stat-card card">
          <div class="stat-icon">📝</div>
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
import { ref, onMounted } from 'vue'
import { search as searchApi, getStats } from '../api'

const query = ref('')
const topK = ref(3)
const loading = ref(false)
const results = ref([])
const totalResults = ref(0)
const hasSearched = ref(false)
const searchQuery = ref('')
const stats = ref({
  document_count: 0,
  chunk_count: 0
})

const exampleQueries = [
  '知识库',
  '文档管理',
  '人工智能',
  '机器学习'
]

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

const handleSearch = async () => {
  if (!query.value.trim()) {
    return
  }

  loading.value = true
  hasSearched.value = true
  searchQuery.value = query.value.trim()

  try {
    const response = await searchApi(query.value.trim(), topK.value)
    if (response.data.success) {
      results.value = response.data.data.results
      totalResults.value = response.data.data.total
    }
  } catch (error) {
    console.error('Search failed:', error)
    results.value = []
    totalResults.value = 0
  } finally {
    loading.value = false
  }
}

const quickSearch = (text) => {
  query.value = text
  handleSearch()
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

.topk-select {
  padding: 14px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
  background: white;
  transition: border-color 0.2s ease;
}

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

.example-queries {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
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

.results-header {
  padding: 16px 24px;
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
}

.results-header strong {
  color: #667eea;
  font-size: 18px;
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

.result-filename,
.result-section,
.result-position {
  color: #888;
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
}
</style>
