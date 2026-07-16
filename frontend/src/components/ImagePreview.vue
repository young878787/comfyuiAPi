<template>
  <div class="image-preview-container">
    <!-- Active Image Area -->
    <div class="active-image-card">
      <div v-if="activeImage" class="active-image-wrapper">
        <img :src="activeImage.url" alt="Generated Image" class="main-image" @click="openLightbox" title="點擊放大圖片" />
        
        <div class="image-overlay-actions">
          <a :href="downloadUrl" download class="btn-action-round" title="下載此圖片">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </a>
          <button @click="useAsTemplate" class="btn-action-round" title="帶入此提示詞與參數">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
          </button>
        </div>
      </div>
      
      <div v-else-if="generating" class="generating-placeholder">
        <div class="glow-ring">
          <div class="spinner"></div>
          <span class="spinner-percent" v-if="progressPercentage > 0">{{ progressPercentage }}%</span>
        </div>
        <p class="pulse-text">{{ progressMessage || 'AI 正在精心繪製您的創作中...' }}</p>
        <div class="progress-bar-container" v-if="progressPercentage > 0">
          <div class="progress-bar-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <span class="sub-text">ComfyUI 排程渲染中，請稍候</span>
      </div>
      
      <div v-else class="empty-placeholder">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
        <h3>尚無生成的圖片</h3>
        <p>請在左側輸入提示詞並點擊「開始生成」來開始生圖。</p>
      </div>
    </div>

    <!-- Action Toolbar under image -->
    <div v-if="activeImage" class="image-toolbar-under">
      <button @click="openImageFolder" class="toolbar-btn" title="開啟 ComfyUI 輸出資料夾並選取圖片">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f39c12" stroke-width="2.5">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
        </svg>
        <span>開啟資料夾</span>
      </button>
      <div class="toolbar-divider"></div>
      <a :href="downloadUrl" download class="toolbar-btn" title="下載此圖片">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2ec4b6" stroke-width="2.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        <span>下載圖片</span>
      </a>
      <div class="toolbar-divider"></div>
      <button @click="useAsTemplate" class="toolbar-btn" title="帶入此提示詞與參數">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a29bfe" stroke-width="2.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
        </svg>
        <span>套用參數</span>
      </button>
      <div class="toolbar-divider"></div>
      <button @click="deleteCurrentImage" class="toolbar-btn delete-btn" title="刪除此圖片與參數記錄">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ff7675" stroke-width="2.5">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          <line x1="10" y1="11" x2="10" y2="17"></line>
          <line x1="14" y1="11" x2="14" y2="17"></line>
        </svg>
        <span>刪除圖片</span>
      </button>
    </div>

    <!-- Image History Slider -->
    <div class="history-section" v-if="history.length > 0">
      <div class="section-header">
        <h4>📁 歷史生成圖片 (今日)</h4>
        <span class="count-tag">{{ history.length }} 張</span>
      </div>
      <div class="history-track">
        <div
          v-for="(img, idx) in history"
          :key="img.filename"
          :class="['thumb-card', activeImage && activeImage.filename === img.filename ? 'active' : '']"
          @click="selectImage(img)"
        >
          <img :src="img.url" alt="Thumb" />
          <div class="thumb-badge">{{ idx + 1 }}</div>
        </div>
      </div>
    </div>

    <!-- Metadata Details Card -->
    <div class="metadata-card" v-if="activeImage && activeImage.metadata">
      <div class="metadata-header">
        <h4>🎨 圖片參數與 AI 軌跡</h4>
      </div>
      <div class="metadata-grid">
        <div class="meta-item span-2" v-if="activeImage.metadata.original_prompt">
          <div class="meta-header-inline">
            <span class="meta-label">原始提示詞:</span>
            <div class="meta-actions">
              <button 
                class="meta-action-btn" 
                @click="copyText(activeImage.metadata.original_prompt, 'original')"
                :title="copiedOriginal ? '已複製！' : '複製原始提示詞'"
              >
                <span class="action-icon">
                  <svg v-if="copiedOriginal" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2ec4b6" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                </span>
                <span class="action-text" :class="{ success: copiedOriginal }">
                  {{ copiedOriginal ? '已複製！' : '複製' }}
                </span>
              </button>
              
              <button 
                v-if="isLongPrompt(activeImage.metadata.original_prompt)"
                class="meta-action-btn" 
                @click="isExpandedOriginal = !isExpandedOriginal"
                :title="isExpandedOriginal ? '收合提示詞' : '展開完整提示詞'"
              >
                <span class="action-icon">
                  <svg v-if="isExpandedOriginal" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </span>
                <span class="action-text">
                  {{ isExpandedOriginal ? '收合' : '展開' }}
                </span>
              </button>
            </div>
          </div>
          <div class="prompt-container" :class="{ expanded: isExpandedOriginal }">
            <span class="meta-val code">{{ activeImage.metadata.original_prompt }}</span>
          </div>
        </div>
        <div class="meta-item span-2" v-if="activeImage.metadata.user_idea">
          <span class="meta-label">修改想法 (Idea):</span>
          <span class="meta-val idea">{{ activeImage.metadata.user_idea }}</span>
        </div>
        <div class="meta-item span-2">
          <div class="meta-header-inline">
            <span class="meta-label">最終提示詞 (Positive Prompt):</span>
            <div class="meta-actions">
              <button 
                class="meta-action-btn" 
                @click="copyText(activeImage.metadata.positive_prompt, 'positive')"
                :title="copiedPositive ? '已複製！' : '複製最終提示詞'"
              >
                <span class="action-icon">
                  <svg v-if="copiedPositive" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2ec4b6" stroke-width="2.5">
                    <polyline points="20 6 9 17 4 12"></polyline>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                  </svg>
                </span>
                <span class="action-text" :class="{ success: copiedPositive }">
                  {{ copiedPositive ? '已複製！' : '複製' }}
                </span>
              </button>
              
              <button 
                v-if="isLongPrompt(activeImage.metadata.positive_prompt)"
                class="meta-action-btn" 
                @click="isExpandedPositive = !isExpandedPositive"
                :title="isExpandedPositive ? '收合提示詞' : '展開完整提示詞'"
              >
                <span class="action-icon">
                  <svg v-if="isExpandedPositive" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                  <svg v-else width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </span>
                <span class="action-text">
                  {{ isExpandedPositive ? '收合' : '展開' }}
                </span>
              </button>
            </div>
          </div>
          <div class="prompt-container" :class="{ expanded: isExpandedPositive }">
            <span class="meta-val code final">{{ activeImage.metadata.positive_prompt }}</span>
          </div>
        </div>
        <div class="meta-item">
          <span class="meta-label">寬度 x 高度:</span>
          <span class="meta-val">{{ activeImage.metadata.width }} x {{ activeImage.metadata.height }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">採樣步數 (Steps):</span>
          <span class="meta-val">{{ activeImage.metadata.steps }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">CFG Scale:</span>
          <span class="meta-val">{{ activeImage.metadata.cfg }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">隨機種子 (Seed):</span>
          <span class="meta-val code">{{ activeImage.metadata.seed }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">採樣與調度:</span>
          <span class="meta-val">{{ activeImage.metadata.sampler }} ({{ activeImage.metadata.scheduler }})</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">工作流 (Workflow):</span>
          <span class="meta-val">{{ activeImage.metadata.workflow_name || '預設' }}</span>
        </div>
        <div class="meta-item span-2" v-if="activeImage.metadata.ai_model">
          <span class="meta-label">AI 提示詞模型:</span>
          <span class="meta-val robot">🤖 {{ activeImage.metadata.ai_model }} ({{ activeImage.metadata.ai_provider }})</span>
        </div>
      </div>
    </div>

    <!-- Lightbox Modal -->
    <Teleport to="body">
      <Transition name="lightbox-fade">
        <div v-if="showLightbox && activeImage" class="lightbox-overlay" @click="showLightbox = false">
          <div class="lightbox-close-btn" @click="showLightbox = false" title="關閉 (Esc)">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </div>
          
          <!-- Left/Right Navigation Buttons -->
          <button 
            v-if="hasPrev" 
            class="lightbox-nav-btn prev-btn" 
            @click.stop="navigateImage(-1)" 
            title="上一張 (左方向鍵)"
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>

          <button 
            v-if="hasNext" 
            class="lightbox-nav-btn next-btn" 
            @click.stop="navigateImage(1)" 
            title="下一張 (右方向鍵)"
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>

          <div class="lightbox-content" @click.stop>
            <div :class="['lightbox-image-wrapper', isZoomed ? 'zoomed' : '']">
              <img 
                :src="activeImage.url" 
                alt="Fullscreen Preview" 
                :class="['lightbox-image', isZoomed ? 'zoom-out' : 'zoom-in']"
                @click="toggleZoom" 
                :title="isZoomed ? '點擊縮小適應螢幕' : '點擊放大至原始尺寸'"
              />
            </div>
            
            <div class="lightbox-actions-panel">
              <span class="lightbox-info" v-if="activeImage.metadata">
                {{ activeImage.metadata.width }} × {{ activeImage.metadata.height }}
              </span>
              <a :href="downloadUrl" download class="btn-lightbox-action" title="下載原圖">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                下載原圖
              </a>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({
  activeImage: {
    type: Object,
    default: null
  },
  history: {
    type: Array,
    default: () => []
  },
  generating: {
    type: Boolean,
    default: false
  },
  progressPercentage: {
    type: Number,
    default: 0
  },
  progressMessage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select-image', 'apply-template', 'delete-image'])

// Lightbox states
const showLightbox = ref(false)
const isZoomed = ref(false)

const openLightbox = () => {
  if (props.activeImage) {
    showLightbox.value = true
    isZoomed.value = false
  }
}

const toggleZoom = () => {
  isZoomed.value = !isZoomed.value
}

// Lightbox navigation logic
const currentIndex = computed(() => {
  if (!props.activeImage || !props.history.length) return -1
  return props.history.findIndex(img => img.filename === props.activeImage.filename)
})

const hasPrev = computed(() => {
  return currentIndex.value > 0
})

const hasNext = computed(() => {
  return currentIndex.value !== -1 && currentIndex.value < props.history.length - 1
})

const navigateImage = (direction) => {
  const newIndex = currentIndex.value + direction
  if (newIndex >= 0 && newIndex < props.history.length) {
    isZoomed.value = false
    selectImage(props.history[newIndex])
  }
}

// Keyboard shortcuts & overflow body management
const handleKeyDown = (e) => {
  if (e.key === 'Escape') {
    showLightbox.value = false
  } else if (e.key === 'ArrowLeft') {
    navigateImage(-1)
  } else if (e.key === 'ArrowRight') {
    navigateImage(1)
  }
}

watch(showLightbox, (newVal) => {
  if (newVal) {
    window.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'
  } else {
    window.removeEventListener('keydown', handleKeyDown)
    document.body.style.overflow = ''
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeyDown)
  document.body.style.overflow = ''
})

const downloadUrl = computed(() => {
  if (!props.activeImage) return '#'
  // Extract date from URL path outputs/2026-07-06/001.png
  const parts = props.activeImage.url.split('/')
  if (parts.length >= 3) {
    const dateStr = parts[parts.length - 2]
    const filename = parts[parts.length - 1]
    return `/api/image/download/${dateStr}/${filename}`
  }
  return '#'
})

const selectImage = (img) => {
  emit('select-image', img)
}

const useAsTemplate = () => {
  if (props.activeImage) {
    emit('apply-template', props.activeImage)
  }
}

const openImageFolder = async () => {
  if (!props.activeImage) return
  
  // Extract date and filename from URL (e.g. /api/image/view/2026-07-07/001.png)
  const parts = props.activeImage.url.split('/')
  if (parts.length >= 3) {
    const dateStr = parts[parts.length - 2]
    const filename = parts[parts.length - 1]
    const workflowName = props.activeImage.metadata?.workflow_name || 'anima'
    
    try {
      const response = await fetch('/api/image/open-folder', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          date_str: dateStr,
          filename: filename,
          workflow: workflowName
        })
      })
      if (!response.ok) {
        const data = await response.json()
        alert('無法開啟資料夾: ' + (data.detail || '未知錯誤'))
      }
    } catch (err) {
      alert('連線伺服器失敗: ' + err.message)
    }
  }
}

// Copy & Expand States
const copiedPositive = ref(false)
const copiedOriginal = ref(false)
const isExpandedPositive = ref(false)
const isExpandedOriginal = ref(false)

const isLongPrompt = (text) => {
  return text && text.length > 120
}

const copyText = (text, type) => {
  if (!text) return
  navigator.clipboard.writeText(text).then(() => {
    if (type === 'positive') {
      copiedPositive.value = true
      setTimeout(() => { copiedPositive.value = false }, 2000)
    } else if (type === 'original') {
      copiedOriginal.value = true
      setTimeout(() => { copiedOriginal.value = false }, 2000)
    }
  }).catch(err => {
    console.error('Failed to copy: ', err)
  })
}

const deleteCurrentImage = () => {
  if (props.activeImage) {
    if (confirm('確定要永久刪除此張圖片以及對應的參數記錄檔 (.json / .txt) 嗎？此動作無法復原。')) {
      emit('delete-image', props.activeImage)
    }
  }
}

watch(() => props.activeImage, () => {
  isExpandedPositive.value = false
  isExpandedOriginal.value = false
})
</script>

<style scoped>
.image-preview-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding-right: 4px;
}

.active-image-card {
  width: 100%;
  height: 480px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.active-image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  cursor: zoom-in;
}

.main-image:hover {
  transform: scale(1.015);
  filter: brightness(1.05);
}

.image-overlay-actions {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
  z-index: 5;
}

.btn-action-round {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
  text-decoration: none;
}

.btn-action-round:hover {
  background: #6c5ce7;
  border-color: #6c5ce7;
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(108, 92, 231, 0.4);
}

.generating-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: white;
  text-align: center;
}

.glow-ring {
  position: relative;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(108, 92, 231, 0.05);
  box-shadow: 0 0 20px rgba(108, 92, 231, 0.2);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.05);
  border-top-color: #6c5ce7;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.pulse-text {
  font-size: 0.95rem;
  font-weight: 500;
  animation: pulse 1.5s infinite;
}

