import React, { useState } from 'react'
import './App.css'
import { ChatBot } from './ChatBot'

interface LambdaResponse {
  message: string;
  event?: any;
  error?: string;
  snowflake_version?: string;
  warehouse?: string;
  database?: string;
  schema?: string;
}

function App() {
  const [response, setResponse] = useState<LambdaResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const callLambda = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const res = await fetch('http://127.0.0.1:3000/hello')
      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch')
    } finally {
      setLoading(false)
    }
  }

  const testSnowflake = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const res = await fetch('http://127.0.0.1:3000/test-snowflake')
      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="App">
      <h1>Hello World!</h1>
      <p>Welcome to React with TypeScript</p>
      
      <ChatBot />
      
      <div className="lambda-section">
        <h2>Test Lambda Functions</h2>
        
        <div className="button-group">
          <button onClick={callLambda} disabled={loading}>
            {loading ? 'Calling...' : 'Call Lambda Function'}
          </button>
          
          <button onClick={testSnowflake} disabled={loading} className="snowflake-btn">
            {loading ? 'Testing...' : '❄️ Test Snowflake'}
          </button>
        </div>
        
        {error && (
          <div className="error">
            <strong>Error:</strong> {error}
          </div>
        )}
        
        {response && (
          <div className="response">
            <h3>Response:</h3>
            <pre>{JSON.stringify(response, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
