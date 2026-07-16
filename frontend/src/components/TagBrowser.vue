<template>
  <div class="tag-browser" :class="{ collapsed: isCollapsed }">
    <!-- Toggle Header -->
    <div class="browser-header" @click="isCollapsed = !isCollapsed">
      <div class="header-left">
        <svg :class="['toggle-arrow', isCollapsed ? '' : 'open']" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="9 18 15 12 9 6"/>
        </svg>
        <span class="header-title">🏷️ 提示詞標籤庫</span>
        <span class="tag-count" v-if="tagData.length">{{ totalTagCount }} 個標籤</span>
      </div>
      <div class="header-right" v-if="selectedTags.length" @click.stop>
        <span class="selected-count">已選 {{ selectedTags.length }}</span>
        <button class="btn-clear-selected" @click="clearAllSelected" title="清除所有已選">✕</button>
      </div>
    </div>

    <!-- Browser Body -->
    <div class="browser-body" v-show="!isCollapsed">
      <!-- Selected Tags Preview -->
      <div class="selected-preview" v-if="selectedTags.length">
        <div
          class="selected-tag"
          v-for="tag in selectedTags"
          :key="tag.en"
          @click="removeTag(tag)"
          :title="'移除 ' + tag.en"
        >
          <span class="tag-zh">{{ tag.zh }}</span>
          <svg class="remove-icon" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </div>
      </div>

      <!-- Search Bar -->
      <div class="search-bar">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜尋標籤（中文或英文）..."
          class="search-input"
        />
        <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">✕</button>
      </div>

      <!-- Search Results -->
      <div class="search-results" v-if="searchQuery.trim()">
        <div class="results-header">
          找到 {{ searchResults.length }} 個結果
        </div>
        <div class="tags-grid">
          <div
            v-for="tag in searchResults"
            :key="tag.en + tag.categoryName"
            :class="['tag-card', isSelected(tag) ? 'selected' : '']"
            @click="toggleTag(tag)"
            :title="tag.categoryName + ' > ' + tag.groupName"
          >
            <span class="tag-zh">{{ tag.zh }}</span>
            <span class="tag-en">{{ tag.en }}</span>
          </div>
        </div>
      </div>

      <!-- Category Navigation -->
      <template v-else>
        <!-- Primary Category Tabs -->
        <div class="category-tabs" ref="categoryTabsRef">
          <button
            v-for="(cat, idx) in tagData"
            :key="idx"
            :class="['cat-tab', activeCatIdx === idx ? 'active' : '']"
            @click="selectCategory(idx)"
          >{{ cat.name }}</button>
        </div>

        <!-- Sub-group Tabs -->
        <div class="subgroup-tabs" v-if="activeCategory">
          <button
            v-for="(group, gIdx) in activeCategory.groups"
            :key="gIdx"
            :class="['sub-tab', activeGroupIdx === gIdx ? 'active' : '']"
            @click="activeGroupIdx = gIdx"
          >{{ group.name }}</button>
        </div>

        <!-- Tags Grid -->
        <div class="tags-grid" v-if="activeGroup">
          <div
            v-for="tag in activeGroup.tags"
            :key="tag.en"
            :class="['tag-card', isSelected(tag) ? 'selected' : '']"
            :style="tagCardStyle(activeGroup.color)"
            @click="toggleTag(tag)"
          >
            <span class="tag-zh">{{ tag.zh }}</span>
            <span class="tag-en" v-if="tag.zh !== tag.en">{{ tag.en }}</span>
          </div>
        </div>
      </template>

      <!-- Loading State -->
      <div class="loading-state" v-if="loading">
        <div class="loading-spinner"></div>
        <span>載入標籤資料中...</span>
      </div>

      <!-- Error State -->
      <div class="error-state" v-if="error">
        <span>⚠️ {{ error }}</span>
        <button class="btn-retry" @click="loadData">重試</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { loadTagData, searchTags } from '@/utils/tagData.js'

const emit = defineEmits(['select-tag', 'deselect-tag'])

const tagData = ref([])
const loading = ref(false)
const error = ref('')
const isCollapsed = ref(false)
const searchQuery = ref('')
const activeCatIdx = ref(0)
const activeGroupIdx = ref(0)
const selectedTags = ref([])

const categoryTabsRef = ref(null)

// Computed
const activeCategory = computed(() => tagData.value[activeCatIdx.value] || null)
const activeGroup = computed(() => activeCategory.value?.groups?.[activeGroupIdx.value] || null)

const totalTagCount = computed(() => {
  let count = 0
  tagData.value.forEach(cat => {
    cat.groups.forEach(g => { count += g.tags.length })
  })
  return count
})

const searchResults = computed(() => {
  if (!searchQuery.value.trim()) return []
  return searchTags(tagData.value, searchQuery.value)
})

// Methods
function selectCategory(idx) {
  activeCatIdx.value = idx
  activeGroupIdx.value = 0
}

function isSelected(tag) {
  return selectedTags.value.some(t => t.en === tag.en)
}

function toggleTag(tag) {
  const idx = selectedTags.value.findIndex(t => t.en === tag.en)
  if (idx >= 0) {
    selectedTags.value.splice(idx, 1)
    emit('deselect-tag', tag)
  } else {
    selectedTags.value.push({ en: tag.en, zh: tag.zh })
    emit('select-tag', tag)
  }
}

