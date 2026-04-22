import { ref } from 'vue'
import axios from 'axios'

const currentSessionId = ref(null)
const currentSession = ref(null)
const sessions = ref([])
const loading = ref(false)
const pendingPrompt = ref(null)

export function useSessionStore() {
  const fetchSessions = async () => {
    try {
      const res = await axios.get('/api/sessions')
      sessions.value = res.data
    } catch (e) {
      console.error('Failed to fetch sessions:', e)
    }
  }

  const createSession = async (title) => {
    try {
      const res = await axios.post('/api/sessions', { title: title || '新對話' })
      const session = res.data
      sessions.value.unshift(session)
      setCurrentSession(session)
      return session
    } catch (e) {
      console.error('Failed to create session:', e)
      return null
    }
  }

  const deleteSession = async (sessionId) => {
    try {
      await axios.delete(`/api/sessions/${sessionId}`)
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      if (currentSessionId.value === sessionId) {
        const next = sessions.value[0] || null
        setCurrentSession(next)
      }
    } catch (e) {
      console.error('Failed to delete session:', e)
    }
  }

  const updateSessionTitle = async (sessionId, title) => {
    try {
      const res = await axios.put(`/api/sessions/${sessionId}/title`, { title })
      const idx = sessions.value.findIndex(s => s.id === sessionId)
      if (idx !== -1) sessions.value[idx] = res.data
      if (currentSessionId.value === sessionId) currentSession.value = res.data
    } catch (e) {
      console.error('Failed to update title:', e)
    }
  }

  const setCurrentSession = (session) => {
    currentSessionId.value = session?.id || null
    currentSession.value = session || null
  }

  return {
    currentSessionId,
    currentSession,
    sessions,
    loading,
    pendingPrompt,
    fetchSessions,
    createSession,
    deleteSession,
    updateSessionTitle,
    setCurrentSession,
  }
}
