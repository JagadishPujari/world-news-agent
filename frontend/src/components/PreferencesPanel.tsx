import { UserPreferences } from '../types'

interface PreferencesPanelProps {
  preferences: UserPreferences
  onUpdate: (prefs: Partial<UserPreferences>) => void
}

export const PreferencesPanel = ({
  preferences,
  onUpdate,
}: PreferencesPanelProps) => {
  return (
    <div
      style={{
        padding: '12px',
        border: '1px solid #ddd',
        borderRadius: '6px',
        backgroundColor: '#f9f9f9',
      }}
    >
      <h4 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>Preferences</h4>

      <div style={{ marginBottom: '8px' }}>
        <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>
          Summary Style
        </label>
        <select
          value={preferences.summary_style}
          onChange={(e) =>
            onUpdate({
              summary_style: e.target.value as any,
            })
          }
          style={{
            width: '100%',
            padding: '6px',
            fontSize: '12px',
            borderRadius: '4px',
            border: '1px solid #ccc',
          }}
        >
          <option value="simple">Simple</option>
          <option value="detailed">Detailed</option>
          <option value="bullets">Bullets</option>
        </select>
      </div>

      <div style={{ marginBottom: '8px' }}>
        <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>
          Complexity Level
        </label>
        <select
          value={preferences.complexity}
          onChange={(e) =>
            onUpdate({
              complexity: e.target.value as any,
            })
          }
          style={{
            width: '100%',
            padding: '6px',
            fontSize: '12px',
            borderRadius: '4px',
            border: '1px solid #ccc',
          }}
        >
          <option value="beginner">Beginner</option>
          <option value="intermediate">Intermediate</option>
          <option value="expert">Expert</option>
        </select>
      </div>

      <div>
        <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>
          Reading Frequency
        </label>
        <select
          value={preferences.reading_frequency}
          onChange={(e) =>
            onUpdate({
              reading_frequency: e.target.value as any,
            })
          }
          style={{
            width: '100%',
            padding: '6px',
            fontSize: '12px',
            borderRadius: '4px',
            border: '1px solid #ccc',
          }}
        >
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
    </div>
  )
}
