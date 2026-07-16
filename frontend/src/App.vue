<template>
  <div :class="['app-workspace', isDark ? 'dark-theme' : 'light-theme']">
    <!-- Header -->
    <header class="app-header">
      <div class="header-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.5">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <span>ComfyUI Prompt Editor</span>
        <span class="badge">v1.1</span>
      </div>
      
      <!-- Navigation Tabs -->
      <div class="header-nav">
        <button :class="['nav-tab', activeTab === 'txt2img' ? 'active' : '']" @click="handleTabChange('txt2img')">
          ✍️ 文生圖
        </button>
        <button :class="['nav-tab', activeTab === 'img2img' ? 'active' : '']" @click="handleTabChange('img2img')">
          🖼️ 圖生圖 (放大)
        </button>
      </div>

      <div class="header-actions">
        <button class="theme-toggle-btn" @click="toggleTheme" :title="isDark ? '切換為暖陽白' : '切換為暖閣黑'">
          <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
        </button>
        <StatusIndicator :connected="connected" />
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="app-body">
      <!-- Left Panel: Prompt Inputs & Parameter Form -->
      <section class="panel-left glass-card">
        <div class="section-title">
          <h3>🎨 {{ activeTab === 'txt2img' ? '創作控制台' : '批量放大控制台' }}</h3>
          <p>{{ activeTab === 'txt2img' ? '輸入正向提示詞與修改想法，由 AI 自動轉換並送往 ComfyUI 生成圖片' : '導入圖片佇列，系統將讀取提示詞並送往 ComfyUI 批量放大處理' }}</p>
        </div>

        <div class="panel-content scrollable">
          <!-- Workflow Selector -->
          <div class="panel-section">
            <WorkflowSelector
              v-model="activeWorkflow"
              :workflows="filteredWorkflows"
              @change="handleWorkflowChange"
            />
          </div>

          <!-- Prompt Controls -->
          <div class="panel-section">
            <PromptPanel
              v-show="activeTab === 'txt2img'"
              :generating="generating"
              :progress-percentage="progressPercentage"
              :progress-message="progressMessage"
              :error-message="errorMessage"
              @generate="handleGenerate"
              @analyze-image="handleAnalyzeImage"
              @apply-parsed-metadata="handleApplyParsedMetadata"
            />
            <Img2ImgPanel
              v-show="activeTab === 'img2img'"
              :workflow="activeWorkflow"
              :params="params"
              @image-generated="loadHistory"
            />
          </div>

          <!-- Parameter Form -->
          <div class="panel-section divider">
            <div class="collapsible-header" @click="showParams = !showParams">
              <h4>⚙️ 生成高級參數</h4>
              <svg :class="['arrow', showParams ? 'open' : '']" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </div>
            <div class="collapsible-content" v-show="showParams">
              <ParameterForm v-model:params="params" :hide-resolution="activeTab === 'img2img'" />
            </div>
          </div>
        </div>
      </section>

      <!-- Right Panel: Big Preview & Metadata & History -->
      <section class="panel-right glass-card">
        <ImagePreview
          :active-image="activeImage"
          :history="history"
          :generating="generating"
          :progress-percentage="progressPercentage"
          :progress-message="progressMessage"
          @select-image="handleSelectImage"
          @apply-template="handleApplyTemplate"
          @delete-image="handleDeleteImage"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import StatusIndicator from './components/StatusIndicator.vue'
import WorkflowSelector from './components/WorkflowSelector.vue'
import PromptPanel from './components/PromptPanel.vue'
import Img2ImgPanel from './components/Img2ImgPanel.vue'
import ParameterForm from './components/ParameterForm.vue'
import ImagePreview from './components/ImagePreview.vue'

// Theme state
const isDark = ref(localStorage.getItem('theme') !== 'light')
const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

// Tab state
const activeTab = ref('txt2img') // 'txt2img' or 'img2img'

// Connection state
const connected = ref(false)
const workflows = ref([])
const activeWorkflow = ref('anima')
const showParams = ref(true)

