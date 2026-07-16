<template>
  <div class="img2img-panel">
    <!-- Batch Upload Area -->
    <div class="input-group">
      <label>🖼️ 批量導入圖片 (批次處理放大)</label>
      <div
        class="image-upload-zone"
        :class="{ 'dragging': isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="triggerFileInput"
      >
        <input
          type="file"
          ref="fileInput"
          class="hidden-file-input"
          accept="image/*"
          multiple
          @change="handleFileSelect"
          :disabled="isGenerating"
        />
        
        <div class="upload-placeholder">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <p>拖曳多張圖片至此處，或點擊上傳</p>
          <span class="sub-text">上傳後將自動解析圖片所含的 AI 生成提示詞</span>
        </div>
      </div>
    </div>

    <!-- Uploaded Image Queue List -->
    <div v-if="batchImages.length > 0" class="image-queue-section">
      <div class="queue-header">
        <h4>📋 待處理佇列 ({{ batchImages.length }} 張圖片)</h4>
        <button @click="clearAllImages" class="btn-clear-all" :disabled="isGenerating">清除全部</button>
      </div>

      <div class="queue-list scrollable-queue">
        <div v-for="(img, idx) in batchImages" :key="img.id" class="queue-item glass-card-micro" :class="img.status">
          <!-- Thumbnail & Info -->
          <div class="item-main">
            <div class="thumb-container">
              <img :src="img.preview" alt="Thumbnail" />
            </div>
            <div class="item-info">
              <div class="file-name">{{ img.name }}</div>
              <div class="item-status-row">
                <span :class="['status-badge', img.status]">
                  {{ getStatusText(img.status) }}
                </span>
                <span v-if="img.status === 'generating'" class="status-percent">
                  {{ img.progress }}%
                </span>
              </div>
            </div>
            
            <!-- Remove Button -->
            <button @click="removeImage(idx)" class="btn-remove-item" :disabled="isGenerating" title="移除">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- Prompt Editing Area -->
          <div class="item-prompt-wrapper">
            <div class="prompt-toggle-header" @click="img.showEdit = !img.showEdit">
              <span>{{ img.prompt ? '📝 偵測到提示詞 (點擊展開修改)' : '❓ 無提示詞 (點擊展開編輯)' }}</span>
              <button class="btn-edit-toggle">
                {{ img.showEdit ? '收起' : '展開' }}
              </button>
            </div>
            <div v-show="img.showEdit" class="prompt-edit-area">
              <textarea
                v-model="img.prompt"
                placeholder="輸入此張圖片的正向提示詞 (不填則套用下方全域提示詞)..."
                class="glass-textarea-small"
                rows="3"
                :disabled="isGenerating"
              ></textarea>
              <textarea
                v-model="img.negativePrompt"
                placeholder="輸入此張圖片的反向提示詞..."
                class="glass-textarea-small"
                rows="2"
                :disabled="isGenerating"
              ></textarea>
            </div>
          </div>

          <!-- Individual Progress Bar -->
          <div v-if="img.status === 'generating'" class="item-progress-bar">
            <div class="bar-fill" :style="{ width: img.progress + '%' }"></div>
          </div>
          
          <!-- Error details -->
          <div v-if="img.error" class="item-error-msg">
            ⚠️ {{ img.error }}
          </div>
        </div>
      </div>
    </div>

    <!-- Global Prompt Fallbacks -->
    <div class="input-group">
      <div class="input-header">
        <label>📝 全域正向提示詞 (Global Prompt Fallback)</label>
      </div>
      <textarea
        v-model="globalPrompt"
        placeholder="當上傳圖片未內嵌提示詞，且個別圖片未特別設定時，將套用此提示詞…"
        class="glass-textarea prompt-area"
        rows="4"
        :disabled="isGenerating"
      ></textarea>
    </div>

    <div class="input-group">
      <div class="input-header">
        <label>💡 全域反向提示詞 (Global Negative Fallback)</label>
      </div>
      <textarea
        v-model="globalNegative"
        placeholder="反向提示詞..."
        class="glass-textarea idea-area"
        rows="3"
        :disabled="isGenerating"
      ></textarea>
    </div>

    <!-- Generate Action -->
    <div class="generate-control">
      <!-- Error banner -->
      <div v-if="errorMessage" class="error-banner">
        <span>⚠️ {{ errorMessage }}</span>
      </div>

      <button
        @click="startBatchGeneration"
        :disabled="isGenerating || batchImages.length === 0"
        :class="['btn-generate', isGenerating ? 'generating' : '']"
      >
        <span v-if="!isGenerating" class="btn-content">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          開始批量放大 (共 {{ batchImages.length }} 張)
        </span>
        <span v-else class="btn-content">
          <div class="generating-spinner"></div>
          正在批量生成中 ({{ activeIndex + 1 }} / {{ batchImages.length }}) - {{ activeProgress }}%
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  workflow: {
    type: String,
    default: 'anima-放大'
  },
  params: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['image-generated', 'update:params'])

