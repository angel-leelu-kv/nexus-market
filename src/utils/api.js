/**
 * API Client for AI Marketplace
 * Handles all communication with the backend
 */

const API_BASE = '/api'

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }))
      throw new Error(error.error || `HTTP ${response.status}`)
    }
    
    return response.json()
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error)
    throw error
  }
}

// Cache AI status
let aiStatusCache = null

export const api = {
  // ================================
  // LISTINGS
  // ================================
  
  /**
   * Get all listings with optional filters
   */
  getListings: (params = {}) => {
    const query = new URLSearchParams()
    if (params.category) query.set('category', params.category)
    if (params.minPrice) query.set('minPrice', params.minPrice)
    if (params.maxPrice) query.set('maxPrice', params.maxPrice)
    if (params.sort) query.set('sort', params.sort)
    
    const queryString = query.toString()
    return fetchAPI(`/listings${queryString ? `?${queryString}` : ''}`)
  },
  
  /**
   * Get a single listing by ID
   */
  getListing: (id) => {
    return fetchAPI(`/listings/${id}`)
  },

  // ================================
  // SELLERS
  // ================================
  
  /**
   * Get all sellers
   */
  getSellers: () => {
    return fetchAPI('/sellers')
  },
  
  /**
   * Get a single seller by ID
   */
  getSeller: (id) => {
    return fetchAPI(`/sellers/${id}`)
  },

  // ================================
  // AI RECOMMENDATIONS
  // ================================
  
  /**
   * Get AI-powered recommendations based on natural language query
   */
  getRecommendations: (query) => {
    return fetchAPI('/recommend', {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
  },
  
  /**
   * Parse user intent from query (for UI feedback)
   */
  parseIntent: (query) => {
    return fetchAPI('/parse-intent', {
      method: 'POST',
      body: JSON.stringify({ query }),
    })
  },
  
  /**
   * Compare multiple listings
   */
  compareListings: (listingIds, query = '') => {
    return fetchAPI('/compare', {
      method: 'POST',
      body: JSON.stringify({ listingIds, query }),
    })
  },

  // ================================
  // CATEGORIES
  // ================================
  
  /**
   * Get all categories with counts
   */
  getCategories: () => {
    return fetchAPI('/categories')
  },

  // ================================
  // HOME
  // ================================
  
  /**
   * Get personalized home recommendations
   */
  getHomeRecommendations: () => {
    return fetchAPI('/home-recommendations')
  },

  // ================================
  // AI STATUS & CHAT
  // ================================
  
  /**
   * Get AI service status
   */
  getAIStatus: async () => {
    if (aiStatusCache) return aiStatusCache
    const status = await fetchAPI('/ai-status')
    aiStatusCache = status
    return status
  },
  
  /**
   * Send a chat message to AI
   */
  chat: (message, context = {}) => {
    return fetchAPI('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, context }),
    })
  },
  
  /**
   * Use AI Agent with tool calling (Netra traced)
   */
  agent: (query, context = {}) => {
    return fetchAPI('/agent', {
      method: 'POST',
      body: JSON.stringify({ query, context }),
    })
  },
}

export default api