// Generation state
const generating = ref(false)
const progressPercentage = ref(0)
const progressMessage = ref('')
const errorMessage = ref('')

// Image preview state
const activeImage = ref(null)
const history = ref([])

// Params model
const params = ref({
  width: 600,
  height: 1328,
  steps: 35,
  cfg: 4.0,
  seed: null,
  sampler: 'dpmpp_2m_sde',
  scheduler: 'simple',
  attempts: 1,
  negative_prompt: '',
  checkpoint: ''
})

// Fetch initial configuration
const fetchConfig = async () => {
  try {
    const res = await fetch('/api/config')
    if (res.ok) {
      const data = await res.json()
      connected.value = data.connected
      workflows.value = data.workflows
      activeWorkflow.value = data.default_workflow
      
      // Load default parameters for selected workflow
      const defaultWf = data.workflows.find(w => w.name === data.default_workflow)
      if (defaultWf) {
        applyWorkflowDefaults(defaultWf.defaults)
      }
    }
  } catch (err) {
    console.error('Failed to load configs:', err)
  }
}

const applyWorkflowDefaults = (defaults) => {
  params.value = {
    ...params.value,
    width: defaults.width || params.value.width,
    height: defaults.height || params.value.height,
    steps: defaults.steps || params.value.steps,
    cfg: defaults.cfg || params.value.cfg,
    sampler: defaults.sampler || params.value.sampler,
    scheduler: defaults.scheduler || params.value.scheduler,
    negative_prompt: defaults.negative_prompt || params.value.negative_prompt
  }
}

// Filter workflows based on active tab
const filteredWorkflows = computed(() => {
  if (activeTab.value === 'img2img') {
    return workflows.value.filter(w => w.name.includes('放大') || w.name.includes('upscale'))
  } else {
    return workflows.value.filter(w => !w.name.includes('放大') && !w.name.includes('upscale'))
  }
})

// Tab Switch Handler
const handleTabChange = (tab) => {
  activeTab.value = tab
  const list = filteredWorkflows.value
  if (list.length > 0) {
    activeWorkflow.value = list[0].name
    applyWorkflowDefaults(list[0].defaults)
  }
}

const handleWorkflowChange = (wfName) => {
  const target = workflows.value.find(w => w.name === wfName)
  if (target) {
    applyWorkflowDefaults(target.defaults)
  }
}

// Load today's history
const loadHistory = async () => {
  try {
    const d = new Date()
    const todayStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    const res = await fetch(`/api/image/list/${todayStr}`)
    if (res.ok) {
      const data = await res.json()
      
      if (data.images_details && data.images_details.length > 0) {
        history.value = data.images_details
        const stillExists = activeImage.value && data.images_details.some(img => img.filename === activeImage.value.filename)
        if (!stillExists) {
          activeImage.value = data.images_details[data.images_details.length - 1]
        }
        return
      }
      
      // Fallback in case backend details list is empty or fails
      const loadedHistory = []
      for (const filename of data.images) {
        try {
          const metaRes = await fetch(`/api/image/metadata/${todayStr}/${filename}`)
          if (metaRes.ok) {
            const metaData = await metaRes.json()
            loadedHistory.push(metaData)
          } else {
            loadedHistory.push({
              filename,
              url: `/api/image/view/${todayStr}/${filename}`,
              metadata: null
            })
          }
        } catch (e) {
          loadedHistory.push({
            filename,
            url: `/api/image/view/${todayStr}/${filename}`,
            metadata: null
          })
        }
      }
      
      history.value = loadedHistory
      if (loadedHistory.length > 0) {
        const stillExists = activeImage.value && loadedHistory.some(img => img.filename === activeImage.value.filename)
        if (!stillExists) {
          activeImage.value = loadedHistory[loadedHistory.length - 1]
        }
      } else {
        activeImage.value = null
      }
    }
  } catch (err) {
    console.error('Failed to load history list:', err)
  }
}

// Select history image
const handleSelectImage = (img) => {
  activeImage.value = img
}

