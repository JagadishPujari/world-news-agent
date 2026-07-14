import React, { useState, useEffect, useRef } from 'react'
import {
  MessageSquare,
  Newspaper,
  Link as LinkIcon,
  Send,
  Check,
  BookOpen,
  Sparkles,
  RefreshCw,
  User,
  Copy,
  Globe
} from 'lucide-react'
import { getHealth, chat, generateDigest, simplifyContent } from './services/api'
import { ChatMessage, NewsItem, UserPreferences } from './types'
import './styles/index.css'

function App() {
  // App loading state
  const [appLoading, setAppLoading] = useState<boolean>(true)

  // Session state
  const [sessionId] = useState<string>(() => 'sess_' + Math.random().toString(36).substring(2, 11))
  const [activeTab, setActiveTab] = useState<'chat' | 'digest' | 'ingest'>('chat')

  // User preferences state (FR-7, FR-11.7)
  const [preferences, setPreferences] = useState<UserPreferences>({
    topics: ['technology', 'climate'],
    summary_style: 'simple',
    complexity: 'beginner',
    reading_frequency: 'medium',
  })

  // Chat panel state
  const [input, setInput] = useState<string>('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Welcome! I am your AI-powered News Companion. Select your favorite topics in the sidebar, choose your reading style, and start asking me for news or explanations! You can also paste an article link for me to summarize."
    }
  ])
  const [chatLoading, setChatLoading] = useState<boolean>(false)
  const [newsItems, setNewsItems] = useState<NewsItem[]>([])

  // Digest panel state
  const [digestText, setDigestText] = useState<string>('')
  const [digestLoading, setDigestLoading] = useState<boolean>(false)

  // Ingestion pane state
  const [ingestUrl, setIngestUrl] = useState<string>('')
  const [ingestLoading, setIngestLoading] = useState<boolean>(false)
  const [ingestResult, setIngestResult] = useState<string>('')

  // UI States
  const [toast, setToast] = useState<{ message: string; visible: boolean }>({ message: '', visible: false })
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Fetch health configuration on load
  useEffect(() => {
    getHealth()
      .then(() => setAppLoading(false))
      .catch((err) => {
        console.warn('Failed to connect to health endpoint:', err)
        setAppLoading(false)
      })
  }, [])

  // Scroll to bottom of chat list
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatLoading])

  // Display a toast message
  const showToast = (message: string) => {
    setToast({ message, visible: true })
    setTimeout(() => setToast({ message: '', visible: false }), 3000)
  }

  // Handle preference toggles
  const handleTopicToggle = (topic: string) => {
    setPreferences((prev) => {
      const updatedTopics = prev.topics.includes(topic)
        ? prev.topics.filter((t) => t !== topic)
        : [...prev.topics, topic]
      const updated = { ...prev, topics: updatedTopics }
      showToast(`Updated topics list`)
      return updated
    })
  }

  const handleDropdownChange = (key: keyof UserPreferences, value: string) => {
    setPreferences((prev) => {
      const updated = { ...prev, [key]: value }
      showToast(`Updated ${key.replace('_', ' ')}`)
      return updated
    })
  }

  // API 1: Conversational Chat (Route 1 / Route 2 / Route 3)
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!input.trim() || chatLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setChatLoading(true)

    try {
      const data = await chat(sessionId, userMessage, preferences)
      
      // Update chat history
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply,
          news_items: data.news_items,
          workflow_used: data.workflow_used,
          trace_id: data.trace_id
        }
      ])

      // Update right side news cards if returned
      if (data.news_items && data.news_items.length > 0) {
        setNewsItems(data.news_items)
        showToast(`Discovered ${data.news_items.length} news items`)
      }
    } catch (error: any) {
      console.error(error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: "Sorry, I ran into an issue processing your request. Please check that the backend is running and try again."
        }
      ])
    } finally {
      setChatLoading(false)
    }
  }

  // API 2: Generate Daily Digest (Route 3)
  const handleGenerateDigest = async () => {
    setActiveTab('digest')
    setDigestLoading(true)
    setDigestText('')

    try {
      const data = await generateDigest(sessionId, preferences.topics, preferences.summary_style)
      setDigestText(data.digest)
      showToast(`Digest generated successfully`)
    } catch (error) {
      console.error(error)
      setDigestText("Failed to compile your news digest. Please check your network or try again.")
    } finally {
      setDigestLoading(false)
    }
  }

  // API 3: URL Ingestion & Simplification (Route 2)
  const handleIngestUrl = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!ingestUrl.trim() || ingestLoading) return

    setIngestLoading(true)
    setIngestResult('')

    try {
      const data = await simplifyContent(sessionId, '', ingestUrl.trim(), preferences.complexity)
      setIngestResult(data.simplified)
      showToast(`URL summarized successfully`)
    } catch (error) {
      console.error(error)
      setIngestResult("Failed to extract content and summarize the URL. Please verify the URL and try again.")
    } finally {
      setIngestLoading(false)
    }
  }

  // Quick Action: Simplify a news card article (FR-4 / Route 2)
  const handleSimplifyCard = async (article: NewsItem) => {
    setChatLoading(true)
    setMessages((prev) => [...prev, { role: 'user', content: `Simplify this article: ${article.title}` }])

    try {
      const useUrl = article.url.startsWith('http') && !article.url.includes('example.com') ? article.url : undefined
      const contentToSimplify = useUrl ? '' : `${article.title}\n\n${article.description}`

      const data = await simplifyContent(sessionId, contentToSimplify, useUrl, preferences.complexity)
      
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.simplified,
          trace_id: data.trace_id
        }
      ])
    } catch (error) {
      console.error(error)
      setMessages((prev) => [...prev, { role: 'assistant', content: "Failed to simplify this article." }])
    } finally {
      setChatLoading(false)
    }
  }

  // Quick Action: Explain topic in detail
  const handleExplainTopicDetail = async (article: NewsItem) => {
    setChatLoading(true)
    setMessages((prev) => [...prev, { role: 'user', content: `Explain in detail: ${article.title}` }])

    try {
      const contentToExplain = `${article.title}\n\n${article.description}`
      const data = await simplifyContent(sessionId, contentToExplain, undefined, 'expert')
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.simplified,
          trace_id: data.trace_id
        }
      ])
    } catch (error) {
      console.error(error)
      setMessages((prev) => [...prev, { role: 'assistant', content: "Failed to generate detailed explanation." }])
    } finally {
      setChatLoading(false)
    }
  }

  const handleCopyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    showToast('Copied to clipboard!')
  }

  // Loading Splash Screen
  if (appLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#090a0f',
        color: '#fff',
        fontFamily: 'system-ui'
      }}>
        <div className="spinner" style={{ width: 40, height: 40 }}></div>
        <p style={{ marginTop: 20, color: '#94a3b8', fontSize: 14 }}>Initializing News Companion...</p>
      </div>
    )
  }

  // Local guest user (authentication removed)
  const currentUser = { name: 'Jagadish Pujari', email: 'jagadish.pujari@niit.com', picture: null }

  return (
    <div className="app-container">
      {/* 1. LEFT SIDEBAR: Preferences & Options */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-glow">WN</div>
          <div>
            <h2 className="sidebar-title">News Companion</h2>
            <span style={{ fontSize: 10, color: 'var(--accent-teal)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
              AI News Assistant
            </span>
          </div>
        </div>

        <div className="sidebar-scrollable">
          {/* Favorite Categories Panel (FR-11.3) */}
          <div className="sidebar-section">
            <h3 className="section-title">Interests</h3>
            <div className="topics-grid">
              {[
                { id: 'politics', label: 'Politics', class: 'dot-politics' },
                { id: 'sports', label: 'Sports', class: 'dot-sports' },
                { id: 'technology', label: 'Technology', class: 'dot-technology' },
                { id: 'finance', label: 'Finance', class: 'dot-finance' },
                { id: 'climate', label: 'Climate', class: 'dot-climate' }
              ].map((topic) => (
                <div
                  key={topic.id}
                  className={`topic-item ${preferences.topics.includes(topic.id) ? 'active' : ''}`}
                  onClick={() => handleTopicToggle(topic.id)}
                >
                  <div className="topic-checkbox">
                    {preferences.topics.includes(topic.id) && <Check size={10} color="#fff" />}
                  </div>
                  <div className={`topic-dot ${topic.class}`}></div>
                  <span>{topic.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reading Preferences Settings Panel (FR-11.7) */}
          <div className="sidebar-section">
            <h3 className="section-title">Preferences</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Summary Style */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Summary Length</span>
                <div className="select-wrapper">
                  <select
                    className="select-control"
                    value={preferences.summary_style}
                    onChange={(e) => handleDropdownChange('summary_style', e.target.value)}
                  >
                    <option value="simple">Simple / ELI5</option>
                    <option value="detailed">Detailed Analysis</option>
                    <option value="bullets">Bullet Highlights</option>
                  </select>
                </div>
              </div>

              {/* Complexity level */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Explanation Depth</span>
                <div className="select-wrapper">
                  <select
                    className="select-control"
                    value={preferences.complexity}
                    onChange={(e) => handleDropdownChange('complexity', e.target.value)}
                  >
                    <option value="beginner">Beginner (Analogy)</option>
                    <option value="intermediate">Intermediate (Standard)</option>
                    <option value="expert">Expert (Deep Research)</option>
                  </select>
                </div>
              </div>

              {/* Frequency */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Reading Frequency</span>
                <div className="select-wrapper">
                  <select
                    className="select-control"
                    value={preferences.reading_frequency}
                    onChange={(e) => handleDropdownChange('reading_frequency', e.target.value)}
                  >
                    <option value="low">Low (Condensed)</option>
                    <option value="medium">Medium (Standard)</option>
                    <option value="high">High (Deep Digest)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Profile card in sidebar footer */}
        <div className="sidebar-footer">
          <div className="auth-card">
            <div className="user-avatar">
              <User size={16} />
            </div>
            <div className="user-info">
              <div className="user-name">{currentUser.name}</div>
              <div className="user-status">Active session</div>
            </div>
          </div>
        </div>
      </aside>

      {/* 2. MAIN WORKSPACE */}
      <main className="main-content">
        {/* Main Navbar */}
        <header className="main-header">
          <div className="header-tabs">
            <button
              className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              <MessageSquare size={16} />
              Assistant Chat
            </button>
            <button
              className={`tab-btn ${activeTab === 'digest' ? 'active' : ''}`}
              onClick={() => setActiveTab('digest')}
            >
              <Newspaper size={16} />
              Daily Digest
            </button>
            <button
              className={`tab-btn ${activeTab === 'ingest' ? 'active' : ''}`}
              onClick={() => setActiveTab('ingest')}
            >
              <LinkIcon size={16} />
              Summarize Link
            </button>
          </div>

          <div className="header-actions">
            {/* Direct button to compile digest (FR-11.6) */}
            <button className="btn-primary" onClick={handleGenerateDigest}>
              <Sparkles size={14} />
              Generate Digest
            </button>
          </div>
        </header>

        {/* Viewport switching */}
        <div className="pane-container">
          {/* TAB 1: Chat interface (FR-11.2) */}
          {activeTab === 'chat' && (
            <div className="chat-pane">
              <div className="messages-list">
                {messages.length === 0 ? (
                  <div className="welcome-container">
                    <h2 className="welcome-title">AI News Companion</h2>
                    <p className="welcome-desc">
                      Explore global news, simplify economics or science concepts, and read tailored daily newsletters.
                    </p>
                    <div className="welcome-cards">
                      <div className="welcome-card" onClick={() => { setInput("Show me technology news"); }}>
                        <div className="welcome-card-title">Fetch Tech News</div>
                        <div className="welcome-card-desc">Get the latest technology articles and headlines.</div>
                      </div>
                      <div className="welcome-card" onClick={() => { setInput("Explain quantum computing in simple terms"); }}>
                        <div className="welcome-card-title">Simplify Concepts</div>
                        <div className="welcome-card-desc">Explain dense subjects with ELI5 analogies.</div>
                      </div>
                    </div>
                  </div>
                ) : (
                  messages.map((msg, idx) => (
                    <div key={idx} className={`message-row ${msg.role}`}>
                      <div className="message-bubble">
                        {msg.content.split('\n').map((line, lIdx) => {
                          let cleanLine = line
                          const isBullet = cleanLine.startsWith('•') || cleanLine.startsWith('*') || cleanLine.match(/^\d+\./)
                          
                          // Format bold tags
                          const boldRegex = /\*\*(.*?)\*\*/g
                          const elements = []
                          let lastIndex = 0
                          let match
                          
                          while ((match = boldRegex.exec(cleanLine)) !== null) {
                            if (match.index > lastIndex) {
                              elements.push(cleanLine.substring(lastIndex, match.index))
                            }
                            elements.push(<strong key={match.index}>{match[1]}</strong>)
                            lastIndex = boldRegex.lastIndex
                          }
                          if (lastIndex < cleanLine.length) {
                            elements.push(cleanLine.substring(lastIndex))
                          }

                          return (
                            <p key={lIdx} style={{ margin: isBullet ? '0 0 6px 12px' : '0 0 10px 0' }}>
                              {elements.length > 0 ? elements : cleanLine}
                            </p>
                          )
                        })}
                        {msg.trace_id && (
                          <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--accent-teal)', opacity: 0.8, fontFamily: 'var(--font-mono)' }}>
                            Trace Ref: {msg.trace_id.substring(0, 12)}...
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
                
                {chatLoading && (
                  <div className="message-row assistant">
                    <div className="message-bubble" style={{ minWidth: 80 }}>
                      <div className="loading-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input panel */}
              <div className="chat-input-area">
                <form onSubmit={handleSendMessage} className="input-box">
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask for news ('tech news'), ask to simplify a topic, or paste a link..."
                    className="chat-input"
                    disabled={chatLoading}
                  />
                  <button type="submit" className="btn-send" disabled={!input.trim() || chatLoading}>
                    <Send size={16} />
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* TAB 2: Daily Digest panel (FR-5, FR-11.6) */}
          {activeTab === 'digest' && (
            <div className="digest-fullscreen">
              <div className="digest-paper">
                <div className="digest-paper-header">
                  <span className="digest-tag">Custom Newsletter</span>
                  <h1 className="digest-title">Your Daily News Digest</h1>
                  <div className="digest-date">Generated on {new Date().toLocaleDateString()}</div>
                </div>

                {digestLoading ? (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 0' }}>
                    <div className="spinner" style={{ width: 36, height: 36 }}></div>
                    <p style={{ marginTop: 20, color: 'var(--text-secondary)' }}>Compiling newsletter and summarizing articles...</p>
                  </div>
                ) : digestText ? (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginBottom: 20 }}>
                      <button className="card-btn" onClick={() => handleCopyToClipboard(digestText)}>
                        <Copy size={14} />
                        Copy text
                      </button>
                      <button className="card-btn primary" onClick={handleGenerateDigest}>
                        <RefreshCw size={14} />
                        Rebuild
                      </button>
                    </div>
                    
                    <div className="digest-body">
                      {digestText.split('\n').map((line, idx) => {
                        if (line.startsWith('###')) {
                          return <h3 key={idx}>{line.replace('###', '').trim()}</h3>
                        }
                        return <p key={idx}>{line}</p>
                      })}
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>Select topics in the sidebar and click generate.</p>
                    <button className="btn-primary" style={{ margin: '0 auto' }} onClick={handleGenerateDigest}>
                      <Sparkles size={14} />
                      Generate News Digest Now
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: URL Ingestion pane (Route 2 / FR-11.5) */}
          {activeTab === 'ingest' && (
            <div className="ingest-view">
              <div className="ingest-card">
                <h2 className="ingest-title">Summarize News URL</h2>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', textAlign: 'center', marginBottom: 10 }}>
                  Enter any web page link. We will extract the core article contents and generate a summary at your preferred complexity level.
                </p>
                
                <form onSubmit={handleIngestUrl} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div className="ingest-field">
                    <span className="ingest-label">Article Link</span>
                    <input
                      type="url"
                      value={ingestUrl}
                      onChange={(e) => setIngestUrl(e.target.value)}
                      placeholder="https://news.ycombinator.com/item..."
                      className="ingest-input"
                      required
                    />
                  </div>
                  
                  <button type="submit" className="btn-primary" style={{ width: '100%', padding: '12px' }} disabled={ingestLoading}>
                    {ingestLoading ? (
                      <div className="spinner" style={{ width: 16, height: 16 }}></div>
                    ) : (
                      <>
                        <LinkIcon size={14} />
                        Extract & Summarize
                      </>
                    )}
                  </button>
                </form>

                {ingestResult && (
                  <div style={{ marginTop: 24, borderTop: '1px solid var(--border-light)', paddingTop: 20 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>Extracted Summary</span>
                      <button className="card-btn" style={{ padding: '4px 8px' }} onClick={() => handleCopyToClipboard(ingestResult)}>
                        <Copy size={12} />
                        Copy
                      </button>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: 16, borderRadius: 8, fontSize: 14, lineHeight: 1.6, border: '1px solid var(--border-light)' }}>
                      {ingestResult}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 3. RIGHT SIDEBAR: News Cards Panel (FR-3.2, FR-11.4) */}
          {activeTab === 'chat' && (
            <aside className="news-side-pane">
              <div className="news-pane-header">
                <h3 className="news-pane-title">
                  <Globe size={16} color="var(--accent-teal)" />
                  Latest Headlines
                </h3>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                  {newsItems.length} found
                </span>
              </div>

              <div className="news-scroll">
                {newsItems.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)', fontSize: 13 }}>
                    No headlines fetched yet. Ask the Assistant for news on a topic (e.g., "show me climate news") to display interactive cards.
                  </div>
                ) : (
                  newsItems.map((article, index) => (
                    <div key={index} className="news-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span className={`news-card-badge badge-${article.category || 'technology'}`}>
                          {article.category || 'news'}
                        </span>
                        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{article.published_date}</span>
                      </div>
                      <h4 className="news-card-title">{article.title}</h4>
                      <p className="news-card-desc">{article.description}</p>
                      
                      <div className="news-card-meta">
                        <span>Source: <strong>{article.source}</strong></span>
                        {article.url && (
                          <a href={article.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-teal)', textDecoration: 'none' }}>
                            Visit source
                          </a>
                        )}
                      </div>

                      {/* Interactive Card Action Buttons (FR-11.5) */}
                      <div className="news-card-actions">
                        <button className="card-btn primary" onClick={() => handleSimplifyCard(article)}>
                          <Sparkles size={12} />
                          Simplify
                        </button>
                        <button className="card-btn" onClick={() => handleExplainTopicDetail(article)}>
                          <BookOpen size={12} />
                          Explain Detail
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </aside>
          )}
        </div>
      </main>

      {/* Toast popup */}
      {toast.visible && (
        <div className="toast-msg">
          <Check size={14} color="var(--accent-teal)" />
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  )
}

export default App