.sub-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.45);
}

.empty-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.35);
  padding: 32px;
  text-align: center;
}

.empty-placeholder h3 {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.1rem;
}

.empty-placeholder p {
  font-size: 0.85rem;
  max-width: 260px;
}

.history-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h4 {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.count-tag {
  font-size: 0.7rem;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.7);
  padding: 2px 6px;
  border-radius: 10px;
}

.history-track {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.thumb-card {
  width: 72px;
  height: 96px;
  flex-shrink: 0;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  position: relative;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.01);
  transition: all 0.2s ease;
}

.thumb-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.3);
}

.thumb-card.active {
  border-color: #6c5ce7;
  box-shadow: 0 0 10px rgba(108, 92, 231, 0.5);
  transform: scale(1.02);
}

.thumb-badge {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 4px;
}

.metadata-card {
  background: rgba(255, 255, 255, 0.01);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 14px;
}

.metadata-header h4 {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  margin-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 6px;
}

.metadata-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.span-2 {
  grid-column: span 2;
}

.meta-label {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.4);
}

.meta-val {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.85);
  word-break: break-all;
}

.meta-header-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.meta-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.meta-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  color: rgba(255, 255, 255, 0.6);
  padding: 2px 6px;
  font-size: 0.65rem;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.meta-action-btn:hover {
  background: rgba(108, 92, 231, 0.15);
  border-color: rgba(108, 92, 231, 0.35);
  color: #a29bfe;
}

