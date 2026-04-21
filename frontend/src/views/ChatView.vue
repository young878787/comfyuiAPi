<template>
  <div class="chat-view">
    <!-- No session selected -->
    <div v-if="!currentSessionId" class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      <h3>開始對話</h3>
      <p>從左側選擇或建立新的對話</p>
    </div>

    <!-- Chat area -->
    <template v-else>
      <!-- Messages -->
      <div class="messages-area" ref="messagesArea">
        <div class="messages-inner">
          <MessageBubble
            v-for="msg in messages"
            :key="msg.id"
            :message="msg"
          />
          <!-- Typing indicator -->
          <div v-if="isLoading" class="message-row assistant fade-in">
            <div class="avatar"><span>AI</span></div>
            <div class="bubble-wrapper">
              <div class="bubble assistant typing">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="input-area">
        <!-- Image preview -->
        <div v-if="imagePreview" class="image-preview-bar">
          <img :src="imagePreview" alt="preview" class="preview-thumb" />
          <span class="preview-name">{{ imageFile?.name }}</span>
          <button class="btn-remove-image" @click="clearImage" title="移除圖片">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div class="input-row"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
          :class="{ 'is-dragging': isDragging }"
        >
          <!-- Attach image button -->
          <label class="btn-attach" title="附加圖片">
            <input type="file" accept="image/*" @change="handleFileSelect" class="hidden-input" />
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
          </label>

          <textarea
            ref="textareaRef"
            v-model="inputText"
            @keydown="handleKeydown"
            @input="autoResize"
            placeholder="輸入訊息... (Ctrl+Enter 發送，可拖曳圖片)"
            rows="1"
            :disabled="isLoading"
          ></textarea>

          <button
            class="btn-send"
            @click="sendMessage"
            :disabled="(!inputText.trim() && !imageFile) || isLoading"
            title="發送 (Ctrl+Enter)"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import axios from 'axios'
import { useSessionStore } from '@/stores/sessionStore'
import MessageBubble from '@/components/MessageBubble.vue'

const { currentSessionId } = useSessionStore()

const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesArea = ref(null)
const textareaRef = ref(null)

// Image attachment
const imageFile = ref(null)
const imagePreview = ref(null)
const isDragging = ref(false)

// Load chat history when session changes
watch(currentSessionId, async (newId) => {
  messages.value = []
  if (!newId) return
  try {
    const res = await axios.get(`/api/chat/history/${newId}`)
    messages.value = res.data.messages || []
    scrollToBottom()
  } catch (e) {
    console.error('Failed to load history:', e)
  }
}, { immediate: true })

const scrollToBottom = async () => {
  await nextTick()
  if (messagesArea.value) {
    messagesArea.value.scrollTop = messagesArea.value.scrollHeight
  }
}

const autoResize = () => {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}

const handleKeydown = (e) => {
  if (e.ctrlKey && e.key === 'Enter') {
    e.preventDefault()
    sendMessage()
  }
}

// Image handling
const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file && file.type.startsWith('image/')) setImage(file)
}

const handleDrop = (e) => {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) setImage(file)
}

const setImage = (file) => {
  imageFile.value = file
  imagePreview.value = URL.createObjectURL(file)
}

const clearImage = () => {
  if (imagePreview.value) {
    URL.revokeObjectURL(imagePreview.value)
  }
  imageFile.value = null
  imagePreview.value = null
}

const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if ((!text && !imageFile.value) || isLoading.value || !currentSessionId.value) return

  // Build user message for display
  const userMsg = {
    id: 'temp-' + Date.now(),
    role: 'user',
    content: text || '(已附加圖片)',
    timestamp: new Date().toISOString(),
    imagePreview: imagePreview.value || null,
  }
  messages.value.push(userMsg)

  const payload = {
    session_id: currentSessionId.value,
    message: text || '請分析這張圖片',
  }

  // If image attached, convert to base64
  if (imageFile.value) {
    try {
      payload.image_base64 = await fileToBase64(imageFile.value)
      payload.image_mime_type = imageFile.value.type || 'image/jpeg'
    } catch (err) {
      console.error('Failed to convert image:', err)
    }
  }

  inputText.value = ''
  clearImage()
  isLoading.value = true
  scrollToBottom()

  // Reset textarea height
  if (textareaRef.value) textareaRef.value.style.height = 'auto'

  try {
    const res = await axios.post('/api/chat/send', payload)
    messages.value.push({
      id: res.data.id,
      role: res.data.role,
      content: res.data.content,
      timestamp: res.data.timestamp,
    })
  } catch (err) {
    const detail = err.response?.data?.detail || '未知錯誤'
    messages.value.push({
      id: 'err-' + Date.now(),
      role: 'assistant',
      content: `發生錯誤: ${detail}`,
      timestamp: new Date().toISOString(),
    })
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-content);
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
.empty-icon {
  opacity: 0.3;
}
.empty-state h3 {
  font-size: 1.25rem;
  color: var(--text-secondary);
  font-weight: 600;
}
.empty-state p {
  font-size: 0.9rem;
}

/* Messages */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}
.messages-inner {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* Typing indicator */
.message-row {
  display: flex;
  gap: 12px;
  padding: 12px 24px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
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
  background: var(--accent-light);
  color: var(--accent);
}
.bubble-wrapper {
  max-width: 75%;
}
.bubble.typing {
  padding: 16px 20px;
  background: var(--ai-bubble);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  gap: 4px;
  align-items: center;
}

/* Input area */
.input-area {
  padding: 12px 24px 20px;
  background: var(--bg-white);
  border-top: 1px solid var(--border);
}

.image-preview-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-content);
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
}
.preview-thumb {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
}
.preview-name {
  flex: 1;
  font-size: 0.8rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.btn-remove-image {
  background: transparent;
  color: var(--text-muted);
  padding: 4px;
  border-radius: 4px;
}
.btn-remove-image:hover {
  color: var(--danger);
  background: #fef2f2;
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-content);
  border-radius: var(--radius-md);
  border: 2px solid transparent;
  transition: var(--transition);
}
.input-row:focus-within {
  border-color: var(--accent);
  background: var(--bg-white);
}
.input-row.is-dragging {
  border-color: var(--accent);
  background: var(--accent-light);
}

.hidden-input {
  display: none;
}

.btn-attach {
  cursor: pointer;
  color: var(--text-muted);
  padding: 6px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  transition: var(--transition);
  flex-shrink: 0;
}
.btn-attach:hover {
  color: var(--accent);
  background: var(--accent-light);
}

.input-row textarea {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  padding: 6px 0;
  font-size: 0.9375rem;
  line-height: 1.5;
  max-height: 150px;
  font-family: inherit;
}
.input-row textarea:focus {
  outline: none;
  box-shadow: none;
}

.btn-send {
  background: var(--accent);
  color: #fff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: var(--transition);
}
.btn-send:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.05);
}
.btn-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
