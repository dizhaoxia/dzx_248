import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const healthCheck = () => {
  return api.get('/health')
}

export const getStats = () => {
  return api.get('/stats')
}

export const getDocuments = () => {
  return api.get('/documents')
}

export const uploadDocument = (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  return api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: onProgress
  })
}

export const deleteDocument = (docId) => {
  return api.delete(`/documents/${docId}`)
}

export const search = (query, topK = 3, docId = '') => {
  return api.get('/search', {
    params: {
      q: query,
      top_k: topK,
      doc_id: docId
    }
  })
}

export const getSynonyms = () => {
  return api.get('/synonyms')
}

export const addSynonym = (word, synonym) => {
  return api.post('/synonyms', { word, synonym })
}

export const removeSynonym = (word, synonym) => {
  return api.delete('/synonyms', { data: { word, synonym } })
}

export const updateSynonymsBatch = (synonyms) => {
  return api.post('/synonyms/batch', { synonyms })
}

export const spellCheck = (query) => {
  return api.get('/spellcheck', {
    params: { q: query }
  })
}

export const getSimilarQueries = (query, topK = 5) => {
  return api.get('/similar-queries', {
    params: { q: query, top_k: topK }
  })
}

export const getQueryHistory = (limit = 50) => {
  return api.get('/query-history', {
    params: { limit }
  })
}

export const clearQueryHistory = () => {
  return api.delete('/query-history')
}

export const recordQuery = (query) => {
  return api.post('/query-history/record', { q: query })
}

export default api
