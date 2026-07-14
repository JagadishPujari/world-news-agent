import { UserPreferences } from '../types'

interface TopicSelectorProps {
  preferences: UserPreferences
  onUpdate: (topics: string[]) => void
}

const TOPICS = ['politics', 'sports', 'technology', 'finance', 'climate']

export const TopicSelector = ({
  preferences,
  onUpdate,
}: TopicSelectorProps) => {
  const handleToggle = (topic: string) => {
    const updated = preferences.topics.includes(topic)
      ? preferences.topics.filter((t) => t !== topic)
      : [...preferences.topics, topic]
    onUpdate(updated)
  }

  return (
    <div style={{ padding: '12px', border: '1px solid #ddd', borderRadius: '6px', backgroundColor: '#f9f9f9' }}>
      <h4 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>Favorite Topics</h4>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
        {TOPICS.map((topic) => (
          <label
            key={topic}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            <input
              type="checkbox"
              checked={preferences.topics.includes(topic)}
              onChange={() => handleToggle(topic)}
            />
            {topic.charAt(0).toUpperCase() + topic.slice(1)}
          </label>
        ))}
      </div>
    </div>
  )
}
