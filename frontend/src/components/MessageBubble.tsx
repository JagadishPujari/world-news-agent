import { ChatMessage } from '../types'

interface MessageBubbleProps {
  message: ChatMessage
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '12px',
      }}
    >
      <div
        style={{
          maxWidth: '70%',
          padding: '10px 15px',
          borderRadius: '8px',
          backgroundColor: isUser ? '#007bff' : '#f0f0f0',
          color: isUser ? 'white' : 'black',
          wordWrap: 'break-word',
        }}
      >
        <p style={{ margin: 0, lineHeight: '1.5' }}>{message.content}</p>
        {message.trace_id && (
          <small style={{ opacity: 0.7, marginTop: '4px', display: 'block' }}>
            Trace: {message.trace_id.substring(0, 12)}...
          </small>
        )}
      </div>
    </div>
  )
}
