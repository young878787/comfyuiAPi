<template>
  <div class="prompt-panel">
    <!-- Original Prompt -->
    <div class="input-group">
      <div class="input-header">
        <label for="original-prompt">📝 原始提示詞 (Prompt)</label>
        <span class="clear-btn" @click="clearPrompt" v-if="prompt">清除</span>
      </div>
      <textarea
        id="original-prompt"
        v-model="prompt"
        placeholder="在此輸入原始提示詞（英文），或者留空讓 AI 根據您的修改想法自由發揮..."
        class="glass-textarea prompt-area"
        rows="5"
        :disabled="generating"
      ></textarea>
    </div>

    <!-- Modification Idea -->
    <div class="input-group">
      <div class="input-header">
        <label for="modification-idea">💡 修改想法 (Idea)</label>
        <span class="clear-btn" @click="clearIdea" v-if="idea">清除</span>
      </div>
      <textarea
        id="modification-idea"
        v-model="idea"
        placeholder="例：『換成藍色水手服』或『在森林背景中，加入柔和微光』。AI 將會幫您優化並改寫提示詞..."
        class="glass-textarea idea-area"
        rows="4"
        :disabled="generating"
      ></textarea>
    </div>

    <!-- Reference Image (Optional) -->
    <div class="input-group">
      <label>📁 參考圖片（可選，分析用）</label>
      <div
        class="image-upload-zone"
        :class="{ 'has-image': refImagePreview, 'dragging': isDragging }"
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
          @change="handleFileSelect"
          :disabled="generating"
        />
        
        <div v-if="!refImagePreview" class="upload-placeholder">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
            <circle cx="8.5" cy="8.5" r="1.5"/>
            <polyline points="21 15 16 10 5 21"/>
          </svg>
          <p>拖曳圖片至此處，或點擊上傳</p>
        </div>
        
        <div v-else class="upload-preview">
          <img :src="refImagePreview" alt="Upload Preview" />
          <button @click.stop="clearRefImage" class="btn-clear-image" title="移除圖片">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
          <div class="analyze-overlay" v-if="analyzing">
            <div class="spinner"></div>
            <span>分析圖片中...</span>
          </div>
          <button
            v-if="!analyzing"
            @click.stop="analyzeImage"
            class="btn-analyze"
            title="利用 AI 分析此圖片並帶入描述"
          >
            🔍 AI 分析圖片
          </button>
        </div>
      </div>
    </div>

    <!-- Generate Control -->
    <div class="generate-control">
      <!-- Error message if any -->
      <div v-if="errorMessage" class="error-banner">
        <span>⚠️ {{ errorMessage }}</span>
      </div>

      <!-- Action Button -->
      <button
        @click="startGeneration"
        :disabled="generating || (!prompt.trim() && !idea.trim())"
        :class="['btn-generate', generating ? 'generating' : '']"
      >
        <span v-if="!generating" class="btn-content">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          開始生成
        </span>
        <span v-else class="btn-content">
          <div class="generating-spinner"></div>
          {{ progressMessage || '生圖中...' }}
        </span>
      </button>

      <!-- Active Progress Bar -->
      <div class="progress-container" v-if="generating">
        <div class="progress-header">
          <span class="progress-state">{{ progressMessage }}</span>
          <span class="progress-percent">{{ progressPercentage }}%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
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
  },
  errorMessage: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['generate', 'analyze-image'])

const prompt = ref('')
const idea = ref('')
const isDragging = ref(false)
const refImagePreview = ref(null)
const refImageFile = ref(null)
const fileInput = ref(null)
const analyzing = ref(false)

const clearPrompt = () => { prompt.value = '' }
const clearIdea = () => { idea.value = '' }

const triggerFileInput = () => {
  if (!props.generating) {
    fileInput.value.click()
  }
}

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  processFile(file)
}

const handleDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  processFile(file)
}

const processFile = (file) => {
  if (!file || !file.type.startsWith('image/')) return
  refImageFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    refImagePreview.value = e.target.result
  }
  reader.readAsDataURL(file)
}

const clearRefImage = () => {
  refImageFile.value = null
  refImagePreview.value = null
  if (fileInput.value) fileInput.value.value = ''
}

const analyzeImage = async () => {
  if (!refImageFile.value || analyzing.value) return
  analyzing.value = true
  emit('analyze-image', {
    file: refImageFile.value,
    onSuccess: (resultPrompt) => {
      analyzing.value = false
      prompt.value = resultPrompt
    },
    onError: (err) => {
      analyzing.value = false
      alert('分析失敗：' + err)
    }
  })
}

const startGeneration = () => {
  if (props.generating) return
  emit('generate', {
    prompt: prompt.value,
    idea: idea.value,
    image: refImagePreview.value
  })
}
</script>

<style scoped>
.prompt-panel {
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
  color: rgba(255, 255, 255, 0.5);
}

.clear-btn {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: color 0.2s;
}

.clear-btn:hover {
  color: #e74c3c;
}

.glass-textarea {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: white;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.5;
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
}

.glass-textarea:focus {
  border-color: #6c5ce7;
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 12px rgba(108, 92, 231, 0.2);
  outline: none;
}

.prompt-area {
  font-family: monospace;
}

.image-upload-zone {
  border: 1.5px dashed rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.2s ease;
}

.image-upload-zone:hover, .image-upload-zone.dragging {
  border-color: #6c5ce7;
  background: rgba(108, 92, 231, 0.05);
}

.hidden-file-input {
  display: none;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.8rem;
}

.upload-placeholder svg {
  opacity: 0.7;
}

.upload-preview {
  width: 100%;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.upload-preview img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.btn-clear-image {
  position: absolute;
  top: 6px;
  right: 6px;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  color: white;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.btn-clear-image:hover {
  background: rgba(231, 76, 60, 0.8);
}

.btn-analyze {
  position: absolute;
  bottom: 6px;
  background: rgba(108, 92, 231, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 0.75rem;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  backdrop-filter: blur(5px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.btn-analyze:hover {
  background: #6c5ce7;
}

.analyze-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: white;
  font-size: 0.8rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.generating-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.generate-control {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.error-banner {
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid rgba(231, 76, 60, 0.3);
  color: #ff7675;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.8rem;
}

.btn-generate {
  width: 100%;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  border: none;
  color: white;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
  cursor: pointer;
  transition: all 0.3s;
  overflow: hidden;
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-1.5px);
  box-shadow: 0 6px 20px rgba(108, 92, 231, 0.4);
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.btn-generate.generating {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  cursor: wait;
  box-shadow: none;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.progress-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 10px;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.progress-state {
  font-weight: 500;
}

.progress-percent {
  font-weight: 700;
  color: #a29bfe;
}

.progress-bar-bg {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #6c5ce7, #a29bfe);
  border-radius: 3px;
  transition: width 0.4s ease;
  box-shadow: 0 0 8px rgba(108, 92, 231, 0.5);
}
</style>
