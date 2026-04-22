<template>
  <div class="draw-view">
    <!-- No session selected -->
    <div v-if="!currentSessionId" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
      </div>
      <h3>圖片生成</h3>
      <p>請先從左側選擇或建立對話</p>
    </div>

    <template v-else>
      <div class="draw-layout">
        <!-- Left: Parameters -->
        <div class="params-panel">
          <div class="panel-header">
            <h3>生成參數</h3>
          </div>
          <div class="panel-body">
            <div class="form-group">
              <label for="positivePrompt">正向提示詞</label>
              <textarea
                id="positivePrompt"
                v-model="form.positive_prompt"
                rows="4"
                placeholder="描述你想生成的圖片內容..."
              ></textarea>
            </div>

            <div class="form-group">
              <label for="negativePrompt">負向提示詞</label>
              <textarea
                id="negativePrompt"
                v-model="form.negative_prompt"
                rows="3"
                placeholder="不希望出現的元素..."
              ></textarea>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>寬度</label>
                <input type="number" v-model.number="form.width" min="256" max="2048" step="8" />
              </div>
              <div class="form-group">
                <label>高度</label>
                <input type="number" v-model.number="form.height" min="256" max="2048" step="8" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Steps</label>
                <input type="number" v-model.number="form.steps" min="1" max="100" />
              </div>
              <div class="form-group">
                <label>CFG</label>
                <input type="number" v-model.number="form.cfg" min="0.1" max="30" step="0.1" />
              </div>
            </div>

            <div class="form-group">
              <label>Seed (留空隨機)</label>
              <input type="number" v-model.number="form.seed" placeholder="隨機" />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Sampler</label>
                <select v-model="form.sampler">
                  <option value="dpmpp_2m_sde">dpmpp_2m_sde</option>
                  <option value="dpmpp_2m_sde_gpu">dpmpp_2m_sde_gpu</option>
                  <option value="euler">euler</option>
                  <option value="euler_ancestral">euler_ancestral</option>
                  <option value="dpmpp_2m">dpmpp_2m</option>
                  <option value="dpmpp_sde">dpmpp_sde</option>
                </select>
              </div>
              <div class="form-group">
                <label>Scheduler</label>
                <select v-model="form.scheduler">
                  <option value="simple">simple</option>
                  <option value="normal">normal</option>
                  <option value="karras">karras</option>
                  <option value="sgm_uniform">sgm_uniform</option>
                </select>
              </div>
            </div>

            <button
              class="btn-generate"
              @click="generateImage"
              :disabled="!form.positive_prompt.trim() || isGenerating"
            >
              <svg v-if="!isGenerating" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
              <span v-if="isGenerating" class="spinner"></span>
              {{ isGenerating ? '生成中...' : '生成圖片' }}
            </button>
          </div>
        </div>

        <!-- Right: Results -->
        <div class="result-panel">
          <div class="panel-header">
            <div class="header-left">
              <h3>生成結果</h3>
              <span v-if="generatedImages.length" class="image-count">
                {{ generatedImages.length }} 張圖片
              </span>
            </div>
            <a
              v-if="latestImage"
              :href="`/api/image/download/${currentSessionId}/${latestImage}`"
              class="btn-download-top"
              download
              title="下載圖片"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/>
              </svg>
              下載圖片
            </a>
          </div>
          <div class="panel-body result-body">
            <!-- Latest result -->
            <div v-if="latestImage" class="latest-result fade-in">
              <img
                :src="`/api/image/view/${currentSessionId}/${latestImage}`"
                alt="Generated"
                class="result-image"
                @click="openFullscreen(latestImage)"
              />
            </div>

            <!-- Gallery -->
            <div v-if="generatedImages.length > 1" class="gallery">
              <h4>歷史圖片</h4>
              <div class="gallery-grid">
                <div
                  v-for="img in generatedImages"
                  :key="img"
                  class="gallery-item"
                  @click="openFullscreen(img)"
                >
                  <img :src="`/api/image/view/${currentSessionId}/${img}`" alt="Generated" />
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div v-if="!latestImage && !isGenerating" class="result-empty">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <circle cx="8.5" cy="8.5" r="1.5"/>
                <polyline points="21 15 16 10 5 21"/>
              </svg>
              <p>填寫提示詞後點擊「生成圖片」</p>
            </div>

            <!-- Generating -->
            <div v-if="isGenerating" class="generating-state">
              <div class="spinner-large"></div>
              <p>圖片生成中，請稍候...</p>
            </div>

            <!-- Error -->
            <div v-if="errorMsg" class="error-msg fade-in">
              {{ errorMsg }}
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Fullscreen overlay -->
    <div v-if="fullscreenImage" class="fullscreen-overlay" @click="fullscreenImage = null">
      <img :src="`/api/image/view/${currentSessionId}/${fullscreenImage}`" alt="Fullscreen" />
      <button class="btn-close-fullscreen" @click.stop="fullscreenImage = null">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import axios from 'axios'
import { useSessionStore } from '@/stores/sessionStore'

const { currentSessionId, pendingPrompt } = useSessionStore()

