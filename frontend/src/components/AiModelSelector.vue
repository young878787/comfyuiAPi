<template>
  <div class="ai-model-selector-container">
    <label for="ai-model-select">AI 模型 (OpenCode Go)</label>
    <div class="selector-wrapper">
      <select
        id="ai-model-select"
        v-model="selected"
        class="glass-select"
        :disabled="switching"
        @change="handleSelect"
      >
        <option v-for="m in models" :key="m.id" :value="m.id">{{ m.id }}</option>
      </select>
      <button
        class="refresh-btn"
        @click="refresh"
        :disabled="switching"
        title="重新取得模型清單"
      >
        <svg :class="['refresh-icon', loading ? 'spinning' : '']" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"></polyline>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const emit = defineEmits(['changed'])

const models = ref([])
const selected = ref('')
const loading = ref(false)
const switching = ref(false)
const stale = ref(false)

const RETRY_DELAY_MS = 3000
const MAX_ATTEMPTS = 5
const BACKGROUND_POLL_MS = 5000
const BACKGROUND_POLL_MAX = 24

let backgroundTimer = null

const stopBackgroundPoll = () => {
  if (backgroundTimer) {
    clearInterval(backgroundTimer)
    backgroundTimer = null
  }
}

const startBackgroundPoll = () => {
  if (backgroundTimer || models.value.length > 0) return
  let polls = 0
  backgroundTimer = setInterval(async () => {
    polls++
    await fetchModels(false)
    if (models.value.length > 0 || polls >= BACKGROUND_POLL_MAX) stopBackgroundPoll()
  }, BACKGROUND_POLL_MS)
}

const fetchModels = async (force = false) => {
  try {
    const res = await fetch(force ? '/api/ai/models/refresh' : '/api/ai/models', {
      method: force ? 'POST' : 'GET'
    })
    if (res.ok) {
      const data = await res.json()
      models.value = data.models || []
      stale.value = !!data.stale
      if (data.current_model) selected.value = data.current_model
    }
  } catch (err) {
    console.warn('Failed to fetch AI models:', err)
  }
}

const loadCatalog = async (force = false) => {
  loading.value = true
  // Retry a few times to survive a slow backend startup
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    await fetchModels(force)
    if (models.value.length > 0) break
    if (attempt < MAX_ATTEMPTS) {
      await new Promise((r) => setTimeout(r, RETRY_DELAY_MS))
    }
  }
  loading.value = false
  // Keep polling in the background until the list arrives (no user action needed)
  if (models.value.length === 0) startBackgroundPoll()
}

const refresh = () => loadCatalog(true)

const handleVisibility = () => {
  if (document.visibilityState === 'visible' && models.value.length === 0) {
    loadCatalog(false)
  }
}

const handleSelect = async () => {
  const modelId = selected.value
  if (!modelId) return
  switching.value = true
  try {
    const res = await fetch('/api/ai/models/current', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id: modelId })
    })
    if (res.ok) {
      const data = await res.json()
      selected.value = data.current_model
      emit('changed', data.current_model)
    } else {
      const err = await res.json().catch(() => ({}))
      alert('切換模型失敗: ' + (err.detail || `HTTP ${res.status}`))
      await loadCatalog(true)
    }
  } catch (err) {
    console.error('Failed to switch model:', err)
    alert('無法連線到伺服器切換模型')
    await loadCatalog(true)
  } finally {
    switching.value = false
  }
}

onMounted(() => {
  loadCatalog(false)
  document.addEventListener('visibilitychange', handleVisibility)
})

onBeforeUnmount(() => {
  stopBackgroundPoll()
  document.removeEventListener('visibilitychange', handleVisibility)
})
</script>

<style scoped>
.ai-model-selector-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
}

.selector-wrapper {
  position: relative;
  width: 100%;
}

.glass-select {
  appearance: none;
  width: 100%;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  color: var(--input-text);
  padding: 10px 36px 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.glass-select:focus {
  border-color: var(--input-focus);
  box-shadow: 0 0 0 3px var(--input-focus-shadow);
  outline: none;
}

.glass-select:disabled {
  cursor: wait;
  opacity: 0.6;
}

.glass-select option {
  background: var(--panel-bg);
  color: var(--text-primary);
  padding: 10px;
}

.refresh-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: auto;
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 2px;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: var(--transition);
}

.refresh-btn:hover:not(:disabled) {
  color: var(--accent);
}

.refresh-btn:disabled {
  opacity: 0.4;
  cursor: wait;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
