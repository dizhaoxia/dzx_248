<template>
  <div class="synonyms-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">
          <span class="title-icon">📚</span>
          同义词管理
        </h1>
        <p class="page-subtitle">维护同义词词典，提升搜索召回率</p>
      </div>

      <div class="add-section card">
        <h2 class="section-title">➕ 添加同义词</h2>
        <p class="section-desc">输入词语和它的同义词，多个同义词用逗号分隔</p>
        
        <div class="add-form">
          <div class="form-group">
            <label class="form-label">词语</label>
            <input
              v-model="newWord"
              type="text"
              class="form-input"
              placeholder="例如：退货"
            />
          </div>
          <div class="form-group">
            <label class="form-label">同义词</label>
            <input
              v-model="newSynonyms"
              type="text"
              class="form-input"
              placeholder="例如：退款, 退换, 退钱（用逗号分隔）"
            />
          </div>
          <button class="btn btn-primary add-btn" @click="handleAdd" :disabled="adding">
            {{ adding ? '添加中...' : '🚀 添加' }}
          </button>
        </div>
      </div>

      <div class="synonyms-list-section card">
        <div class="section-header">
          <h2 class="section-title">📋 同义词列表</h2>
          <span class="synonyms-count">共 {{ synonymCount }} 个词条</span>
        </div>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <span style="margin-left: 12px;">加载中...</span>
        </div>

        <div v-else-if="Object.keys(synonyms).length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p>暂无同义词，快添加一些吧！</p>
        </div>

        <div v-else class="synonyms-list">
          <div
            v-for="(synonymList, word) in synonyms"
            :key="word"
            class="synonym-item"
          >
            <div class="synonym-word">
              <span class="word-text">{{ word }}</span>
              <span class="word-arrow">→</span>
            </div>
            <div class="synonym-tags">
              <span
                v-for="syn in synonymList"
                :key="syn"
                class="synonym-tag"
              >
                {{ syn }}
                <span class="remove-syn" @click="handleRemoveSynonym(word, syn)">×</span>
              </span>
            </div>
            <button
              class="btn btn-danger delete-btn"
              @click="handleDeleteWord(word)"
              :disabled="deletingWord === word"
            >
              {{ deletingWord === word ? '删除中...' : '🗑️' }}
            </button>
          </div>
        </div>
      </div>

      <div class="batch-section card">
        <h2 class="section-title">📝 批量编辑</h2>
        <p class="section-desc">以 JSON 格式批量编辑同义词词典</p>
        
        <textarea
          v-model="batchJson"
          class="batch-textarea"
          rows="15"
          placeholder='{"退货": ["退款", "退换"], "退款": ["退货", "退换"]}'
        ></textarea>
        
        <div class="batch-actions">
          <button class="btn btn-secondary" @click="handleResetBatch">
            🔄 重置
          </button>
          <button class="btn btn-primary" @click="handleSaveBatch" :disabled="savingBatch">
            {{ savingBatch ? '保存中...' : '💾 保存全部' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getSynonyms, addSynonym, removeSynonym, updateSynonymsBatch } from '../api'

const synonyms = ref({})
const loading = ref(false)
const adding = ref(false)
const deletingWord = ref('')
const savingBatch = ref(false)
const newWord = ref('')
const newSynonyms = ref('')
const batchJson = ref('')

const synonymCount = computed(() => Object.keys(synonyms.value).length)

const loadSynonyms = async () => {
  loading.value = true
  try {
    const response = await getSynonyms()
    if (response.data.success) {
      synonyms.value = response.data.data
      batchJson.value = JSON.stringify(response.data.data, null, 2)
    }
  } catch (error) {
    console.error('Failed to load synonyms:', error)
    alert('加载同义词失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = async () => {
  if (!newWord.value.trim()) {
    alert('请输入词语')
    return
  }
  if (!newSynonyms.value.trim()) {
    alert('请输入同义词')
    return
  }

  adding.value = true
  try {
    const syns = newSynonyms.value.split(/[,，]/).map(s => s.trim()).filter(s => s)
    
    for (const syn of syns) {
      await addSynonym(newWord.value.trim(), syn)
    }
    
    alert('添加成功！')
    newWord.value = ''
    newSynonyms.value = ''
    await loadSynonyms()
  } catch (error) {
    console.error('Failed to add synonym:', error)
    alert('添加失败：' + (error.response?.data?.error || error.message))
  } finally {
    adding.value = false
  }
}

const handleRemoveSynonym = async (word, synonym) => {
  if (!confirm(`确定要移除「${word}」的同义词「${synonym}」吗？`)) {
    return
  }

  try {
    await removeSynonym(word, synonym)
    await loadSynonyms()
  } catch (error) {
    console.error('Failed to remove synonym:', error)
    alert('移除失败')
  }
}

const handleDeleteWord = async (word) => {
  if (!confirm(`确定要删除整个词条「${word}」吗？`)) {
    return
  }

  deletingWord.value = word
  try {
    const syns = synonyms.value[word] || []
    for (const syn of syns) {
      await removeSynonym(word, syn)
    }
    await loadSynonyms()
  } catch (error) {
    console.error('Failed to delete word:', error)
    alert('删除失败')
  } finally {
    deletingWord.value = ''
  }
}

const handleResetBatch = () => {
  batchJson.value = JSON.stringify(synonyms.value, null, 2)
}

const handleSaveBatch = async () => {
  try {
    const parsed = JSON.parse(batchJson.value)
    if (typeof parsed !== 'object' || parsed === null) {
      alert('JSON 格式错误：必须是对象')
      return
    }

    savingBatch.value = true
    await updateSynonymsBatch(parsed)
    alert('保存成功！')
    await loadSynonyms()
  } catch (error) {
    if (error instanceof SyntaxError) {
      alert('JSON 格式错误：' + error.message)
    } else {
      console.error('Failed to save batch:', error)
      alert('保存失败')
    }
  } finally {
    savingBatch.value = false
  }
}

onMounted(() => {
  loadSynonyms()
})
</script>

<style scoped>
.synonyms-page {
  min-height: 100%;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-title {
  font-size: 32px;
  color: white;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.title-icon {
  font-size: 36px;
}

.page-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
}

.section-title {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.section-desc {
  color: #888;
  font-size: 14px;
  margin-bottom: 20px;
}

.add-section,
.synonyms-list-section,
.batch-section {
  margin-bottom: 24px;
}

.add-form {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  flex: 1;
  min-width: 200px;
}

.form-label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  border-color: #667eea;
}

.add-btn {
  padding: 12px 24px;
  white-space: nowrap;
}

.add-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.synonyms-count {
  color: #888;
  font-size: 14px;
}

.synonyms-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.synonym-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.synonym-item:hover {
  background: #f0f3ff;
}

.synonym-word {
  min-width: 120px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.word-text {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.word-arrow {
  color: #667eea;
  font-weight: bold;
}

.synonym-tags {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.synonym-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 500;
}

.remove-syn {
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.remove-syn:hover {
  opacity: 1;
}

.delete-btn {
  flex-shrink: 0;
  padding: 8px 12px;
  font-size: 14px;
}

.delete-btn:disabled {
  opacity: 0.6;
}

.batch-textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  font-family: 'Monaco', 'Menlo', monospace;
  outline: none;
  resize: vertical;
  transition: border-color 0.2s ease;
}

.batch-textarea:focus {
  border-color: #667eea;
}

.batch-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

@media (max-width: 768px) {
  .add-form {
    flex-direction: column;
  }

  .form-group {
    width: 100%;
  }

  .add-btn {
    width: 100%;
  }

  .synonym-item {
    flex-wrap: wrap;
  }

  .synonym-word {
    width: 100%;
  }

  .delete-btn {
    width: 100%;
  }
}
</style>
