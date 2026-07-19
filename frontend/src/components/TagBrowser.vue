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
          :style="tagCardStyle(tag.color, tag.categoryName)"
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
            :style="tagCardStyle(tag.color, tag.categoryName)"
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
            :style="tagCardStyle(activeGroup.color, activeCategory.name)"
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
    const color = tag.color || activeGroup.value?.color || ''
    const categoryName = tag.categoryName || activeCategory.value?.name || ''
    selectedTags.value.push({
      en: tag.en,
      zh: tag.zh,
      color,
      categoryName
    })
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

function tagCardStyle(color, categoryName) {
  if (!color && categoryName) {
    const catMap = {
      '人物': 'rgba(224, 122, 95, 0.4)',      /* Terracotta */
      '服飾': 'rgba(230, 119, 140, 0.4)',     /* Warm Rose */
      '動作': 'rgba(220, 175, 106, 0.4)',     /* Warm Gold */
      '姿勢/動作': 'rgba(220, 175, 106, 0.4)',
      '場景': 'rgba(168, 119, 150, 0.4)',     /* Mauve */
      '物品': 'rgba(180, 160, 105, 0.4)',     /* Warm Sage-Gold */
      '環境': 'rgba(124, 153, 120, 0.4)',     /* Sage Green */
      '構圖': 'rgba(142, 160, 115, 0.4)',     /* Warm Sage */
      '視角': 'rgba(142, 160, 115, 0.4)',
      '漢服': 'rgba(188, 90, 80, 0.4)',       /* Hanfu Clay Red */
      '魔法系': 'rgba(150, 140, 190, 0.4)',    /* Soft Lavender */
      '反向提示詞': 'rgba(210, 110, 100, 0.4)'  /* Rust Red */
    }
    color = catMap[categoryName] || catMap[categoryName.trim()]
  }
  
  if (!color) {
    color = 'rgba(217, 119, 6, 0.4)'; /* Warm Amber */
  }

  let rgb = '217, 119, 6';
  const match = color.match(/rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
  if (match) {
    rgb = `${match[1]}, ${match[2]}, ${match[3]}`;
  }

  return {
    '--tag-rgb': rgb,
    '--tag-accent': `rgb(${rgb})`,
    '--tag-bg': `rgba(${rgb}, 0.08)`,
    '--tag-border': `rgba(${rgb}, 0.2)`,
    '--tag-bg-hover': `rgba(${rgb}, 0.15)`,
    '--tag-border-hover': `rgba(${rgb}, 0.45)`,
    '--tag-bg-selected': `rgb(${rgb})`,
    '--tag-border-selected': `rgb(${rgb})`,
    '--tag-text-selected': `var(--workspace-bg)`,
    '--tag-text-color': `var(--text-primary)`,
    '--tag-en-color': `var(--text-muted)`,
    '--tag-en-selected-color': `var(--text-muted)`
  }
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
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  background: var(--panel-bg);
  overflow: hidden;
  transition: var(--transition);
}

.tag-browser.collapsed {
  border-color: var(--panel-border);
  opacity: 0.95;
}

/* Header */
.browser-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  transition: var(--transition);
  background: var(--button-ghost-hover);
  border-bottom: 1px solid var(--panel-border);
}

.browser-header:hover {
  background: var(--panel-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toggle-arrow {
  transition: transform 0.25s ease;
  color: var(--text-muted);
}

.toggle-arrow.open {
  transform: rotate(90deg);
}

.header-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.tag-count {
  font-size: 0.65rem;
  color: var(--text-muted);
  padding: 2px 6px;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.selected-count {
  font-size: 0.68rem;
  color: var(--accent);
  font-weight: 600;
}

.btn-clear-selected {
  background: var(--danger-light);
  border: none;
  color: var(--danger);
  font-size: 0.65rem;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition);
}

.btn-clear-selected:hover {
  background: var(--danger);
  color: white;
}

/* Body */
.browser-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
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
  gap: 6px;
  padding: 8px;
  background: var(--accent-light);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-sm);
}