// Delete image from history and disk
const handleDeleteImage = async (img) => {
  if (!img) return
  // Extract date from URL path (e.g. /api/image/view/2026-07-07/001.png)
  const parts = img.url.split('/')
  if (parts.length >= 3) {
    const dateStr = parts[parts.length - 2]
    const filename = parts[parts.length - 1]
    
    try {
      const res = await fetch(`/api/image/${dateStr}/${filename}`, {
        method: 'DELETE'
      })
      if (res.ok) {
        // Remove from local history array
        const idx = history.value.findIndex(item => item.filename === filename)
        if (idx !== -1) {
          history.value.splice(idx, 1)
        }
        
        // Update active image selection
        if (activeImage.value && activeImage.value.filename === filename) {
          if (history.value.length > 0) {
            // Select the neighboring image
            const nextActiveIdx = Math.min(idx, history.value.length - 1)
            activeImage.value = history.value[nextActiveIdx]
          } else {
            activeImage.value = null
          }
        }
      } else {
        const errorData = await res.json()
        alert('刪除圖片失敗: ' + (errorData.detail || '未知錯誤'))
      }
    } catch (err) {
      alert('無法連線到伺服器進行刪除: ' + err.message)
    }
  }
}

// Apply selected history template back into editor
const handleApplyTemplate = (img) => {
  if (img && img.metadata) {
    params.value = {
      ...params.value,
      width: img.metadata.width,
      height: img.metadata.height,
      steps: img.metadata.steps,
      cfg: img.metadata.cfg,
      sampler: img.metadata.sampler,
      scheduler: img.metadata.scheduler,
      negative_prompt: img.metadata.negative_prompt,
      seed: img.metadata.seed,
      checkpoint: img.metadata.checkpoint || ''
    }
    // Set custom event or notify that prompts should be populated
    // We can also target prompt element directly or broadcast it
    const promptArea = document.getElementById('original-prompt')
    const ideaArea = document.getElementById('modification-idea')
    if (promptArea) promptArea.value = img.metadata.original_prompt || ''
    if (ideaArea) ideaArea.value = img.metadata.user_idea || ''
    // Dispatch input events manually to trigger vue v-model binding updates
    if (promptArea) promptArea.dispatchEvent(new Event('input'))
    if (ideaArea) ideaArea.dispatchEvent(new Event('input'))
  }
}

// Analyze Uploaded Image
const handleAnalyzeImage = async ({ file, onSuccess, onError }) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch('/api/image/analyze', {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const data = await response.json()
      onSuccess(data.result)
    } else {
      const errText = await response.text()
      onError(errText)
    }
  } catch (e) {
    onError(e.message)
  }
}

// Handle applying metadata parsed from PNG images
const handleApplyParsedMetadata = (parsed) => {
  if (parsed && parsed.params) {
    params.value = {
      ...params.value,
      width: parsed.params.width || params.value.width,
      height: parsed.params.height || params.value.height,
      steps: parsed.params.steps || params.value.steps,
      cfg: parsed.params.cfg || params.value.cfg,
      sampler: parsed.params.sampler || params.value.sampler,
      scheduler: parsed.params.scheduler || params.value.scheduler,
      negative_prompt: parsed.params.negativePrompt || parsed.params.negative_prompt || params.value.negative_prompt,
      seed: parsed.params.seed !== undefined ? parsed.params.seed : params.value.seed
    }
  }
}

