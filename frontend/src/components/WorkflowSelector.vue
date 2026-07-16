<template>
  <div class="workflow-selector-container">
    <label for="workflow-select">工作流模組 (Workflow)</label>
    <div class="selector-wrapper">
      <select
        id="workflow-select"
        v-model="selected"
        @change="emitChange"
        class="glass-select"
      >
        <option
          v-for="wf in workflows"
          :key="wf.name"
          :value="wf.name"
        >
          {{ wf.display_name }} ({{ wf.file }})
        </option>
      </select>
      <div class="arrow-down">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  workflows: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: String,
    default: 'anima'
  }
})

const emit = defineEmits(['update:modelValue', 'change'])
const selected = ref(props.modelValue)

watch(() => props.modelValue, (newVal) => {
  selected.value = newVal
})

const emitChange = () => {
  emit('update:modelValue', selected.value)
  emit('change', selected.value)
}
</script>

<style scoped>
.workflow-selector-container {
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

.glass-select option {
  background: var(--panel-bg);
  color: var(--text-primary);
  padding: 10px;
}

.arrow-down {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: var(--text-muted);
  display: flex;
  align-items: center;
}
</style>
