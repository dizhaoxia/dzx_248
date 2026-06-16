import { createRouter, createWebHistory } from 'vue-router'
import SearchView from '../views/SearchView.vue'
import DocumentsView from '../views/DocumentsView.vue'
import SynonymsView from '../views/SynonymsView.vue'

const routes = [
  {
    path: '/',
    name: 'search',
    component: SearchView
  },
  {
    path: '/documents',
    name: 'documents',
    component: DocumentsView
  },
  {
    path: '/synonyms',
    name: 'synonyms',
    component: SynonymsView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
