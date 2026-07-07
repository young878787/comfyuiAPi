<template>
  <div class="app-workspace dark-theme">
    <!-- Header -->
    <header class="app-header">
      <div class="header-logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#6c5ce7" stroke-width="2.5">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        <span>ComfyUI Prompt Editor</span>
        <span class="badge">v1.1</span>
      </div>
      
      <div class="header-actions">
        <StatusIndicator :connected="connected" />
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="app-body">
      <!-- Left Panel: Prompt Inputs & Parameter Form -->
      <section class="panel-left glass-card">
        <div class="section-title">
          <h3>🎨 創作控制台</h3>
          <p>輸入正向提示詞與修改想法，由 AI 自動轉換並送往 ComfyUI 生成圖片</p>
        </div>

        <div class="panel-content scrollable">
          <!-- Workflow Selector -->
          <div class="panel-section">
            <WorkflowSelector
              v-model="activeWorkflow"
              :workflows="workflows"
              @change="handleWorkflowChange"
            />
          </div>

          <!-- Prompt Controls -->
          <div class="panel-section">
            <PromptPanel
              :generating="generating"
              :progress-percentage="progressPercentage"
              :progress-message="progressMessage"
              :error-message="errorMessage"
              @generate="handleGenerate"
              @analyze-image="handleAnalyzeImage"
              @apply-parsed-metadata="handleApplyParsedMetadata"
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
              <ParameterForm v-model:params="params" />
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
          @select-image="handleSelectImage"
          @apply-template="handleApplyTemplate"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatusIndicator from './components/StatusIndicator.vue'
import WorkflowSelector from './components/WorkflowSelector.vue'
import PromptPanel from './components/PromptPanel.vue'
import ParameterForm from './components/ParameterForm.vue'
import ImagePreview from './components/ImagePreview.vue'

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

const handleWorkflowChange = (wfName) => {
  const target = workflows.value.find(w => w.name === wfName)
  if (target) {
    applyWorkflowDefaults(target.defaults)
  }
}

// Load today's history
const loadHistory = async () => {
  try {
    const todayStr = new Date().toISOString().split('T')[0]
    const res = await fetch(`/api/image/list/${todayStr}`)
    if (res.ok) {
      const data = await res.json()
      const loadedHistory = []
      
      // Fetch metadata for each image in history
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
        activeImage.value = loadedHistory[loadedHistory.length - 1]
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
/* Global Dark Theme overrides */
:root {
  --workspace-bg: #0d0e15;
  --panel-bg: rgba(20, 21, 33, 0.6);
  --border-glass: rgba(255, 255, 255, 0.08);
  --text-primary: #f8f9fa;
  --text-muted: #8a8d9a;
  --accent: #6c5ce7;
}

body {
  margin: 0;
  background-color: var(--workspace-bg);
  color: var(--text-primary);
}
</style>

<style scoped>
.app-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: radial-gradient(circle at top right, #1a153b, var(--workspace-bg) 60%);
  overflow: hidden;
}

/* Header */
.app-header {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: rgba(13, 14, 21, 0.8);
  border-bottom: 1px solid var(--border-glass);
  backdrop-filter: blur(10px);
  z-index: 10;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: 0.5px;
  color: #fff;
}

.badge {
  font-size: 0.65rem;
  background: rgba(108, 92, 231, 0.2);
  border: 1px solid rgba(108, 92, 231, 0.4);
  color: #a29bfe;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
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
  border: 1px solid var(--border-glass);
  border-radius: 16px;
  backdrop-filter: blur(25px);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  overflow: hidden;
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
  border-bottom: 1px solid var(--border-glass);
}

.section-title h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: #fff;
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
  border-top: 1px solid var(--border-glass);
  padding-top: 16px;
}

/* Collapsible 고급參數 */
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
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
}

.arrow {
  color: rgba(255, 255, 255, 0.4);
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
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.scrollable::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}
</style>
