<template>
  <div class="parameter-form">
    <div class="form-grid">
      <!-- Checkpoint Model -->
      <div class="form-group span-2">
        <label>模型 (Checkpoint)</label>
        <select
          v-model="localParams.checkpoint"
          class="glass-select full-width"
          @change="emitUpdate"
        >
          <option value="">使用工作流預設模型 (Default)</option>
          <option v-for="ckpt in checkpoints" :key="ckpt" :value="ckpt">
            {{ ckpt }}
          </option>
        </select>
      </div>

      <!-- Resolution (hidden in img2img mode) -->
      <div v-if="!hideResolution" class="form-group span-2">
        <label>解析度 (寬 x 高)</label>
        <div class="resolution-inputs">
          <input
            type="number"
            v-model.number="localParams.width"
            placeholder="寬度"
            class="glass-input"
            @change="emitUpdate"
          />
          <span class="x-divider">×</span>
          <input
            type="number"
            v-model.number="localParams.height"
            placeholder="高度"
            class="glass-input"
            @change="emitUpdate"
          />
        </div>
      </div>

      <!-- Steps & CFG -->
      <div class="form-group">
        <label>生成步數 (Steps)</label>
        <input
          type="number"
          v-model.number="localParams.steps"
          class="glass-input"
          min="1"
          max="100"
          @change="emitUpdate"
        />
      </div>

      <div class="form-group">
        <label>CFG Scale</label>
        <input
          type="number"
          step="0.1"
          v-model.number="localParams.cfg"
          class="glass-input"
          min="0.1"
          max="30"
          @change="emitUpdate"
        />
      </div>

      <!-- Sampler & Scheduler -->
      <div class="form-group">
        <label>採樣器 (Sampler)</label>
        <select
          v-model="localParams.sampler"
          class="glass-select"
          @change="emitUpdate"
        >
          <option v-for="s in samplers" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <div class="form-group">
        <label>調度器 (Scheduler)</label>
        <select
          v-model="localParams.scheduler"
          class="glass-select"
          @change="emitUpdate"
        >
          <option v-for="s in schedulers" :key="s" :value="s">{{ s }}</option>
        </select>
      </div>

      <!-- Seed -->
      <div class="form-group span-2">
        <label>隨機種子 (Seed)</label>
        <div class="seed-input-wrapper">
          <input
            type="number"
            v-model.number="localParams.seed"
            placeholder="留空隨機生成"
            class="glass-input"
            @change="emitUpdate"
          />
          <button @click="randomizeSeed" class="btn-seed" title="隨機生成種子">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="23 4 23 10 17 10"/>
              <polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Attempts -->
      <div class="form-group span-2">
        <label>批次生成數量 (1-5)</label>
        <div class="attempts-selector">
          <button
            v-for="n in 5"
            :key="n"
            @click="setAttempts(n)"
            :class="['btn-attempt', localParams.attempts === n ? 'active' : '']"
          >
            {{ n }} 張
          </button>
        </div>
      </div>

      <!-- Negative Prompt -->
      <div class="form-group span-2">
        <label>反向提示詞 (Negative Prompt)</label>
        <textarea
          v-model="localParams.negative_prompt"
          placeholder="worst quality, low quality..."
          class="glass-textarea"
          rows="3"
          @change="emitUpdate"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, onMounted, ref } from 'vue'

const props = defineProps({
  params: {
    type: Object,
    required: true
  },
  hideResolution: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:params'])

const localParams = reactive({ ...props.params })
const checkpoints = ref([])

// Fetch available checkpoints from backend ComfyUI proxy on load
onMounted(async () => {
  try {
    const res = await fetch('/api/comfyui/checkpoints')
    if (res.ok) {
      checkpoints.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to load ComfyUI checkpoints:', err)
  }
})

// Watch for external changes (like changing workflow which changes defaults)
watch(() => props.params, (newVal) => {
  Object.assign(localParams, newVal)
}, { deep: true })

const samplers = [
  'dpmpp_2m_sde',
  'dpmpp_2m_sde_gpu',
  'euler',
  'euler_ancestral',
  'heun',
  'dpm_2',
  'ddim',
  'uni_pc'
]

const schedulers = [
  'simple',
  'normal',
  'karras',
  'exponential',
  'sgm_uniform'
]

const randomizeSeed = () => {
  localParams.seed = Math.floor(Math.random() * 1000000000)
  emitUpdate()
}

const setAttempts = (n) => {
  localParams.attempts = n
  emitUpdate()
}

const emitUpdate = () => {
  emit('update:params', { ...localParams })
}
</script>

<style scoped>
.parameter-form {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.span-2 {
  grid-column: span 2;
}

label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.5);
}

.resolution-inputs {
  display: flex;
  align-items: center;
  gap: 6px;
}

.x-divider {
  color: rgba(255, 255, 255, 0.4);
  font-size: 1rem;
}

.glass-input, .glass-select, .glass-textarea {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: white;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  transition: all 0.2s ease;
}

.glass-input:focus, .glass-select:focus, .glass-textarea:focus {
  border-color: #6c5ce7;
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 10px rgba(108, 92, 231, 0.2);
  outline: none;
}

.glass-select {
  appearance: none;
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='rgba(255, 255, 255, 0.5)' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 14px;
  padding-right: 32px !important;
}

.glass-select option {
  background: #1e1e2e;
  color: white;
}

.seed-input-wrapper {
  position: relative;
  display: flex;
}

.seed-input-wrapper input {
  padding-right: 36px;
}

.btn-seed {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-seed:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.attempts-selector {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  padding: 3px;
}

.btn-attempt {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  padding: 6px 0;
  font-size: 0.8rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.btn-attempt:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.btn-attempt.active {
  background: #6c5ce7;
  color: white;
  box-shadow: 0 2px 8px rgba(108, 92, 231, 0.3);
}

.full-width {
  width: 100%;
}
</style>
