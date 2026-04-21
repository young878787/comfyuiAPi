<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h2 class="sidebar-title">ComfyUI Chat</h2>
      <button class="btn-new-chat" @click="handleNewChat" title="新增對話">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M5 12h14"/>
        </svg>
      </button>
    </div>

    <div class="session-list">
      <div
        v-for="session in sessions"
        :key="session.id"
        :class="['session-item', { active: session.id === currentSessionId }]"
        @click="handleSelect(session)"
      >
        <div class="session-info">
          <span class="session-title">{{ session.title || '未命名對話' }}</span>
          <span class="session-meta">{{ formatDate(session.updated_at) }}</span>
        </div>
        <div class="session-actions" @click.stop>
          <button class="btn-icon-sm" @click="handleEdit(session)" title="重新命名">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>
            </svg>
          </button>
          <button class="btn-icon-sm btn-delete" @click="handleDelete(session)" title="刪除">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
            </svg>
          </button>
        </div>
      </div>

      <div v-if="sessions.length === 0" class="empty-state">
        <p>尚無對話</p>
        <p class="hint">點擊 + 開始新對話</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSessionStore } from '@/stores/sessionStore'

const {
  sessions,
  currentSessionId,
  fetchSessions,
  createSession,
  deleteSession,
  updateSessionTitle,
  setCurrentSession,
} = useSessionStore()

onMounted(() => {
  fetchSessions()
})

const handleNewChat = async () => {
  await createSession('新對話')
}

const handleSelect = (session) => {
  setCurrentSession(session)
}

const handleEdit = async (session) => {
  const newTitle = prompt('輸入新標題:', session.title)
  if (newTitle && newTitle.trim()) {
    await updateSessionTitle(session.id, newTitle.trim())
  }
}

const handleDelete = async (session) => {
  if (confirm(`確定刪除「${session.title}」？`)) {
    await deleteSession(session.id)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '剛才'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分鐘前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小時前`
  return d.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: 100vh;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255,255,255,0.06);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.sidebar-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--sidebar-text);
  letter-spacing: -0.02em;
}

.btn-new-chat {
  background: var(--accent);
  color: #fff;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}
.btn-new-chat:hover {
  background: var(--accent-hover);
  transform: scale(1.05);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
  margin-bottom: 2px;
}
.session-item:hover {
  background: var(--sidebar-hover);
}
.session-item.active {
  background: var(--sidebar-active);
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-title {
  color: var(--sidebar-text);
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-meta {
  color: var(--sidebar-muted);
  font-size: 0.7rem;
}

.session-actions {
  display: none;
  gap: 2px;
  margin-left: 8px;
}
.session-item:hover .session-actions {
  display: flex;
}

.btn-icon-sm {
  background: transparent;
  color: var(--sidebar-muted);
  width: 26px;
  height: 26px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-icon-sm:hover {
  background: rgba(255,255,255,0.1);
  color: var(--sidebar-text);
}
.btn-delete:hover {
  color: var(--danger);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--sidebar-muted);
  font-size: 0.85rem;
}
.empty-state .hint {
  font-size: 0.75rem;
  margin-top: 8px;
  opacity: 0.6;
}
</style>
