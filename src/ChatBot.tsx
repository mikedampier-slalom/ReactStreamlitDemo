import React, { useState, useRef, useEffect } from 'react'
import './ChatBot.css'

interface Message {
  role: 'user' | 'analyst'
  content: MessageContent[]
  request_id?: string
}

interface MessageContent {
  type: 'text' | 'sql' | 'suggestions'
  text?: string
  statement?: string
  suggestions?: string[]
  confidence?: any
}

interface SQLResult {
  columns: string[]
  data: any[]
  row_count: number
}

export function ChatBot() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sqlResults, setSqlResults] = useState<{[key: number]: SQLResult}>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: [{ type: 'text', text: messageText }]
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:3000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content
          })),
          semantic_model: "DAMPIERMIKE.REVENUE_TIMESERIES.RAW_DATA/revenue_timeseries.yaml"
        })
      })

      const data = await response.json()
      
      if (data.error) {
        const errorMessage: Message = {
          role: 'analyst',
          content: [{ type: 'text', text: `Error: ${data.error}\n\n${data.details ? JSON.stringify(data.details, null, 2) : ''}` }]
        }
        setMessages(prev => [...prev, errorMessage])
      } else if (data.message) {
        const analystMessage: Message = {
          role: 'analyst',
          content: data.message.content,
          request_id: data.request_id
        }
        setMessages(prev => [...prev, analystMessage])
        
        // Execute any SQL queries in the response
        const sqlContent = data.message.content.find((c: MessageContent) => c.type === 'sql')
        if (sqlContent && sqlContent.statement) {
          // Use the correct message index (current messages + user message + analyst message)
          const messageIndex = messages.length + 1
          await executeSql(sqlContent.statement, messageIndex)
        }
      }
    } catch (error) {
      const errorMessage: Message = {
        role: 'analyst',
        content: [{ type: 'text', text: `Failed to send message: ${error}` }]
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const executeSql = async (sql: string, messageIndex: number) => {
    console.log(`Executing SQL for message index ${messageIndex}:`, sql)
    try {
      const response = await fetch('http://127.0.0.1:3000/execute-sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql })
      })

      const data = await response.json()
      
      if (data.error) {
        console.error('SQL execution error:', data.error)
        // Store error as result
        setSqlResults(prev => ({
          ...prev,
          [messageIndex]: { error: data.error, columns: [], data: [], row_count: 0 }
        }))
      } else {
        console.log(`SQL results for message ${messageIndex}:`, data)
        setSqlResults(prev => ({
          ...prev,
          [messageIndex]: data
        }))
      }
    } catch (error) {
      console.error('Failed to execute SQL:', error)
      setSqlResults(prev => ({
        ...prev,
        [messageIndex]: { error: String(error), columns: [], data: [], row_count: 0 }
      }))
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    sendMessage(input)
  }

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <h2>💬 Cortex Analyst Chat</h2>
        <button onClick={() => setMessages([])} className="clear-btn">Clear Chat</button>
      </div>

      <div className="chatbot-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Welcome to Cortex Analyst! Ask me questions about your data.</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              {message.content.map((content, contentIndex) => (
                <div key={contentIndex}>
                  {content.type === 'text' && (
                    <p className="message-text">{content.text}</p>
                  )}

                  {content.type === 'suggestions' && content.suggestions && (
                    <div className="suggestions">
                      {content.suggestions.map((suggestion, suggestionIndex) => (
                        <button
                          key={suggestionIndex}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="suggestion-btn"
                          disabled={loading}
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}

                  {content.type === 'sql' && content.statement && (
                    <div className="sql-section">
                      <details>
                        <summary>SQL Query</summary>
                        <pre className="sql-code">{content.statement}</pre>
                      </details>
                      
                      {sqlResults[index] && !sqlResults[index].error && (
                        <details open>
                          <summary>Results ({sqlResults[index].row_count} rows)</summary>
                          <div className="sql-results">
                            {sqlResults[index].row_count > 0 ? (
                              <>
                                <table>
                                  <thead>
                                    <tr>
                                      {sqlResults[index].columns.map((col, i) => (
                                        <th key={i}>{col}</th>
                                      ))}
                                    </tr>
                              </thead>
                              <tbody>
                                {sqlResults[index].data.slice(0, 10).map((row, rowIndex) => (
                                  <tr key={rowIndex}>
                                    {sqlResults[index].columns.map((col, colIndex) => (
                                      <td key={colIndex}>{String(row[col])}</td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {sqlResults[index].row_count > 10 && (
                              <p className="more-rows">
                                ... and {sqlResults[index].row_count - 10} more rows
                              </p>
                            )}
                              </>
                            ) : (
                              <p style={{ fontStyle: 'italic', color: '#666' }}>No results returned</p>
                            )}
                          </div>
                        </details>
                      )}
                      
                      {sqlResults[index] && sqlResults[index].error && (
                        <details open>
                          <summary style={{ color: '#d32f2f' }}>❌ SQL Execution Error</summary>
                          <div className="sql-results" style={{ color: '#d32f2f' }}>
                            <pre>{sqlResults[index].error}</pre>
                          </div>
                        </details>
                      )}
                      
                      {!sqlResults[index] && (
                        <p style={{ fontStyle: 'italic', opacity: 0.7, marginTop: '0.5rem' }}>
                          Executing query...
                        </p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message analyst">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <p className="message-text" style={{ fontStyle: 'italic', opacity: 0.8 }}>
                Analyzing your question and generating insights... This may take up to 2 minutes.
              </p>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chatbot-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your data..."
          disabled={loading}
          className="chatbot-input"
        />
        <button type="submit" disabled={loading || !input.trim()} className="send-btn">
          Send
        </button>
      </form>
    </div>
  )
}