.meta-action-btn:active {
  transform: scale(0.95);
}

.action-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.action-text {
  font-size: 0.65rem;
}

.action-text.success {
  color: #2ec4b6;
  font-weight: 600;
}

.prompt-container {
  width: 100%;
}

.meta-val.code {
  display: block;
  width: 100%;
  box-sizing: border-box;
  font-family: monospace;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  padding: 4px 6px;
  border-radius: 4px;
  max-height: 80px;
  overflow-y: auto;
  white-space: pre-wrap;
  transition: max-height 0.25s ease;
}

.meta-val.code.final {
  max-height: 100px;
}

.prompt-container.expanded .meta-val.code {
  max-height: 400px;
}

.meta-val.idea {
  color: #a29bfe;
  font-weight: 500;
}

.meta-val.robot {
  color: #2ec4b6;
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
/* Lightbox Styles */
.lightbox-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(10, 11, 21, 0.9);
  backdrop-filter: blur(16px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Lightbox Navigation Buttons */
.lightbox-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
  z-index: 10002;
  backdrop-filter: blur(8px);
}

.lightbox-nav-btn:hover {
  background: #6c5ce7;
  border-color: #6c5ce7;
  color: white;
  transform: translateY(-50%) scale(1.1);
  box-shadow: 0 0 20px rgba(108, 92, 231, 0.5);
}

.lightbox-nav-btn:active {
  transform: translateY(-50%) scale(0.95);
}

.prev-btn {
  left: 24px;
}

.next-btn {
  right: 24px;
}

@media (max-width: 768px) {
  .lightbox-nav-btn {
    width: 44px;
    height: 44px;
  }
  .prev-btn {
    left: 12px;
  }
  .next-btn {
    right: 12px;
  }
}

.lightbox-close-btn {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 10001;
}

.lightbox-close-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  transform: scale(1.05);
}

