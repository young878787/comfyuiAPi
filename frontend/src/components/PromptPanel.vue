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
        placeholder="輸入原始提示詞（英文 tag 或自然語言），Anima 繪師會自動結構化並優化…"
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
        placeholder="描述你的創作想法，例：『穿著和服的少女在櫻花樹下微笑，柔和的夕陽光線』"
        class="glass-textarea idea-area"
        rows="4"
        :disabled="generating"
      ></textarea>

      <!-- Tag Browser -->
      <TagBrowser
        @select-tag="handleSelectTag"
        @deselect-tag="handleDeselectTag"
      />
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

      <!-- Metadata Detected Banner -->
      <div v-if="showMetadataBanner && detectedMetadata" class="metadata-banner glass-card-micro">
        <div class="banner-header">
          <span class="banner-title">✨ 偵測到 AI 生成參數 ({{ detectedMetadata.format === 'comfyui' ? 'ComfyUI' : 'Stable Diffusion' }})</span>
          <span class="close-banner" @click="showMetadataBanner = false">✕</span>
        </div>
        <div class="metadata-details">
          <div class="metadata-prompt-preview" v-if="detectedMetadata.positivePrompt">
            <strong>正向提示詞：</strong>
            <p class="truncate-text">{{ detectedMetadata.positivePrompt }}</p>
          </div>
          <div class="metadata-params-row" v-if="hasParams(detectedMetadata.params)">
            <span v-if="detectedMetadata.params.steps">Steps: <strong>{{ detectedMetadata.params.steps }}</strong></span>
            <span v-if="detectedMetadata.params.cfg">CFG: <strong>{{ detectedMetadata.params.cfg }}</strong></span>
            <span v-if="detectedMetadata.params.sampler">Sampler: <strong>{{ detectedMetadata.params.sampler }}</strong></span>
            <span v-if="detectedMetadata.params.seed">Seed: <strong>{{ detectedMetadata.params.seed }}</strong></span>
            <span v-if="detectedMetadata.params.width && detectedMetadata.params.height">Size: <strong>{{ detectedMetadata.params.width }}x{{ detectedMetadata.params.height }}</strong></span>
          </div>
        </div>
        <div class="banner-actions">
          <button class="btn-meta-apply" @click.stop="applyMetadata('all')">全部套用</button>
          <button class="btn-meta-apply-prompt" @click.stop="applyMetadata('prompt')">僅提示詞</button>
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
import TagBrowser from './TagBrowser.vue'

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

const emit = defineEmits(['generate', 'analyze-image', 'apply-parsed-metadata'])

const prompt = ref('')
const idea = ref('')
const isDragging = ref(false)
const refImagePreview = ref(null)
const refImageFile = ref(null)
const fileInput = ref(null)
const analyzing = ref(false)

// Metadata state
const detectedMetadata = ref(null)
const showMetadataBanner = ref(false)

const clearPrompt = () => { prompt.value = '' }
const clearIdea = () => { idea.value = '' }

// Handle tag browser selections - append to idea
const handleSelectTag = (tag) => {
  const valueToAdd = tag.zh || tag.en
  if (!valueToAdd) return
  
  const current = idea.value.trim()
  if (current) {
    const tags = current.split(/,\s*/).map(t => t.trim())
    if (!tags.includes(valueToAdd)) {
      idea.value = current + ', ' + valueToAdd
    }
  } else {
    idea.value = valueToAdd
  }
}

const handleDeselectTag = (tag) => {
  const valueToRemove = tag.zh || tag.en
  if (!valueToRemove) return
  
  const current = idea.value.trim()
  if (!current) return
  
  const tags = current.split(/,\s*/).map(t => t.trim())
  const filtered = tags.filter(t => t !== valueToRemove)
  idea.value = filtered.join(', ')
}

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
  
  // 1. Read preview
  const reader = new FileReader()
  reader.onload = (e) => {
    refImagePreview.value = e.target.result
  }
  reader.readAsDataURL(file)
  
  // Reset previous metadata
  detectedMetadata.value = null
  showMetadataBanner.value = false

  // 2. Read ArrayBuffer for metadata parsing locally
  const arrayReader = new FileReader()
  arrayReader.onload = (e) => {
    try {
      const arrayBuffer = e.target.result
      const rawMetadata = parsePngMetadata(arrayBuffer)
      if (rawMetadata) {
        const parsed = extractImagePrompt(rawMetadata)
        if (parsed.format !== 'unknown' && (parsed.positivePrompt || parsed.negativePrompt)) {
          detectedMetadata.value = parsed
          showMetadataBanner.value = true
          return
        }
      }
    } catch (err) {
      console.error("Local PNG metadata parsing failed, trying backend fallback:", err)
    }
    
    // Fallback: Ask backend to parse metadata (e.g. if WebP or compressed)
    tryBackendParse(file)
  }
  arrayReader.readAsArrayBuffer(file)
}

