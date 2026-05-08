import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Sparkles, ArrowRight, Loader2 } from 'lucide-react'
import './SearchBar.css'

function SearchBar({ large = false, placeholder = "Describe what you need...", autoFocus = false }) {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  const exampleQueries = [
    "I need a website for my bakery under $500",
    "Looking for a logo designer for my startup",
    "Build me a mobile app for fitness tracking",
    "SEO expert to improve my rankings",
    "Video editor for my YouTube channel",
  ]

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus()
    }
  }, [autoFocus])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    // Navigate to browse with the query
    navigate(`/browse?q=${encodeURIComponent(query)}`)
    setIsLoading(false)
  }

  const handleExampleClick = (example) => {
    setQuery(example)
    navigate(`/browse?q=${encodeURIComponent(example)}`)
  }

  return (
    <div className={`search-bar-container ${large ? 'large' : ''}`}>
      <form onSubmit={handleSubmit} className="search-bar-form">
        <div className="search-bar-input-wrapper">
          <div className="search-bar-icon">
            {isLoading ? (
              <Loader2 className="spinning" size={large ? 24 : 20} />
            ) : (
              <Sparkles size={large ? 24 : 20} />
            )}
          </div>
          
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder={placeholder}
            className="search-bar-input"
          />

          <button
            type="submit"
            className="search-bar-button"
            disabled={!query.trim() || isLoading}
          >
            <span>Search</span>
            <ArrowRight size={18} />
          </button>
        </div>

        <AnimatePresence>
          {showSuggestions && !query && (
            <motion.div
              className="search-suggestions"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <p className="suggestions-label">Try asking:</p>
              <div className="suggestions-list">
                {exampleQueries.map((example, index) => (
                  <button
                    key={index}
                    type="button"
                    className="suggestion-item"
                    onClick={() => handleExampleClick(example)}
                  >
                    <Search size={14} />
                    <span>{example}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </form>

      {large && (
        <div className="search-tags">
          <span className="search-tags-label">Popular:</span>
          {['Web Development', 'Logo Design', 'SEO', 'Mobile App', 'Copywriting'].map((tag) => (
            <button
              key={tag}
              type="button"
              className="search-tag"
              onClick={() => handleExampleClick(`I need ${tag.toLowerCase()} services`)}
            >
              {tag}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default SearchBar