// State
const batchImages = ref([])
const isDragging = ref(false)
const fileInput = ref(null)
const isGenerating = ref(false)
const errorMessage = ref('')

const globalPrompt = ref('')
const globalNegative = ref('lowres, extra digit, fewer digits, worst quality, jpeg artifacts, signature, watermark, artist name, bad perspective, artistic error, bad proportions, disfigured, deformed body, malformed limbs, flat color, outline, nsfw, sepia, logo')

const activeIndex = ref(0)
const activeProgress = ref(0)

// Helper: Trigger file select click
const triggerFileInput = () => {
  if (!isGenerating.value) {
    fileInput.value.click()
  }
}

// Helper: Handle file select
const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  addFilesToQueue(files)
  e.target.value = '' // Clear input
}

// Helper: Handle Drop
const handleDrop = (e) => {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'))
  addFilesToQueue(files)
}

// Add files to queue and trigger metadata parsing in background
const addFilesToQueue = (files) => {
  files.forEach(file => {
    const id = Math.random().toString(36).substring(2, 9)
    const preview = URL.createObjectURL(file)
    const newImg = ref({
      id,
      file,
      name: file.name,
      preview,
      prompt: '',
      negativePrompt: '',
      status: 'parsing',
      progress: 0,
      showEdit: false,
      error: ''
    })
    
    batchImages.value.push(newImg.value)
    parseMetadata(newImg.value)
  })
}

// Parse Image Metadata in background
const parseMetadata = async (imgObj) => {
  try {
    const formData = new FormData()
    formData.append('file', imgObj.file)
    
    const response = await fetch('/api/image/parse-metadata', {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data && data.positivePrompt) {
        imgObj.prompt = data.positivePrompt
      }
      if (data && data.negativePrompt) {
        imgObj.negativePrompt = data.negativePrompt
      }
    }
  } catch (err) {
    console.error('Failed to parse metadata for file ' + imgObj.name, err)
  } finally {
    imgObj.status = 'pending'
  }
}

// Clear single item
const removeImage = (idx) => {
  const imgObj = batchImages.value[idx]
  if (imgObj.preview) {
    URL.revokeObjectURL(imgObj.preview)
  }
  batchImages.value.splice(idx, 1)
}

// Clear all items
const clearAllImages = () => {
  batchImages.value.forEach(img => {
    if (img.preview) {
      URL.revokeObjectURL(img.preview)
    }
  })
  batchImages.value = []
}

// Status text mapping
const getStatusText = (status) => {
  switch (status) {
    case 'parsing': return '⏳ 解析提示詞中...'
    case 'pending': return '⚪ 等待處理'
    case 'generating': return '⚡ 放大繪圖中...'
    case 'done': return '✅ 放大成功'
    case 'failed': return '❌ 處理失敗'
    default: return status
  }
}

// Convert file to Base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => {
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = error => reject(error)
  })
}