const tryBackendParse = async (file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch('/api/image/parse-metadata', {
      method: 'POST',
      body: formData
    })
    if (response.ok) {
      const parsed = await response.json()
      if (parsed.format !== 'unknown' && (parsed.positive_prompt || parsed.negative_prompt)) {
        detectedMetadata.value = {
          format: parsed.format,
          positivePrompt: parsed.positive_prompt,
          negativePrompt: parsed.negative_prompt,
          params: {
            steps: parsed.parameters?.steps,
            cfg: parsed.parameters?.cfg,
            seed: parsed.parameters?.seed,
            sampler: parsed.parameters?.sampler,
            scheduler: parsed.parameters?.scheduler,
            width: parsed.parameters?.width,
            height: parsed.parameters?.height
          }
        }
        showMetadataBanner.value = true
      }
    }
  } catch (err) {
    console.error("Backend metadata parsing failed:", err)
  }
}

const applyMetadata = (type) => {
  if (!detectedMetadata.value) return
  
  if (type === 'all') {
    prompt.value = detectedMetadata.value.positivePrompt || ''
    emit('apply-parsed-metadata', detectedMetadata.value)
  } else if (type === 'prompt') {
    prompt.value = detectedMetadata.value.positivePrompt || ''
    emit('apply-parsed-metadata', {
      ...detectedMetadata.value,
      params: {
        negative_prompt: detectedMetadata.value.negativePrompt
      }
    })
  }
  showMetadataBanner.value = false
}

const hasParams = (params) => {
  if (!params) return false
  return params.steps || params.cfg || params.sampler || params.seed || (params.width && params.height)
}

