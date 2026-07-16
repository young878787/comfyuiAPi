/**
 * Lightweight YAML parser for sd-webui-prompt-all-in-one group_tags format.
 * Only handles the specific nested structure: categories → groups → tags
 */
export function parseGroupTagsYaml(content) {
  const lines = content.split('\n')
  const result = []
  let currentCategory = null
  let currentGroup = null

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].replace(/\r$/, '')

    // Skip comments and empty lines
    if (line.trim() === '' || line.trim().startsWith('#')) continue

    // Top-level category: "- name: xxx"
    const topMatch = line.match(/^- name:\s*(.+)$/)
    if (topMatch) {
      currentCategory = { name: topMatch[1].trim(), groups: [] }
      result.push(currentCategory)
      currentGroup = null
      continue
    }

    // Groups array marker
    if (line.match(/^\s+groups:\s*$/)) continue

    // Sub-group: "    - name: xxx"
    const subMatch = line.match(/^\s+- name:\s*(.+)$/)
    if (subMatch && currentCategory) {
      currentGroup = { name: subMatch[1].trim(), color: '', tags: [] }
      currentCategory.groups.push(currentGroup)
      continue
    }

    // Color: "      color: xxx"
    const colorMatch = line.match(/^\s+color:\s*(.+)$/)
    if (colorMatch && currentGroup) {
      currentGroup.color = colorMatch[1].trim()
      continue
    }

    // Tags marker
    if (line.match(/^\s+tags:\s*$/)) continue

    // Tag entry: "        english_tag: 中文翻譯"
    const tagMatch = line.match(/^\s{8}(.+?):\s*(.*)$/)
    if (tagMatch && currentGroup) {
      const en = tagMatch[1].trim()
      const zh = tagMatch[2].trim()
      if (en) {
        currentGroup.tags.push({ en, zh: zh || en })
      }
    }
  }

  return result
}

/**
 * Search tags across all categories
 * @param {Array} data - Parsed tag data
 * @param {string} query - Search query (matches both en and zh)
 * @returns {Array} - Flat array of matching { en, zh, categoryName, groupName, color }
 */
export function searchTags(data, query) {
  if (!query || !query.trim()) return []
  const q = query.toLowerCase().trim()
  const results = []

  for (const category of data) {
    for (const group of category.groups) {
      for (const tag of group.tags) {
        if (tag.en.toLowerCase().includes(q) || tag.zh.toLowerCase().includes(q)) {
          results.push({
            ...tag,
            categoryName: category.name,
            groupName: group.name,
            color: group.color
          })
        }
      }
    }
  }

  return results.slice(0, 100) // Limit results
}

/**
 * Load and parse the YAML tag file
 */
export async function loadTagData() {
  const response = await fetch('/tags/zh_TW.yaml')
  if (!response.ok) throw new Error(`Failed to load tag data: ${response.status}`)
  const yamlText = await response.text()
  return parseGroupTagsYaml(yamlText)
}
