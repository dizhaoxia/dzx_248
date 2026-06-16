<template>
  <div class="app-wrapper">
    <nav class="navbar">
      <div class="nav-container">
        <router-link to="/" class="logo">
          <span class="logo-icon">📚</span>
          <span class="logo-text">企业知识库</span>
        </router-link>
        <div class="nav-links">
          <router-link to="/" class="nav-link" exact-active-class="active">
            🔍 搜索
          </router-link>
          <router-link to="/documents" class="nav-link" active-class="active">
            📄 文档管理
          </router-link>
          <router-link to="/synonyms" class="nav-link" active-class="active">
            📚 同义词管理
          </router-link>
        </div>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #333;
  font-size: 20px;
  font-weight: 700;
}

.logo-icon {
  font-size: 28px;
}

.logo-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-link {
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #666;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-link:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.nav-link.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.main-content {
  flex: 1;
  padding: 40px 20px;
}
</style>