const clearRefImage = () => {
  refImageFile.value = null
  refImagePreview.value = null
  detectedMetadata.value = null
  showMetadataBanner.value = false
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

// Local binary PNG metadata parser helper
const parsePngMetadata = (arrayBuffer) => {
  const view = new DataView(arrayBuffer)
  // Check PNG signature: 89 50 4E 47 0D 0A 1A 0A
  if (view.getUint32(0) !== 0x89504E47 || view.getUint32(4) !== 0x0D0A1A0A) {
    return null
  }
  
  const textChunks = {}
  let offset = 8
  const length = arrayBuffer.byteLength
  
  while (offset < length - 12) {
    const chunkLength = view.getUint32(offset)
    const chunkType = String.fromCharCode(
      view.getUint8(offset + 4),
      view.getUint8(offset + 5),
      view.getUint8(offset + 6),
      view.getUint8(offset + 7)
    )
    
    offset += 8
    
    if (chunkType === 'tEXt') {
      const chunkData = new Uint8Array(arrayBuffer, offset, chunkLength)
      let nullIndex = 0
      while (nullIndex < chunkLength && chunkData[nullIndex] !== 0) {
        nullIndex++
      }
      if (nullIndex < chunkLength) {
        const key = new TextDecoder('latin1').decode(chunkData.subarray(0, nullIndex))
        const val = new TextDecoder('latin1').decode(chunkData.subarray(nullIndex + 1))
        textChunks[key] = val
      }
    } else if (chunkType === 'iTXt') {
      const chunkData = new Uint8Array(arrayBuffer, offset, chunkLength)
      let nullIndex = 0
      while (nullIndex < chunkLength && chunkData[nullIndex] !== 0) {
        nullIndex++
      }
      if (nullIndex < chunkLength) {
        const key = new TextDecoder('utf-8').decode(chunkData.subarray(0, nullIndex))
        const compressionFlag = chunkData[nullIndex + 1]
        const compressionMethod = chunkData[nullIndex + 2]
        
        let langIndex = nullIndex + 3
        while (langIndex < chunkLength && chunkData[langIndex] !== 0) {
          langIndex++
        }
        
        let transKeyIndex = langIndex + 1
        while (transKeyIndex < chunkLength && chunkData[transKeyIndex] !== 0) {
          transKeyIndex++
        }
        
        let textBytes = chunkData.subarray(transKeyIndex + 1)
        if (compressionFlag === 0) {
          const val = new TextDecoder('utf-8').decode(textBytes)
          textChunks[key] = val
        }
      }
    }
    
    offset += chunkLength + 4
  }
  
  return textChunks
}

const extractImagePrompt = (metadata) => {
  const result = {
    format: 'unknown',
    positivePrompt: '',
    negativePrompt: '',
    params: {}
  }
  
  if (!metadata) return result
  
  // 1. ComfyUI Format
  if (metadata.prompt) {
    result.format = 'comfyui'
    try {
      const promptObj = JSON.parse(metadata.prompt)
      const positiveTexts = []
      const negativeTexts = []
      const samplerNodes = []
      const clipNodes = {}
      
      for (const [nodeId, node] of Object.entries(promptObj)) {
        const classType = node.class_type || ''
        if (['CLIPTextEncode', 'SDXLPromptEncoder', 'CLIPTextEncodeSDXL', 'CLIPTextEncodeSVD'].includes(classType)) {
          clipNodes[nodeId] = node
        } else if (classType.includes('Sampler') || classType === 'KSampler' || classType === 'KSamplerAdvanced') {
          samplerNodes.push(node)
        }
      }
      
      for (const sampler of samplerNodes) {
        const inputs = sampler.inputs || {}
        const posConn = inputs.positive
        const negConn = inputs.negative
        
        if (Array.isArray(posConn) && posConn.length > 0) {
          const posNodeId = String(posConn[0])
          if (clipNodes[posNodeId]) {
            const text = clipNodes[posNodeId].inputs?.text || ''
            if (text && !positiveTexts.includes(text)) {
              positiveTexts.push(text)
            }
          }
        }
        
        if (Array.isArray(negConn) && negConn.length > 0) {
          const negNodeId = String(negConn[0])
          if (clipNodes[negNodeId]) {
            const text = clipNodes[negNodeId].inputs?.text || ''
            if (text && !negativeTexts.includes(text)) {
              negativeTexts.push(text)
            }
          }
        }
      }
      
      if (positiveTexts.length === 0) {
        for (const node of Object.values(clipNodes)) {
          const text = node.inputs?.text || ''
          if (text) {
            const textLower = text.toLowerCase()
            if (textLower.includes('worst quality') || textLower.includes('low quality') || textLower.includes('bad anatomy')) {
              negativeTexts.push(text)
            } else {
              positiveTexts.push(text)
            }
          }
        }
      }
      
      result.positivePrompt = positiveTexts.join('\n')
      result.negativePrompt = negativeTexts.join('\n')
      
      if (samplerNodes.length > 0) {
        const sInputs = samplerNodes[0].inputs || {}
        result.params = {
          steps: sInputs.steps,
          cfg: sInputs.cfg,
          seed: sInputs.seed,
          sampler: sInputs.sampler_name,
          scheduler: sInputs.scheduler
        }
      }
    } catch (e) {
      console.error('Failed to parse ComfyUI prompt JSON:', e)
    }
  } 
  // 2. Stable Diffusion Format
  else if (metadata.parameters) {
    result.format = 'stable_diffusion'
    const paramsStr = metadata.parameters
    const lines = paramsStr.split('\n')
    
    const posLines = []
    const negLines = []
    let paramLine = ''
    
    let inNegative = false
    for (const line of lines) {
      const lineTrim = line.trim()
      if (lineTrim.startsWith('Negative prompt:')) {
        inNegative = true
        negLines.push(lineTrim.substring('Negative prompt:'.length).trim())
      } else if (lineTrim.match(/^(Steps:|Sampler:|CFG scale:|Seed:)/i)) {
        paramLine = lineTrim
        inNegative = false
      } else {
        if (inNegative) {
          negLines.push(lineTrim)
        } else {
          posLines.push(lineTrim)
        }
      }
    }
    
    result.positivePrompt = posLines.join('\n').trim()
    result.negativePrompt = negLines.join('\n').trim()
    
    if (paramLine) {
      const params = {}
      const pairs = paramLine.split(',')
      for (const pair of pairs) {
        const index = pair.indexOf(':')
        if (index !== -1) {
          const k = pair.substring(0, index).trim().toLowerCase()
          const v = pair.substring(index + 1).trim()
          params[k] = v
        }
      }
      
      result.params = {
        steps: params['steps'] ? parseInt(params['steps']) : undefined,
        cfg: params['cfg scale'] ? parseFloat(params['cfg scale']) : undefined,
        seed: params['seed'] ? parseInt(params['seed']) : undefined,
        sampler: params['sampler'],
      }
      
      if (params['size']) {
        const sizeMatch = params['size'].match(/^(\d+)x(\d+)$/)
        if (sizeMatch) {
          result.params.width = parseInt(sizeMatch[1])
          result.params.height = parseInt(sizeMatch[2])
        }
      }
    }
  }
  
  return result
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

/* Glassmorphism Metadata Banner styling */
.glass-card-micro {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  animation: slideDown 0.3s ease-out;
}

.banner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.banner-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #a29bfe;
}

.close-banner {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.close-banner:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.metadata-details {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.metadata-prompt-preview p {
  margin: 4px 0 0 0;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(0, 0, 0, 0.25);
  padding: 6px 10px;
  border-radius: 6px;
  font-family: monospace;
}

.truncate-text {
  max-height: 100px;
  overflow-y: auto;
  word-break: break-all;
  white-space: pre-wrap;
  font-size: 0.75rem;
  line-height: 1.4;
  scrollbar-width: thin;
}

.truncate-text::-webkit-scrollbar {
  width: 4px;
}

.truncate-text::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

.metadata-params-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 0.7rem;
  background: rgba(255, 255, 255, 0.02);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.metadata-params-row span {
  color: rgba(255, 255, 255, 0.5);
}

.metadata-params-row strong {
  color: #a29bfe;
  font-weight: 600;
}

.banner-actions {
  display: flex;
  gap: 8px;
}

.btn-meta-apply {
  flex: 1;
  background: linear-gradient(135deg, #6c5ce7, #8e2de2);
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(108, 92, 231, 0.3);
}

.btn-meta-apply:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}

.btn-meta-apply-prompt {
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-meta-apply-prompt:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}
</style>
