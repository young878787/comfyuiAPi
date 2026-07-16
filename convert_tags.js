// Convert zh_TW.yaml to JSON for frontend use
const fs = require('fs');
const path = require('path');

function parseYaml(content) {
  const lines = content.split('\n');
  const result = [];
  let currentCategory = null;
  let currentGroup = null;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].replace(/\r$/, '');
    
    if (line.trim() === '' || line.trim().startsWith('#')) continue;
    
    const topMatch = line.match(/^- name:\s*(.+)$/);
    if (topMatch) {
      currentCategory = { name: topMatch[1].trim(), groups: [] };
      result.push(currentCategory);
      currentGroup = null;
      continue;
    }
    
    if (line.match(/^\s+groups:\s*$/)) continue;
    
    const subMatch = line.match(/^\s+- name:\s*(.+)$/);
    if (subMatch && currentCategory) {
      currentGroup = { name: subMatch[1].trim(), color: '', tags: {} };
      currentCategory.groups.push(currentGroup);
      continue;
    }
    
    const colorMatch = line.match(/^\s+color:\s*(.+)$/);
    if (colorMatch && currentGroup) {
      currentGroup.color = colorMatch[1].trim();
      continue;
    }
    
    if (line.match(/^\s+tags:\s*$/)) continue;
    
    const tagMatch = line.match(/^\s{8}(.+?):\s*(.*)$/);
    if (tagMatch && currentGroup) {
      const en = tagMatch[1].trim();
      const zh = tagMatch[2].trim();
      if (en) currentGroup.tags[en] = zh || en;
      continue;
    }
  }
  
  return result;
}

const yamlPath = path.join(__dirname, 'sd-webui-prompt-all-in-one', 'group_tags', 'zh_TW.yaml');
const outputDir = path.join(__dirname, 'frontend', 'public', 'tags');
const outputPath = path.join(outputDir, 'zh_TW.json');

console.log('Reading YAML from:', yamlPath);
const yamlContent = fs.readFileSync(yamlPath, 'utf-8');

console.log('Parsing YAML...');
const data = parseYaml(yamlContent);

let totalCategories = data.length;
let totalGroups = 0;
let totalTags = 0;
data.forEach(cat => {
  totalGroups += cat.groups.length;
  cat.groups.forEach(g => { totalTags += Object.keys(g.tags).length; });
});

console.log(`Parsed: ${totalCategories} categories, ${totalGroups} sub-groups, ${totalTags} tags`);

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(data, null, 2), 'utf-8');
console.log('Written to:', outputPath);
console.log('File size:', (fs.statSync(outputPath).size / 1024).toFixed(1), 'KB');

data.forEach((cat, i) => {
  const tagCount = cat.groups.reduce((sum, g) => sum + Object.keys(g.tags).length, 0);
  console.log(`  ${i + 1}. ${cat.name} (${cat.groups.length} groups, ${tagCount} tags)`);
});