// Queue execution loop
const startBatchGeneration = async () => {
  if (isGenerating.value) return
  isGenerating.value = true
  errorMessage.value = ''
  
  // 記錄當端批量放大啟動時的 workflow 與 params，避免在跑圖期間切換 Tab 造成後續佇列的參數被修改
  const currentWorkflow = props.workflow
  const currentParams = { ...props.params }
  
  for (let i = 0; i < batchImages.value.length; i++) {
    const img = batchImages.value[i]
    if (img.status === 'done') continue
    
    activeIndex.value = i
    img.status = 'generating'
    img.progress = 0
    img.error = ''
    activeProgress.value = 0
    
    try {
      const base64Str = await fileToBase64(img.file)
      
      const reqBody = {
        prompt: img.prompt.trim() || globalPrompt.value.trim(),
        idea: '', // no AI modification during upscale
        attempts: 1,
        workflow: currentWorkflow,
        width: currentParams.width,
        height: currentParams.height,
        steps: currentParams.steps,
        cfg: currentParams.cfg,
        seed: currentParams.seed,
        sampler: currentParams.sampler,
        scheduler: currentParams.scheduler,
        negative_prompt: img.negativePrompt.trim() || globalNegative.value.trim(),
        image_base64: base64Str,
        image_mime_type: img.file.type,
        checkpoint: currentParams.checkpoint || null
      }
      
      await runSingleGeneration(img, reqBody)
      img.status = 'done'
      img.progress = 100
    } catch (err) {
      console.error(err)
      img.status = 'failed'
      img.error = err.message || '生成失敗'
    }
  }
  
  isGenerating.value = false
}

// Run single generation request and stream SSE progress
const runSingleGeneration = (imgObj, reqBody) => {
  return new Promise(async (resolve, reject) => {
    try {
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
        buffer = lines.pop()
        
        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data: ')) {
            try {
              const event = JSON.parse(trimmed.slice(6))
              
              if (event.type === 'progress') {
                const current = event.completed
                const total = event.total
                
                // Map KSampler rendering (starts from 20% to 95%)
                const ratio = total > 0 ? (current / total) : 0
                const percent = Math.floor(20 + ratio * 75)
                
                imgObj.progress = percent
                activeProgress.value = percent
              } else if (event.type === 'error') {
                reject(new Error(event.message || '生成失敗'))
                return
              } else if (event.type === 'failure') {
                // Backend sends 'failure' when ComfyUI pipeline errors
                reject(new Error(event.error || '圖片生成失敗'))
                return
              } else if (event.type === 'done') {
                imgObj.progress = 100
                activeProgress.value = 100
                
                // Trigger parent component to reload image list
                emit('image-generated')
                resolve()
                return
              }
            } catch (parseErr) {
              console.error('Error parsing SSE event:', parseErr)
            }
          }
        }
      }
      // SSE stream ended without a 'done' event
      reject(new Error('SSE 連線已關閉但未收到完成事件'))
    } catch (err) {
      reject(err)
    }
  })
}
</script>

<style scoped>
.img2img-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
}

.glass-textarea {
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  color: var(--input-text);
  padding: 12px;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  line-height: 1.5;
  transition: var(--transition);
}

.glass-textarea:focus {
  border-color: var(--input-focus);
  background: var(--input-bg);
  box-shadow: 0 0 0 3px var(--input-focus-shadow);
  outline: none;
}

.glass-textarea-small {
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  color: var(--input-text);
  padding: 8px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  line-height: 1.4;
  width: 100%;
  resize: vertical;
  margin-top: 4px;
  transition: var(--transition);
}

.glass-textarea-small:focus {
  border-color: var(--input-focus);
  box-shadow: 0 0 0 3px var(--input-focus-shadow);
  outline: none;
}

.prompt-area {
  font-family: monospace;
}

/* Image Upload Area */
.image-upload-zone {
  border: 1.5px dashed var(--input-border);
  background: var(--input-bg);
  border-radius: var(--radius-md);
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--transition);
  padding: 20px;
}

.image-upload-zone:hover, .image-upload-zone.dragging {
  border-color: var(--accent);
  background: var(--accent-light);
}

