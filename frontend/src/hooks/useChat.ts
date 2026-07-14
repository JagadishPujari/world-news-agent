import { useState, useCallback } from 'react'
import { ChatMessage, UserPreferences } from '../types'
import { chat, generateDigest, simplifyContent } from '../services/api'

export const useChat = (sessionId: string) => {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [preferences, setPreferences] = useState<UserPreferences>({
    topics: [],
    summary_style: 'simple',
    complexity: 'beginner',
    reading_frequency: 'medium',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (message: string) => {
      if (!message.trim()) return

      setLoading(true)
      setError(null)

      try {
        const response = await chat(sessionId, message, preferences)

        setMessages((prev) => [
          ...prev,
          { role: 'user', content: message },
          {
            role: 'assistant',
            content: response.reply,
            news_items: response.news_items,
            workflow_used: response.workflow_used,
            trace_id: response.trace_id,
          },
        ])
      } catch (err: any) {
        setError(err.message || 'Failed to send message')
      } finally {
        setLoading(false)
      }
    },
    [sessionId, preferences]
  )

  const requestDigest = useCallback(
    async (topics?: string[], style?: string) => {
      setLoading(true)
      setError(null)

      try {
        const response = await generateDigest(sessionId, topics, style)
        setMessages((prev) => [
          ...prev,
          {
            role: 'user',
            content: `Generate digest for: ${(topics || preferences.topics).join(', ')}`,
          },
          {
            role: 'assistant',
            content: response.digest,
            trace_id: response.trace_id,
          },
        ])
      } catch (err: any) {
        setError(err.message || 'Failed to generate digest')
      } finally {
        setLoading(false)
      }
    },
    [sessionId, preferences]
  )

  const simplifyTopic = useCallback(
    async (content: string, url?: string, level?: string) => {
      setLoading(true)
      setError(null)

      try {
        const response = await simplifyContent(sessionId, content, url, level)
        setMessages((prev) => [
          ...prev,
          {
            role: 'user',
            content: url ? `Simplify: ${url}` : `Explain: ${content}`,
          },
          {
            role: 'assistant',
            content: response.simplified,
            trace_id: response.trace_id,
          },
        ])
      } catch (err: any) {
        setError(err.message || 'Failed to simplify')
      } finally {
        setLoading(false)
      }
    },
    [sessionId]
  )

  const updatePreferences = useCallback((newPrefs: Partial<UserPreferences>) => {
    setPreferences((prev) => ({ ...prev, ...newPrefs }))
  }, [])

  return {
    messages,
    preferences,
    loading,
    error,
    sendMessage,
    requestDigest,
    simplifyTopic,
    updatePreferences,
  }
}
