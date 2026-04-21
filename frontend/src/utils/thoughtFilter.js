/**
 * Remove <thought>...</thought> blocks from AI response text.
 * Supports multiline content inside thought tags.
 * Returns { filtered, thoughts } where filtered has thoughts removed
 * and thoughts is an array of extracted thought contents.
 */
export function filterThoughts(text) {
  if (!text) return { filtered: '', thoughts: [] }
  
  const thoughts = []
  const regex = /<thought>([\s\S]*?)<\/thought>/gi
  let match
  
  while ((match = regex.exec(text)) !== null) {
    thoughts.push(match[1].trim())
  }
  
  const filtered = text.replace(regex, '').trim()
  
  return { filtered, thoughts }
}
