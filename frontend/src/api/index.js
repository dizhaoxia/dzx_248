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

export const search = (query, topK = 3) => {
  return api.get('/search', {
    params: {
      q: query,
      top_k: topK
    }
  })
}

export default api