.lightbox-content {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  box-sizing: border-box;
}

.lightbox-image-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 20px 0;
}

.lightbox-image {
  max-width: 90vw;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1), max-width 0.3s ease, max-height 0.3s ease;
}

.lightbox-image.zoom-in {
  cursor: zoom-in;
}

.lightbox-image.zoom-out {
  cursor: zoom-out;
}

.lightbox-image-wrapper.zoomed {
  align-items: flex-start;
}

.lightbox-image-wrapper.zoomed .lightbox-image {
  max-width: none;
  max-height: none;
  width: auto;
  height: auto;
}

.lightbox-actions-panel {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 30px;
  backdrop-filter: blur(8px);
  z-index: 10001;
}

.lightbox-info {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  font-family: monospace;
}

.btn-lightbox-action {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: #6c5ce7;
  border-radius: 20px;
  color: white;
  font-size: 0.85rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
}

.btn-lightbox-action:hover {
  background: #5b4cc4;
  box-shadow: 0 0 12px rgba(108, 92, 231, 0.4);
  transform: translateY(-1px);
}

/* Transitions */
.lightbox-fade-enter-active,
.lightbox-fade-leave-active {
  transition: opacity 0.3s ease;
}

.lightbox-fade-enter-from,
.lightbox-fade-leave-to {
  opacity: 0;
}

.lightbox-fade-enter-active .lightbox-image {
  animation: lightbox-scale-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes lightbox-scale-in {
  from { transform: scale(0.9); }
  to { transform: scale(1); }
}

/* Under-image Action Toolbar styles */
.image-toolbar-under {
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 8px 16px;
  margin-top: 4px;
  backdrop-filter: blur(10px);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
  text-decoration: none;
  user-select: none;
}

.toolbar-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
  transform: translateY(-1px);
}

.toolbar-btn:active {
  transform: translateY(0);
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.08);
}

.spinner-percent {
  position: absolute;
  font-size: 0.75rem;
  font-weight: 700;
  color: #a29bfe;
  z-index: 10;
}

.progress-bar-container {
  width: 240px;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
  margin-top: 4px;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 3px;
  transition: width 0.3s ease-out;
}

.toolbar-btn.delete-btn:hover {
  background: rgba(231, 76, 60, 0.15);
  color: #ff7675;
}
</style>
