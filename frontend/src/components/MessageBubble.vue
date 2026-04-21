<template>
  <div :class="['message-row', message.role]" class="fade-in">
    <!-- Avatar -->
    <div class="avatar">
      <span v-if="message.role === 'user'">You</span>
      <span v-else>AI</span>
    </div>

    <div class="bubble-wrapper">
      <!-- Image preview if attached -->
      <div v-if="message.imagePreview" class="attached-image">
        <img :src="message.imagePreview" alt="attached" />
      </div>

      <!-- Thought process (collapsible) -->
      <details v-if="thoughts.length > 0" class="thought-block">
        <summary>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
          </svg>
          AI 思考過程
        </summary>
        <div class="thought-content" v-for="(t, i) in thoughts" :key="i">{{ t }}</div>
      </details>

      <!-- Message content -->
      <div
        :class="['bubble', message.role]"
      >
        <div v-if="message.role === 'assistant'" class="markdown-body" v-html="renderedContent"></div>
        <div v-else class="plain-text">{{ message.content }}</div>
      </div>

      <!-- Timestamp -->
      <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { filterThoughts } from '@/utils/thoughtFilter'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

// Configure marked (v12+ API)
marked.use({ breaks: true, gfm: true })

const thoughts = computed(() => {
  if (props.message.role !== 'assistant') return []
  const { thoughts } = filterThoughts(props.message.content)
  return thoughts
})

const renderedContent = computed(() => {
  if (props.message.role !== 'assistant') return props.message.content
  const { filtered } = filterThoughts(props.message.content)
  return DOMPurify.sanitize(marked.parse(filtered))
})

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.message-row {
  display: flex;
  gap: 12px;
  padding: 12px 24px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 700;
  flex-shrink: 0;
  text-transform: uppercase;
}
.message-row.user .avatar {
  background: var(--user-bubble);
  color: var(--user-text);
}
.message-row.assistant .avatar {
  background: var(--accent-light);
  color: var(--accent);
}

.bubble-wrapper {
  max-width: 75%;
  min-width: 60px;
  display: flex;
  flex-direction: column;
}
.message-row.user .bubble-wrapper {
  align-items: flex-end;
}

.bubble {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  word-break: break-word;
}
.bubble.user {
  background: var(--user-bubble);
  color: var(--user-text);
  border-bottom-right-radius: 4px;
}
.bubble.assistant {
  background: var(--ai-bubble);
  color: var(--ai-text);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--border);
}

.plain-text {
  white-space: pre-wrap;
  font-size: 0.9375rem;
  line-height: 1.6;
}

.timestamp {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 4px;
  padding: 0 4px;
}

.attached-image {
  margin-bottom: 8px;
  border-radius: var(--radius-md);
  overflow: hidden;
  max-width: 300px;
  box-shadow: var(--shadow-sm);
}
.attached-image img {
  width: 100%;
  display: block;
}

.thought-block {
  margin-bottom: 8px;
  background: #f8f4ff;
  border: 1px solid #e4d9f7;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  overflow: hidden;
}
.thought-block summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  cursor: pointer;
  color: var(--accent);
  font-weight: 500;
  user-select: none;
}
.thought-block summary:hover {
  background: #f0eaff;
}
.thought-content {
  padding: 8px 12px;
  color: var(--text-secondary);
  border-top: 1px solid #e4d9f7;
  white-space: pre-wrap;
  line-height: 1.5;
}
</style>