function removeTag(tag) {
  const idx = selectedTags.value.findIndex(t => t.en === tag.en)
  if (idx >= 0) {
    selectedTags.value.splice(idx, 1)
    emit('deselect-tag', tag)
  }
}

function clearAllSelected() {
  const cleared = [...selectedTags.value]
  selectedTags.value = []
  cleared.forEach(t => emit('deselect-tag', t))
}


function tagCardStyle(color) {
  if (!color) return {}
  return { '--tag-accent': color }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    tagData.value = await loadTagData()
  } catch (e) {
    error.value = '無法載入標籤資料：' + e.message
    console.error('Failed to load tag data:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.tag-browser {
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(12px);
  overflow: hidden;
  transition: all 0.3s ease;
}

.tag-browser.collapsed {
  border-color: rgba(255, 255, 255, 0.05);
}

/* Header */
.browser-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.browser-header:hover {
  background: rgba(255, 255, 255, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-arrow {
  transition: transform 0.25s ease;
  color: rgba(255, 255, 255, 0.4);
}

.toggle-arrow.open {
  transform: rotate(90deg);
}

.header-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.3px;
}

.tag-count {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.3);
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.selected-count {
  font-size: 0.68rem;
  color: #a29bfe;
  font-weight: 600;
}

.btn-clear-selected {
  background: rgba(231, 76, 60, 0.2);
  border: none;
  color: #ff7675;
  font-size: 0.65rem;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-clear-selected:hover {
  background: rgba(231, 76, 60, 0.4);
}

/* Body */
.browser-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 12px 12px;
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Selected Preview */
.selected-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px;
  background: rgba(108, 92, 231, 0.06);
  border: 1px solid rgba(108, 92, 231, 0.15);
  border-radius: 8px;
}

.selected-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: rgba(108, 92, 231, 0.2);
  border: 1px solid rgba(108, 92, 231, 0.3);
  border-radius: 12px;
  font-size: 0.7rem;
  color: #ddd;
  cursor: pointer;
  transition: all 0.15s;
}

.selected-tag:hover {
  background: rgba(231, 76, 60, 0.2);
  border-color: rgba(231, 76, 60, 0.4);
}

.selected-tag .remove-icon {
  opacity: 0.5;
}

.selected-tag:hover .remove-icon {
  opacity: 1;
  color: #ff7675;
}

/* Search */
.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  transition: border-color 0.2s;
}

.search-bar:focus-within {
  border-color: rgba(108, 92, 231, 0.4);
  background: rgba(255, 255, 255, 0.06);
}

.search-icon {
  color: rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  color: white;
  font-size: 0.78rem;
  outline: none;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.25);
}

.search-clear {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  font-size: 0.7rem;
  padding: 2px;
}

.search-clear:hover {
  color: white;
}

.results-header {
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.35);
  padding: 0 2px;
}

/* Category Tabs */
.category-tabs {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding: 2px 0;
  scrollbar-width: none;
}

.category-tabs::-webkit-scrollbar {
  display: none;
}

.cat-tab {
  flex-shrink: 0;
  padding: 5px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.72rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.cat-tab:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
}

.cat-tab.active {
  background: rgba(108, 92, 231, 0.2);
  border-color: rgba(108, 92, 231, 0.4);
  color: #a29bfe;
  font-weight: 600;
}

/* Subgroup Tabs */
.subgroup-tabs {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  padding: 2px 0;
  scrollbar-width: none;
}

.subgroup-tabs::-webkit-scrollbar {
  display: none;
}

.sub-tab {
  flex-shrink: 0;
  padding: 3px 10px;
  background: none;
  border: 1px solid transparent;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.68rem;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.sub-tab:hover {
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.04);
}

.sub-tab.active {
  color: white;
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
  font-weight: 500;
}

/* Tags Grid */
.tags-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  max-height: 280px;
  overflow-y: auto;
  padding: 4px 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.tags-grid::-webkit-scrollbar {
  width: 4px;
}

.tags-grid::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.tag-card {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  overflow: hidden;
}

.tag-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--tag-accent, rgba(108, 92, 231, 0.4));
  opacity: 0;
  transition: opacity 0.15s;
}

.tag-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}

.tag-card:hover::before {
  opacity: 1;
}

.tag-card.selected {
  background: rgba(108, 92, 231, 0.15);
  border-color: rgba(108, 92, 231, 0.35);
  box-shadow: 0 0 8px rgba(108, 92, 231, 0.15);
}

.tag-card.selected::before {
  opacity: 1;
  background: #6c5ce7;
}

.tag-card .tag-zh {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.2;
}

.tag-card .tag-en {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.35);
  font-family: monospace;
  line-height: 1.2;
}

.tag-card.selected .tag-zh {
  color: #a29bfe;
  font-weight: 500;
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.78rem;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-top-color: #6c5ce7;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error */
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: #ff7675;
  font-size: 0.75rem;
}

.btn-retry {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.7rem;
  cursor: pointer;
}

.btn-retry:hover {
  background: rgba(255, 255, 255, 0.15);
}
</style>
