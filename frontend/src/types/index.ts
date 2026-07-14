export interface NewsItem {
  title: string
  description: string
  source: string
  url: string
  published_date: string
  category: string
}

export interface UserPreferences {
  topics: string[]
  summary_style: 'simple' | 'detailed' | 'bullets'
  complexity: 'beginner' | 'intermediate' | 'expert'
  reading_frequency: 'low' | 'medium' | 'high'
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  news_items?: NewsItem[]
  workflow_used?: string
  trace_id?: string
}

export interface ChatResponse {
  session_id: string
  reply: string
  news_items: NewsItem[]
  workflow_used: string
  trace_id?: string
}

export interface DigestResponse {
  session_id: string
  digest: string
  articles_included: number
  topics: string[]
  trace_id?: string
}

export interface SimplifyResponse {
  session_id: string
  simplified: string
  source_url?: string
  trace_id?: string
}
