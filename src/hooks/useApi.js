import { useState, useEffect, useCallback } from 'react'

/**
 * Generic hook for API calls with loading and error states
 */
export function useApi(apiCall, dependencies = [], options = {}) {
  const { immediate = true, initialData = null } = options
  
  const [data, setData] = useState(initialData)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState(null)

  const execute = useCallback(async (...args) => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await apiCall(...args)
      setData(result)
      return result
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }, [apiCall])

  useEffect(() => {
    if (immediate) {
      execute()
    }
  }, dependencies)

  return { data, loading, error, execute, setData }
}

/**
 * Hook for debounced API calls (useful for search)
 */
export function useDebouncedApi(apiCall, delay = 300) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const execute = useCallback(
    debounce(async (...args) => {
      setLoading(true)
      setError(null)
      
      try {
        const result = await apiCall(...args)
        setData(result)
        return result
      } catch (err) {
        setError(err)
        throw err
      } finally {
        setLoading(false)
      }
    }, delay),
    [apiCall, delay]
  )

  return { data, loading, error, execute, setData }
}

/**
 * Simple debounce utility
 */
function debounce(func, wait) {
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

export default useApi

