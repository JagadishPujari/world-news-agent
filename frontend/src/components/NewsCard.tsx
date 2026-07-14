import { NewsItem } from '../types'

interface NewsCardProps {
  item: NewsItem
  onSimplify: (title: string) => void
}

export const NewsCard = ({ item, onSimplify }: NewsCardProps) => {
  return (
    <div
      style={{
        padding: '12px',
        border: '1px solid #ddd',
        borderRadius: '6px',
        marginBottom: '8px',
        backgroundColor: '#f9f9f9',
      }}
    >
      <h4 style={{ margin: '0 0 6px 0', fontSize: '14px', fontWeight: '600' }}>
        {item.title}
      </h4>
      <p
        style={{
          margin: '0 0 6px 0',
          fontSize: '12px',
          color: '#666',
          lineHeight: '1.4',
        }}
      >
        {item.description}
      </p>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '11px',
          color: '#999',
        }}
      >
        <span>
          {item.source} • {item.published_date}
        </span>
        <div style={{ display: 'flex', gap: '6px' }}>
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: '#007bff',
                textDecoration: 'none',
                fontSize: '11px',
              }}
            >
              Read
            </a>
          )}
          <button
            onClick={() => onSimplify(item.title)}
            style={{
              background: 'none',
              border: 'none',
              color: '#007bff',
              cursor: 'pointer',
              fontSize: '11px',
              padding: 0,
            }}
          >
            Simplify
          </button>
        </div>
      </div>
    </div>
  )
}