.selected-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  background: var(--tag-bg-selected);
  border: 1px solid var(--tag-border-selected);
  border-radius: var(--radius-sm);
  font-size: 0.7rem;
  color: var(--tag-text-selected);
  cursor: pointer;
  transition: var(--transition);
}

.selected-tag:hover {
  background: var(--danger) !important;
  border-color: var(--danger) !important;
  color: white !important;
}

.selected-tag .remove-icon {
  opacity: 0.7;
}

.selected-tag:hover .remove-icon {
  opacity: 1;
  color: white;
}

/* Search */
.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: var(--radius-sm);
  transition: var(--transition);
}

.search-bar:focus-within {
  border-color: var(--input-focus);
  box-shadow: 0 0 0 3px var(--input-focus-shadow);
}

.search-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  color: var(--input-text);
  font-size: 0.78rem;
  outline: none;
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-clear {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.7rem;
  padding: 2px;
}

.search-clear:hover {
  color: var(--text-primary);
}

.results-header {
  font-size: 0.68rem;
  color: var(--text-muted);
  padding: 0 2px;
}

/* Category Tabs */
.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 4px;
  padding: 2px 0;
}

.cat-tab {
  flex-shrink: 0;
  padding: 5px 12px;
  background: var(--button-ghost-hover);
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 0.72rem;
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
}

.cat-tab:hover {
  background: var(--panel-border);
  color: var(--text-primary);
}

.cat-tab.active {
  background: var(--accent-light);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

/* Subgroup Tabs */
.subgroup-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 4px;
  padding: 2px 0;
}

.sub-tab {
  flex-shrink: 0;
  padding: 3px 10px;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 0.68rem;
  cursor: pointer;
  transition: var(--transition);
  white-space: nowrap;
}

.sub-tab:hover {
  color: var(--text-primary);
  background: var(--button-ghost-hover);
}

.sub-tab.active {
  color: var(--accent-text);
  background: var(--accent);
  border-color: var(--accent);
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
  scrollbar-color: var(--scrollbar-thumb) transparent;
}

.tags-grid::-webkit-scrollbar {
  width: 4px;
}

.tags-grid::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 2px;
}

.tag-card {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 5px 10px;
  background: var(--tag-bg);
  border: 1px solid var(--tag-border);
  border-radius: 4px;
  cursor: pointer;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}

.tag-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--tag-accent);
  opacity: 0.7;
  transition: opacity 0.15s;
}

.tag-card:hover {
  background: var(--tag-bg-hover);
  border-color: var(--tag-border-hover);
  transform: translateY(-1px);
}

.tag-card:hover::before {
  opacity: 1;
}

.tag-card.selected {
  background: var(--tag-bg-selected);
  border-color: var(--tag-border-selected);
  box-shadow: 0 2px 8px rgba(var(--tag-rgb), 0.1);
}

.tag-card.selected::before {
  opacity: 1;
  background: var(--tag-accent);
}

.tag-card .tag-zh {
  font-size: 0.72rem;
  color: var(--tag-text-color);
  line-height: 1.2;
}

.tag-card .tag-en {
  font-size: 0.6rem;
  color: var(--tag-en-color);
  font-family: monospace;
  line-height: 1.2;
  margin-top: 1px;
}

.tag-card.selected .tag-zh {
  color: var(--tag-text-selected);
  font-weight: 600;
}

.tag-card.selected .tag-en {
  color: var(--tag-text-selected);
  opacity: 0.8;
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--text-muted);
  font-size: 0.78rem;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--panel-border);
  border-top-color: var(--accent);
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
  color: var(--danger);
  font-size: 0.75rem;
}

.btn-retry {
  background: var(--button-ghost-hover);
  border: 1px solid var(--panel-border);
  color: var(--text-primary);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.7rem;
  cursor: pointer;
  transition: var(--transition);
}

.btn-retry:hover {
  background: var(--panel-bg);
  border-color: var(--accent);
}
</style>
