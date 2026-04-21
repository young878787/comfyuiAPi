<template>
  <div class="app-layout">
    <SessionSidebar />

    <div class="main-area">
      <nav class="top-nav">
        <router-link to="/chat" class="nav-tab" active-class="active">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span>AI 對話</span>
        </router-link>
        <router-link to="/draw" class="nav-tab" active-class="active">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
          <span>繪圖生成</span>
        </router-link>
      </nav>

      <div class="content-area">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import SessionSidebar from '@/components/SessionSidebar.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-content);
}

.top-nav {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  background: var(--bg-white);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-decoration: none;
  transition: var(--transition);
}
.nav-tab:hover {
  background: var(--bg-content);
  color: var(--text-dark);
}
.nav-tab.active {
  background: var(--accent-light, #f0edff);
  color: var(--accent);
}

.content-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