const form = ref({
  positive_prompt: '',
  negative_prompt: 'EasyNegative, disconnected limbs, malformed limbs, Multiple people, (mutated hands and fingers:1.2), (extra arms:1.1), (poorly drawn face:1.1), malformed hands, grayscale, (poorly drawn hands:1.2), mutation, ugly, floating limbs, out of focus, normal quality, disfigured, lowres, blurry, worstquality, no_pupils',
  width: 608,
  height: 1328,
  steps: 12,
  cfg: 1.0,
  seed: null,
  sampler: 'dpmpp_2m_sde',
  scheduler: 'simple',
})

const isGenerating = ref(false)
const latestImage = ref(null)
const generatedImages = ref([])
const errorMsg = ref('')
const fullscreenImage = ref(null)
const backendConfig = ref(null)

onMounted(async () => {
  try {
    const res = await axios.get('/api/config')
    backendConfig.value = res.data
    form.value.steps = res.data.default_steps
    form.value.cfg = res.data.default_cfg
    form.value.sampler = res.data.default_sampler
    form.value.scheduler = res.data.default_scheduler
    form.value.width = res.data.default_width
    form.value.height = res.data.default_height
    if (res.data.default_negative_prompt) {
      form.value.negative_prompt = res.data.default_negative_prompt
    }
  } catch (err) {
    console.error('Failed to fetch backend config:', err)
  }
})

// Load existing images when session changes
watch(currentSessionId, async (newId) => {
  latestImage.value = null
  generatedImages.value = []
  errorMsg.value = ''
  if (!newId) return
  try {
    const res = await axios.get(`/api/image/list/${newId}`)
    generatedImages.value = res.data.images || []
    latestImage.value = res.data.latest_image || null
  } catch (e) {
    // Session might not have images yet, that's ok
  }
}, { immediate: true })

watch(pendingPrompt, (newVal) => {
  if (newVal && newVal.text) {
    form.value.positive_prompt = newVal.text
    if (newVal.autoSubmit) {
      setTimeout(() => {
        generateImage()
      }, 300)
    }
    pendingPrompt.value = null
  }
}, { immediate: true })

const generateImage = async () => {
  if (!form.value.positive_prompt.trim() || isGenerating.value || !currentSessionId.value) return

  isGenerating.value = true
  errorMsg.value = ''

  try {
    const payload = {
      session_id: currentSessionId.value,
      positive_prompt: form.value.positive_prompt,
      negative_prompt: form.value.negative_prompt,
      width: form.value.width,
      height: form.value.height,
      steps: form.value.steps,
      cfg: form.value.cfg,
      sampler: form.value.sampler,
      scheduler: form.value.scheduler,
    }
    if (form.value.seed != null && !Number.isNaN(form.value.seed)) {
      payload.seed = form.value.seed
    }

    const res = await axios.post('/api/image/generate', payload)
    const filename = res.data.filename
    latestImage.value = filename
    if (!generatedImages.value.includes(filename)) {
      generatedImages.value.push(filename)
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '圖片生成失敗，請檢查 ComfyUI 是否運行中。'
  } finally {
    isGenerating.value = false
  }
}

const openFullscreen = (img) => {
  fullscreenImage.value = img
}
</script>

<style scoped>
.draw-view {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  gap: 12px;
}
.empty-icon { opacity: 0.3; }
.empty-state h3 {
  font-size: 1.25rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.draw-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 1px;
  background: var(--border);
}

.params-panel {
  width: 380px;
  min-width: 320px;
  background: var(--bg-white);
  display: flex;
  flex-direction: column;
}

.result-panel {
  flex: 1;
  background: var(--bg-white);
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-left h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-dark);
  margin: 0;
}
.image-count {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--bg-content);
  padding: 2px 10px;
  border-radius: 20px;
}
.btn-download-top {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--accent);
  color: #fff;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}
.btn-download-top:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.form-group textarea,
.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  color: var(--text-dark);
  background: var(--bg-white);
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.form-group textarea:focus,
.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--accent);
}
.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.btn-generate {
  width: 100%;
  padding: 12px;
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}
.btn-generate:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Results */
.result-body {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.latest-result {
  width: 100%;
  max-width: 600px;
}
.result-image {
  width: 100%;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: transform 0.2s;
}
.result-image:hover {
  transform: scale(1.01);
}



.result-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 60px 20px;
}
.result-empty svg { opacity: 0.3; margin-bottom: 12px; }

.generating-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.gallery {
  width: 100%;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}
.gallery h4 {
  font-size: 0.9rem;
  color: var(--text-secondary);
  margin-bottom: 12px;
}
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}
.gallery-item {
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  aspect-ratio: 1;
}
.gallery-item:hover {
  transform: scale(1.03);
  box-shadow: var(--shadow-md);
}
.gallery-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Spinner */
.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.spinner-large {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Fade in */
.fade-in {
  animation: fadeIn 0.3s ease-in;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Error */
.error-msg {
  background: #fef2f2;
  color: var(--danger);
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid #fecaca;
  font-size: 0.875rem;
  margin-top: 16px;
  width: 100%;
}

/* Fullscreen */
.fullscreen-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  cursor: pointer;
}
.fullscreen-overlay img {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
  border-radius: var(--radius-md);
}
.btn-close-fullscreen {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255,255,255,0.1);
  color: #fff;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.btn-close-fullscreen:hover {
  background: rgba(255,255,255,0.2);
}
</style>
