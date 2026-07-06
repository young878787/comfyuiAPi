<template>
  <div class="image-preview-container">
    <!-- Active Image Area -->
    <div class="active-image-card">
      <div v-if="activeImage" class="active-image-wrapper">
        <img :src="activeImage.url" alt="Generated Image" class="main-image" />
        
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
        </div>
        <p class="pulse-text">AI 正在精心繪製您的創作中...</p>
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
          <span class="meta-label">原始提示詞:</span>
          <span class="meta-val code">{{ activeImage.metadata.original_prompt }}</span>
        </div>
        <div class="meta-item span-2" v-if="activeImage.metadata.user_idea">
          <span class="meta-label">修改想法 (Idea):</span>
          <span class="meta-val idea">{{ activeImage.metadata.user_idea }}</span>
        </div>
        <div class="meta-item span-2">
          <span class="meta-label">最終提示詞 (Positive Prompt):</span>
          <span class="meta-val code final">{{ activeImage.metadata.positive_prompt }}</span>
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
  </div>
</template>

<script setup>
import { computed } from 'vue'

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
  }
})

const emit = defineEmits(['select-image', 'apply-template'])

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
  aspect-ratio: 3 / 4;
  max-height: 480px;
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
  transition: transform 0.3s ease;
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

.meta-val.code {
  font-family: monospace;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  padding: 4px 6px;
  border-radius: 4px;
}

.meta-val.code.final {
  max-height: 120px;
  overflow-y: auto;
  white-space: pre-wrap;
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
</style>
