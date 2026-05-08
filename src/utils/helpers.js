/**
 * Utility helper functions
 */

/**
 * Format price with currency
 */
export function formatPrice(price, unit = 'fixed', currency = 'USD') {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })

  const formatted = formatter.format(price)

  if (unit === 'monthly') return `${formatted}/mo`
  if (unit === 'hourly') return `${formatted}/hr`
  return formatted
}

/**
 * Format date relative to now
 */
export function formatRelativeDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffInMs = now - date
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

  if (diffInDays === 0) return 'Today'
  if (diffInDays === 1) return 'Yesterday'
  if (diffInDays < 7) return `${diffInDays} days ago`
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`
  if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`
  return `${Math.floor(diffInDays / 365)} years ago`
}

/**
 * Format a date string to locale date
 */
export function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}

/**
 * Debounce function
 */
export function debounce(func, wait = 300) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Calculate rating stars array
 */
export function getRatingStars(rating, maxStars = 5) {
  const fullStars = Math.floor(rating)
  const hasHalfStar = rating % 1 >= 0.5
  const emptyStars = maxStars - fullStars - (hasHalfStar ? 1 : 0)

  return {
    full: fullStars,
    half: hasHalfStar ? 1 : 0,
    empty: emptyStars,
  }
}

/**
 * Get category icon emoji
 */
export function getCategoryIcon(category) {
  const icons = {
    Development: '💻',
    Design: '🎨',
    Marketing: '📈',
    Writing: '✍️',
    Video: '🎬',
    'Data & AI': '🤖',
  }
  return icons[category] || '📦'
}

/**
 * Get match quality label
 */
export function getMatchLabel(score) {
  if (score >= 80) return { text: 'Excellent Match', color: 'success' }
  if (score >= 60) return { text: 'Strong Match', color: 'primary' }
  if (score >= 40) return { text: 'Good Match', color: 'warning' }
  return { text: 'Potential Match', color: 'default' }
}

/**
 * Generate unique ID
 */
export function generateId(prefix = 'id') {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Clamp a number between min and max
 */
export function clamp(num, min, max) {
  return Math.min(Math.max(num, min), max)
}

/**
 * Parse URL search params to object
 */
export function parseSearchParams(searchParams) {
  const params = {}
  for (const [key, value] of searchParams.entries()) {
    params[key] = value
  }
  return params
}

export default {
  formatPrice,
  formatRelativeDate,
  formatDate,
  truncate,
  debounce,
  getRatingStars,
  getCategoryIcon,
  getMatchLabel,
  generateId,
  clamp,
  parseSearchParams,
}

