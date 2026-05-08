import { useState, useEffect } from 'react'
import { Sparkles, Cpu } from 'lucide-react'
import { api } from '../utils/api'
import './AIStatusBadge.css'

function AIStatusBadge({ showDetails = false }) {
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getAIStatus()
      .then(setStatus)
      .catch(() => setStatus({ configured: false }))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return null

  const isAIEnabled = status?.configured

  return (
    <div className={`ai-status-badge ${isAIEnabled ? 'enabled' : 'fallback'}`}>
      <div className="ai-status-icon">
        {isAIEnabled ? <Sparkles size={14} /> : <Cpu size={14} />}
      </div>
      <span className="ai-status-text">
        {isAIEnabled ? 'AI Powered' : 'Offline'}
      </span>
      {showDetails && status?.model && (
        <span className="ai-status-model">{status.model}</span>
      )}
    </div>
  )
}

export function AIIndicator({ aiPowered, className = '' }) {
  return (
    <span className={`ai-indicator ${aiPowered ? 'ai' : 'rule'} ${className}`}>
      {aiPowered ? (
        <>
          <Sparkles size={12} />
          <span>AI</span>
        </>
      ) : (
        <>
          <Cpu size={12} />
          <span>Smart</span>
        </>
      )}
    </span>
  )
}

export default AIStatusBadge