// Handle Generate Streaming SSE Connection
const handleGenerate = async (data) => {
  generating.value = true
  progressPercentage.value = 10
  progressMessage.value = '⏳ 初始化連接...'
  errorMessage.value = ''
  activeImage.value = null
  
  try {
    const reqBody = {
      prompt: data.prompt || '',
      idea: data.idea || '',
      attempts: params.value.attempts,
      workflow: activeWorkflow.value,
      width: params.value.width,
      height: params.value.height,
      steps: params.value.steps,
      cfg: params.value.cfg,
      seed: params.value.seed,
      sampler: params.value.sampler,
      scheduler: params.value.scheduler,
      negative_prompt: params.value.negative_prompt,
      checkpoint: params.value.checkpoint || null
    }
    
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(reqBody)
    })
    
    if (!response.ok) {
      throw new Error(`伺服器連線失敗 (${response.status})`)
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      
      // Keep last half-line in buffer
      buffer = lines.pop()
      
      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('data: ')) {
          try {
            const event = JSON.parse(trimmed.slice(6))
            
            if (event.type === 'progress') {
              const current = event.completed
              const total = event.total
              progressMessage.value = event.message
              // Map AI edit to 15% and ComfyUI rendering from 20% to 95%
              if (event.message.includes('AI')) {
                progressPercentage.value = 15
              } else {
                const ratio = total > 0 ? (current / total) : 0
                progressPercentage.value = Math.floor(20 + ratio * 75)
              }
            } else if (event.type === 'heartbeat') {
              progressMessage.value = event.message
            } else if (event.type === 'error') {
              throw new Error(event.message)
            } else if (event.type === 'done') {
              progressPercentage.value = 100
              progressMessage.value = '✅ 生成完成！'
              
              // Load today's history to retrieve all metadata and images
              await loadHistory()
              generating.value = false
              return
            }
          } catch (err) {
            console.error('SSE line parse error:', err)
          }
        }
      }
    }
  } catch (err) {
    console.error('Streaming failed:', err)
    errorMessage.value = err.message || '生成失敗，請檢查後端日誌。'
    generating.value = false
    progressPercentage.value = 0
  }
}

onMounted(() => {
  fetchConfig()
  loadHistory()
  
  // Status check loop
  setInterval(async () => {
    try {
      const res = await fetch('/api/status')
      if (res.ok) {
        const data = await res.json()
        connected.value = data.connected
      }
    } catch {
      connected.value = false
    }
  }, 5000)
})
</script>

<style>
body {
  margin: 0;
  background-color: var(--workspace-bg);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
</style>

<style scoped>
.app-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: var(--workspace-bg);
  overflow: hidden;
  transition: background-color 0.3s ease;
}

/* Header */
.app-header {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: var(--panel-bg);
  border-bottom: 1px solid var(--panel-border);
  z-index: 10;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 1.1rem;
  letter-spacing: 0.5px;
  color: var(--text-primary);
}

.badge {
  font-size: 0.65rem;
  background: var(--accent-light);
  border: 1px solid var(--accent);
  color: var(--accent);
  opacity: 0.85;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-toggle-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
}

.theme-toggle-btn:hover {
  background: var(--button-ghost-hover);
  color: var(--text-primary);
}

/* Body layout */
.app-body {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

.glass-card {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  box-shadow: var(--panel-shadow);
  overflow: hidden;
  transition: background-color 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}

.panel-left {
  flex: 5;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.panel-right {
  flex: 4;
  height: 100%;
  padding: 20px;
}

.section-title {
  padding: 20px;
  border-bottom: 1px solid var(--panel-border);
}

.section-title h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.section-title p {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-section {
  width: 100%;
}

.panel-section.divider {
  border-top: 1px solid var(--panel-border);
  padding-top: 16px;
}

/* Collapsible 高級參數 */
.collapsible-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.collapsible-header h4 {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-primary);
  opacity: 0.8;
  text-transform: uppercase;
}

.arrow {
  color: var(--text-muted);
  transition: transform 0.3s;
}

.arrow.open {
  transform: rotate(180deg);
}

.collapsible-content {
  margin-top: 12px;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.scrollable::-webkit-scrollbar {
  width: 6px;
}

.scrollable::-webkit-scrollbar-track {
  background: transparent;
}

.scrollable::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 3px;
}

.scrollable::-webkit-scrollbar-thumb:hover {
  background: var(--scrollbar-thumb-hover);
}

/* Navigation Tabs in Header */
.header-nav {
  display: flex;
  gap: 4px;
  background: var(--button-ghost-hover);
  padding: 4px;
  border-radius: var(--radius-md);
  border: 1px solid var(--panel-border);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.nav-tab {
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-tab:hover {
  color: var(--text-primary);
}

.nav-tab.active {
  color: var(--accent-text);
  background: var(--accent);
  box-shadow: var(--card-shadow);
}
</style>
