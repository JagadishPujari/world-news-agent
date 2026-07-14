import { useState, useRef, useEffect } from 'react'
import { ChatMessage } from '../types'
import { MessageBubble } from './MessageBubble'

interface ChatInterfaceProps {
  messages: ChatMessage[]
  onSendMessage: (message: string) => void
  loading: boolean
}

export const ChatInterface = ({
  messages,
  onSendMessage,
  loading,
}: ChatInterfaceProps) => {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = () => {
    if (input.trim() && !loading) {
      onSendMessage(input)
      setInput('')
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '600px',
        border: '1px solid #ddd',
        borderRadius: '8px',
        backgroundColor: '#fff',
      }}
    >
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '16px',
          backgroundColor: '#fafafa',
        }}
      >
        {messages.length === 0 && (
          <p style={{ textAlign: 'center', color: '#999' }}>
            No messages yet. Start by asking for news!
          </p>
        )}
        {messages.map((msg, idx) => (
          <MessageBubble key={idx} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div
        style={{
          padding: '12px',
          borderTop: '1px solid #ddd',
          display: 'flex',
          gap: '8px',
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask for news, simplify a topic, or generate a digest..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '10px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            fontSize: '14px',
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: loading ? '#999' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px',
          }}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