.hidden-file-input {
  display: none;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 0.82rem;
  text-align: center;
}

.upload-placeholder svg {
  opacity: 0.7;
  margin-bottom: 4px;
}

.sub-text {
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* Queue List Section */
.image-queue-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-top: 1px solid var(--panel-border);
  padding-top: 14px;
}

.queue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.queue-header h4 {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
}

.btn-clear-all {
  font-size: 0.7rem;
  background: var(--danger-light);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition);
}

.btn-clear-all:hover:not(:disabled) {
  background: var(--danger);
  color: white;
}

.scrollable-queue {
  max-height: 280px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
}

/* Scrollbar styling */
.scrollable-queue::-webkit-scrollbar {
  width: 4px;
}
.scrollable-queue::-webkit-scrollbar-track {
  background: transparent;
}
.scrollable-queue::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 2px;
}

/* Queue Item Glass Card */
.queue-item {
  border-radius: var(--radius-sm);
  background: var(--input-bg);
  border: 1px solid var(--panel-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: var(--transition);
}

.queue-item.generating {
  border-color: var(--accent);
  background: var(--accent-light);
}

.queue-item.done {
  border-color: var(--success);
}

.queue-item.failed {
  border-color: var(--danger);
}

.item-main {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  gap: 10px;
  position: relative;
}

.thumb-container {
  width: 40px;
  height: 40px;
  border-radius: 4px;
  overflow: hidden;
  background: var(--button-ghost-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--panel-border);
}

.thumb-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.file-name {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge {
  font-size: 0.65rem;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--button-ghost-hover);
  color: var(--text-muted);
}

.status-badge.generating {
  background: var(--accent-light);
  color: var(--accent);
  border: 1px solid var(--accent);
}

.status-badge.done {
  background: var(--button-ghost-hover);
  color: var(--success);
  border: 1px solid var(--success);
}

.status-badge.failed {
  background: var(--danger-light);
  color: var(--danger);
  border: 1px solid var(--danger);
}

.status-percent {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--accent);
}

.btn-remove-item {
  background: transparent;
  border: none;
  color: var(--text-muted);
  padding: 4px;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}

.btn-remove-item:hover:not(:disabled) {
  color: var(--danger);
  background: var(--danger-light);
}

/* Prompt Edit Section */
.item-prompt-wrapper {
  background: var(--button-ghost-hover);
  border-top: 1px solid var(--panel-border);
  font-size: 0.72rem;
}

.prompt-toggle-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  cursor: pointer;
  color: var(--text-muted);
  user-select: none;
}

.prompt-toggle-header:hover {
  background: var(--panel-border);
  color: var(--text-primary);
}

.btn-edit-toggle {
  background: transparent;
  border: none;
  color: var(--accent);
  font-size: 0.7rem;
  cursor: pointer;
  font-weight: 500;
}

.prompt-edit-area {
  padding: 2px 10px 10px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Progress bar inside queue item */
.item-progress-bar {
  width: 100%;
  height: 2px;
  background: var(--input-border);
  position: relative;
}

.bar-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s;
}

.item-error-msg {
  padding: 6px 10px;
  background: var(--danger-light);
  color: var(--danger);
  font-size: 0.7rem;
  border-top: 1px solid var(--danger);
}

/* Generate controls */
.generate-control {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.error-banner {
  background: var(--danger-light);
  border: 1px solid var(--danger);
  color: var(--danger);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
}

.btn-generate {
  width: 100%;
  background: var(--accent);
  border: none;
  color: var(--accent-text);
  padding: 12px;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-weight: 600;
  box-shadow: var(--card-shadow);
  cursor: pointer;
  transition: var(--transition);
}

.btn-generate:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1.5px);
  box-shadow: var(--panel-shadow);
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-generate.generating {
  background: var(--button-ghost-hover);
  border: 1px solid var(--panel-border);
  color: var(--text-muted);
  cursor: wait;
  box-shadow: none;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.generating-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--panel-border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.glass-card-micro {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
}
</style>
