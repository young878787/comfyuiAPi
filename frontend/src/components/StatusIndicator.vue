<template>
  <div class="status-indicator">
    <div :class="['dot', connected ? 'connected' : 'disconnected']"></div>
    <span class="status-text">{{ connected ? 'ComfyUI 連線成功' : 'ComfyUI 連線中斷' }}</span>
  </div>
</template>

<script setup>
defineProps({
  connected: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 6px 12px;
  border-radius: 4px;
  backdrop-filter: blur(10px);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.dot.connected {
  background-color: #2ec4b6;
  box-shadow: 0 0 10px #2ec4b6, 0 0 20px rgba(46, 196, 182, 0.4);
}

.dot.disconnected {
  background-color: #e74c3c;
  box-shadow: 0 0 10px #e74c3c, 0 0 20px rgba(231, 76, 60, 0.4);
}

.status-text {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
}
</style>
