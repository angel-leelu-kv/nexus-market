import { useState, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  Filter,
  SlidersHorizontal,
  X,
  ChevronDown,
  Sparkles,
  LayoutGrid,
  List,
  Loader2,
  Cpu
} from 'lucide-react'
import ListingCard from '../components/ListingCard'
import RecommendationCard from '../components/RecommendationCard'
import { AIIndicator } from '../components/AIStatusBadge'
import { api } from '../utils/api'
import './Browse.css'

function Browse() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [listings, setListings] = useState([])
  const [recommendations, setRecommendations] = useState(null)
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchMode, setSearchMode] = useState('browse') // 'browse' or 'ai'
  const [showFilters, setShowFilters] = useState(false)
  const [viewMode, setViewMode] = useState('grid')

  // Filter states
  const [filters, setFilters] = useState({
    category: searchParams.get('category') || '',
    minPrice: '',
    maxPrice: '',
    sort: 'rating',
  })

  const query = searchParams.get('q') || ''

  // Fetch categories on mount
  useEffect(() => {
    api.getCategories().then((data) => setCategories(data.categories || []))
  }, [])

  // Fetch data based on search mode
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        if (query) {
          // AI recommendation mode
          setSearchMode('ai')
          const result = await api.getRecommendations(query)
          setRecommendations(result)
          setListings([])
        } else {
          // Browse mode
          setSearchMode('browse')
          const result = await api.getListings({
            category: filters.category,
            minPrice: filters.minPrice,
            maxPrice: filters.maxPrice,
            sort: filters.sort,
          })
          setListings(result.listings || [])
          setRecommendations(null)
        }
      } catch (error) {
        console.error('Failed to fetch:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [query, filters])

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    if (key === 'category' && value) {
      searchParams.set('category', value)
    } else if (key === 'category') {
      searchParams.delete('category')
    }
    setSearchParams(searchParams)
  }

  const clearSearch = () => {
    searchParams.delete('q')
    setSearchParams(searchParams)
  }

  const clearFilters = () => {
    setFilters({
      category: '',
      minPrice: '',
      maxPrice: '',
      sort: 'rating',
    })
    searchParams.delete('category')
    setSearchParams(searchParams)
  }

  return (
    <div className="browse-page">
      <div className="container">
        {/* Header */}
        <div className="browse-header">
          <div className="browse-title-row">
            <div>
              <h1>
                {query ? (
                  <>
                    <Sparkles className="ai-icon" size={32} />
                    AI Results for "{query}"
                  </>
                ) : filters.category ? (
                  `${filters.category} Services`
                ) : (
                  'Browse All Services'
                )}
              </h1>
              <p className="browse-subtitle">
                {loading
                  ? 'Loading...'
                  : searchMode === 'ai' && recommendations
                  ? <>
                      Found {recommendations.recommendations?.length || 0} matches with {Math.round((recommendations.queryConfidence || 0) * 100)}% confidence
                      {' '}
                      <AIIndicator aiPowered={recommendations.aiPowered} />
                    </>
                  : `${listings.length} services available`}
              </p>
            </div>

            {query && (
              <button className="btn btn-secondary" onClick={clearSearch}>
                <X size={16} />
                Clear Search
              </button>
            )}
          </div>

          {/* AI Intent Display */}
          {searchMode === 'ai' && recommendations?.intent && (
            <motion.div
              className="intent-display"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="intent-header">
                {recommendations.aiPowered ? <Sparkles size={16} /> : <Cpu size={16} />}
                <span>
                  {recommendations.aiPowered ? 'AI Analysis' : 'Smart Matching'}
                </span>
                <AIIndicator aiPowered={recommendations.aiPowered} />
              </div>
              <div className="intent-details">
                {recommendations.intent.parsed?.primaryNeed && (
                  <span className="intent-tag">
                    Need: {recommendations.intent.parsed.primaryNeed}
                  </span>
                )}
                {recommendations.intent.parsed?.constraints?.budget?.max && (
                  <span className="intent-tag">
                    Budget: Under ${recommendations.intent.parsed.constraints.budget.max}
                  </span>
                )}
                {recommendations.intent.parsed?.constraints?.quality && (
                  <span className="intent-tag">
                    Quality: {recommendations.intent.parsed.constraints.quality}
                  </span>
                )}
                {recommendations.intent.parsed?.categoryHints?.map((cat) => (
                  <span key={cat} className="intent-tag">
                    Category: {cat}
                  </span>
                ))}
              </div>
              {recommendations.intent.ambiguities?.length > 0 && (
                <div className="intent-clarifications">
                  <span>💡 Tip: </span>
                  {recommendations.intent.ambiguities[0]}
                </div>
              )}
            </motion.div>
          )}

          {/* Filter Bar (only in browse mode) */}
          {searchMode === 'browse' && (
            <div className="filter-bar">
              <div className="filter-row">
                <div className="filter-group">
                  <select
                    value={filters.category}
                    onChange={(e) => handleFilterChange('category', e.target.value)}
                    className="filter-select"
                  >
                    <option value="">All Categories</option>
                    {categories.map((cat) => (
                      <option key={cat.name} value={cat.name}>
                        {cat.name} ({cat.count})
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="select-icon" size={16} />
                </div>

                <button
                  className={`filter-toggle ${showFilters ? 'active' : ''}`}
                  onClick={() => setShowFilters(!showFilters)}
                >
                  <SlidersHorizontal size={16} />
                  Filters
                </button>

                <div className="filter-group sort-group">
                  <select
                    value={filters.sort}
                    onChange={(e) => handleFilterChange('sort', e.target.value)}
                    className="filter-select"
                  >
                    <option value="rating">Top Rated</option>
                    <option value="price_asc">Price: Low to High</option>
                    <option value="price_desc">Price: High to Low</option>
                  </select>
                  <ChevronDown className="select-icon" size={16} />
                </div>

                <div className="view-toggle">
                  <button
                    className={viewMode === 'grid' ? 'active' : ''}
                    onClick={() => setViewMode('grid')}
                  >
                    <LayoutGrid size={18} />
                  </button>
                  <button
                    className={viewMode === 'list' ? 'active' : ''}
                    onClick={() => setViewMode('list')}
                  >
                    <List size={18} />
                  </button>
                </div>
              </div>

              <AnimatePresence>
                {showFilters && (
                  <motion.div
                    className="filter-expanded"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="filter-section">
                      <label>Price Range</label>
                      <div className="price-inputs">
                        <input
                          type="number"
                          placeholder="Min"
                          value={filters.minPrice}
                          onChange={(e) => handleFilterChange('minPrice', e.target.value)}
                          className="input"
                        />
                        <span>to</span>
                        <input
                          type="number"
                          placeholder="Max"
                          value={filters.maxPrice}
                          onChange={(e) => handleFilterChange('maxPrice', e.target.value)}
                          className="input"
                        />
                      </div>
                    </div>

                    <button className="btn btn-ghost" onClick={clearFilters}>
                      Clear All Filters
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Results */}
        <div className="browse-results">
          {loading ? (
            <div className="loading-state">
              <Loader2 className="spinner" size={40} />
              <p>
                {searchMode === 'ai' ? 'AI is analyzing your request...' : 'Loading services...'}
              </p>
            </div>
          ) : searchMode === 'ai' && recommendations ? (
            // AI Recommendations
            <div className="recommendations-list">
              {recommendations.recommendations?.length > 0 ? (
                recommendations.recommendations.map((rec, index) => (
                  <RecommendationCard key={rec.id} recommendation={rec} index={index} />
                ))
              ) : (
                <div className="empty-state">
                  <Sparkles size={48} />
                  <h3>No exact matches found</h3>
                  <p>
                    {recommendations.fallback?.message || 'Try adjusting your search or browse all services.'}
                  </p>
                  {recommendations.fallback?.suggestions && (
                    <ul className="suggestions-list">
                      {recommendations.fallback.suggestions.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ul>
                  )}
                  <button className="btn btn-primary" onClick={clearSearch}>
                    Browse All Services
                  </button>
                </div>
              )}
            </div>
          ) : (
            // Regular Browse Grid
            <div className={`listings-results ${viewMode}`}>
              {listings.length > 0 ? (
                listings.map((listing, index) => (
                  <ListingCard
                    key={listing.id}
                    listing={listing}
                    index={index}
                    variant={viewMode === 'list' ? 'horizontal' : 'default'}
                  />
                ))
              ) : (
                <div className="empty-state">
                  <Filter size={48} />
                  <h3>No services found</h3>
                  <p>Try adjusting your filters or search criteria.</p>
                  <button className="btn btn-primary" onClick={clearFilters}>
                    Clear Filters
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Browse

