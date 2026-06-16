<template>
  <div class="documents-page">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">
          <span class="title-icon">📄</span>
          文档管理
        </h1>
        <p class="page-subtitle">上传和管理您的知识库文档</p>
      </div>

      <div class="upload-section card">
        <h2 class="section-title">📤 上传文档</h2>
        <p class="section-desc">支持 PDF、Word (.docx)、Markdown (.md)、TXT 格式</p>

        <div
          class="upload-area"
          :class="{ 'drag-over': isDragOver }"
          @dragover.prevent="handleDragOver"
          @dragleave="handleDragLeave"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            :accept="acceptedFormats"
            class="file-input"
            @change="handleFileSelect"
          />
          <div class="upload-icon">📁</div>
          <div class="upload-text">
            <p v-if="!selectedFile">点击或拖拽文件到此处上传</p>
            <p v-else class="selected-file">已选择：{{ selectedFile.name }}</p>
          </div>
          <p class="upload-hint">单文件最大 50MB</p>
        </div>

        <button
          class="btn btn-primary upload-btn"
          @click="handleUpload"
          :disabled="!selectedFile || uploading"
        >
          {{ uploading ? '上传中...' : '🚀 开始上传' }}
        </button>

        <div v-if="uploadProgress > 0" class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
          <span class="progress-text">{{ uploadProgress.toFixed(0) }}%</span>
        </div>
      </div>

      <div class="document-list-section card">
        <div class="section-header">
          <h2 class="section-title">📋 文档列表</h2>
          <span class="doc-count">共 {{ documents.length }} 个文档</span>
        </div>

        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <span style="margin-left: 12px;">加载中...</span>
        </div>

        <div v-else-if="documents.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p>暂无文档，快上传一些吧！</p>
        </div>

        <div v-else class="document-list">
          <div
            v-for="doc in documents"
            :key="doc.doc_id"
            class="document-item"
          >
            <div class="doc-icon">📄</div>
            <div class="doc-info">
              <div class="doc-name">{{ doc.filename }}</div>
              <div class="doc-meta">
                <span>📝 {{ doc.chunk_count }} 个文本块</span>
                <span>🕐 {{ formatDate(doc.upload_time) }}</span>
              </div>
            </div>
            <button
              class="btn btn-danger delete-btn"
              @click="handleDelete(doc)"
              :disabled="deletingId === doc.doc_id"
            >
              {{ deletingId === doc.doc_id ? '删除中...' : '🗑️ 删除' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="stats.document_count > 0" class="stats-section">
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
import { getDocuments, uploadDocument, deleteDocument, getStats } from '../api'

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragOver = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const loading = ref(false)
const deletingId = ref(null)
const documents = ref([])
const stats = ref({
  document_count: 0,
  chunk_count: 0
})

const acceptedFormats = '.pdf,.docx,.doc,.md,.markdown,.txt'

const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await getDocuments()
    if (response.data.success) {
      documents.value = response.data.data
    }
  } catch (error) {
    console.error('Failed to load documents:', error)
  } finally {
    loading.value = false
  }
}

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

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const files = event.target.files
  if (files && files.length > 0) {
    selectedFile.value = files[0]
  }
}

const handleDragOver = () => {
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event) => {
  isDragOver.value = false
  const files = event.dataTransfer.files
  if (files && files.length > 0) {
    const file = files[0]
    if (isSupportedFile(file.name)) {
      selectedFile.value = file
    } else {
      alert('不支持的文件格式！')
    }
  }
}

const isSupportedFile = (filename) => {
  const ext = filename.toLowerCase().split('.').pop()
  return ['pdf', 'docx', 'doc', 'md', 'markdown', 'txt'].includes(ext)
}

const handleUpload = async () => {
  if (!selectedFile.value) return

  uploading.value = true
  uploadProgress.value = 0

  try {
    const response = await uploadDocument(selectedFile.value, (progressEvent) => {
      if (progressEvent.total) {
        uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      }
    })

    if (response.data.success) {
      alert('上传成功！')
      selectedFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      await loadDocuments()
      await loadStats()
    } else {
      alert('上传失败：' + response.data.error)
    }
  } catch (error) {
    console.error('Upload failed:', error)
    alert('上传失败，请重试')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

const handleDelete = async (doc) => {
  if (!confirm(`确定要删除文档「${doc.filename}」吗？`)) {
    return
  }

  deletingId.value = doc.doc_id

  try {
    const response = await deleteDocument(doc.doc_id)
    if (response.data.success) {
      await loadDocuments()
      await loadStats()
    } else {
      alert('删除失败：' + response.data.error)
    }
  } catch (error) {
    console.error('Delete failed:', error)
    alert('删除失败，请重试')
  } finally {
    deletingId.value = null
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadDocuments()
  loadStats()
})
</script>

<style scoped>
.documents-page {
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

.upload-section {
  margin-bottom: 24px;
}

.upload-area {
  border: 2px dashed #d0d0d0;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fafafa;
  margin-bottom: 16px;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: #667eea;
  background: #f0f3ff;
}

.file-input {
  display: none;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.upload-text {
  color: #666;
  font-size: 15px;
  margin-bottom: 8px;
}

.selected-file {
  color: #667eea;
  font-weight: 600;
}

.upload-hint {
  color: #aaa;
  font-size: 12px;
}

.upload-btn {
  width: 100%;
  padding: 14px;
  font-size: 16px;
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.progress-bar {
  margin-top: 16px;
  height: 24px;
  background: #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  color: #333;
  font-weight: 600;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.doc-count {
  color: #888;
  font-size: 14px;
}

.document-list-section {
  margin-bottom: 24px;
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

.document-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.document-item:hover {
  background: #f0f3ff;
}

.doc-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.doc-info {
  flex: 1;
  min-width: 0;
}

.doc-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #888;
}

.delete-btn {
  flex-shrink: 0;
  padding: 8px 16px;
  font-size: 14px;
}

.delete-btn:disabled {
  opacity: 0.6;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
}

.stat-icon {
  font-size: 40px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  color: #888;
  font-size: 13px;
  margin-top: 4px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 24px;
  }

  .document-item {
    flex-wrap: wrap;
  }

  .delete-btn {
    width: 100%;
  }

  .stats-section {
    grid-template-columns: 1fr;
  }

  .doc-meta {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
