import { UserPreferences } from '../types'

interface DigestPanelProps {
  preferences: UserPreferences
  onGenerateDigest: (topics?: string[], style?: string) => void
  loading: boolean
}

export const DigestPanel = ({
  preferences,
  onGenerateDigest,
  loading,
}: DigestPanelProps) => {
  return (
    <div
      style={{
        padding: '12px',
        border: '1px solid #28a745',
        borderRadius: '6px',
        backgroundColor: '#f0fff4',
      }}
    >
      <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#28a745' }}>
        Daily Digest
      </h4>
      <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#666' }}>
        {preferences.topics.length > 0
          ? `Generate a digest for: ${preferences.topics.join(', ')}`
          : 'Add favorite topics first to generate a digest'}
      </p>
      <button
        onClick={() => onGenerateDigest(preferences.topics, preferences.summary_style)}
        disabled={loading || preferences.topics.length === 0}
        style={{
          width: '100%',
          padding: '8px',
          backgroundColor: loading || preferences.topics.length === 0 ? '#999' : '#28a745',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading || preferences.topics.length === 0 ? 'not-allowed' : 'pointer',
          fontSize: '13px',
          fontWeight: '600',
        }}
      >
        {loading ? 'Generating...' : 'Generate Digest'}
      </button>
    </div>
  )
}
