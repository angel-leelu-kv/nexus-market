import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageCircle,
  X,
  Send,
  Sparkles,
  Loader2,
  Bot,
  User,
  Maximize2,
  Minimize2,
  ArrowRight,
  Wrench
} from 'lucide-react'
import { api } from '../utils/api'
import './AIChatbox.css'

function AIChatbox() {
  const [isOpen, setIsOpen] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm your AI assistant. I can help you find the perfect services. Just describe what you need!",
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Use the AI Agent endpoint with Netra tracing
      const response = await api.agent(input, {
        previousMessages: messages.slice(-4).map(m => ({
          role: m.role,
          content: m.content,
        })),
      })
      
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        toolsUsed: response.tools_used || response.toolsUsed,
        sessionId: response.session_id,
        aiPowered: response.ai_powered || response.aiPowered,
      }
      
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const isAINotConfigured = error.message?.includes('503') || error.message?.includes('not configured') || error.message?.includes('unavailable')
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: isAINotConfigured 
          ? "AI Agent is not available. Please run ./start.sh to start all services."
          : "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
        isError: true,
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestionClick = (suggestion) => {
    setInput(suggestion)
    inputRef.current?.focus()
  }

  const quickPrompts = [
    "I need a website for my business",
    "Find me a logo designer",
    "Looking for SEO help",
    "Need a mobile app developer",
  ]

  return (
    <>
      {/* Chat Toggle Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            className="chat-toggle-btn"
            onClick={() => setIsOpen(true)}
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <Sparkles className="chat-toggle-icon" size={24} />
            <span className="chat-toggle-label">AI Assistant</span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={`chatbox ${isExpanded ? 'expanded' : ''}`}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
          >
            {/* Header */}
            <div className="chatbox-header">
              <div className="chatbox-title">
                <div className="chatbox-avatar">
                  <Sparkles size={18} />
                </div>
                <div>
                  <h3>AI Assistant</h3>
                  <span className="chatbox-status">
                    <span className="status-dot" />
                    Online
                  </span>
                </div>
              </div>
              <div className="chatbox-actions">
                <button
                  className="chatbox-action-btn"
                  onClick={() => setIsExpanded(!isExpanded)}
                  title={isExpanded ? 'Minimize' : 'Expand'}
                >
                  {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                </button>
                <button
                  className="chatbox-action-btn"
                  onClick={() => setIsOpen(false)}
                  title="Close"
                >
                  <X size={16} />
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="chatbox-messages">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`chat-message ${message.role} ${message.isError ? 'error' : ''}`}
                >
                  <div className="message-avatar">
                    {message.role === 'assistant' ? (
                      <Bot size={16} />
                    ) : (
                      <User size={16} />
                    )}
                  </div>
                  <div className="message-content">
                    <p>{message.content}</p>
                    
                    {/* Recommendations */}
                    {message.recommendations && (
                      <div className="message-recommendations">
                        {message.recommendations.map((rec) => (
                          <a
                            key={rec.listing.id}
                            href={`/listing/${rec.listing.id}`}
                            className="rec-card"
                          >
                            <div className="rec-info">
                              <span className="rec-title">{rec.listing.title}</span>
                              <span className="rec-meta">
                                ${rec.listing.price} • {rec.scores?.overall || 0}% match
                              </span>
                            </div>
                            <ArrowRight size={14} />
                          </a>
                        ))}
                      </div>
                    )}
                    
                    {/* Suggestions */}
                    {message.suggestions && (
                      <div className="message-suggestions">
                        {message.suggestions.map((suggestion, i) => (
                          <button
                            key={i}
                            className="suggestion-btn"
                            onClick={() => handleSuggestionClick(suggestion)}
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                    
                    {/* Tools Used Badge */}
                    {message.toolsUsed && message.toolsUsed.length > 0 && (
                      <div className="tools-used">
                        <Wrench size={12} />
                        <span>{message.toolsUsed.join(', ')}</span>
                      </div>
                    )}
                    
                    {/* AI Badge */}
                    {message.aiPowered !== undefined && (
                      <span className={`ai-badge ${message.aiPowered ? 'ai' : 'smart'}`}>
                        {message.aiPowered ? '✨ AI' : '⚡ Smart'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
              
              {/* Loading indicator */}
              {isLoading && (
                <div className="chat-message assistant loading">
                  <div className="message-avatar">
                    <Bot size={16} />
                  </div>
                  <div className="message-content">
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

            {/* Quick Prompts (shown when no messages from user) */}
            {messages.length === 1 && (
              <div className="quick-prompts">
                <p>Try asking:</p>
                <div className="quick-prompts-grid">
                  {quickPrompts.map((prompt, i) => (
                    <button
                      key={i}
                      className="quick-prompt-btn"
                      onClick={() => handleSuggestionClick(prompt)}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="chatbox-input">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Describe what you need..."
                rows={1}
                disabled={isLoading}
              />
              <button
                className="send-btn"
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
              >
                {isLoading ? (
                  <Loader2 className="spinning" size={18} />
                ) : (
                  <Send size={18} />
                )}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}

export default AIChatbox

