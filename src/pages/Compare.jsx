import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Scale,
  Star,
  CheckCircle,
  X,
  Trophy,
  Loader2,
  ArrowLeft,
  Clock,
  DollarSign,
  Sparkles
} from 'lucide-react'
import { AIIndicator } from '../components/AIStatusBadge'
import { api } from '../utils/api'
import './Compare.css'

function Compare() {
  const [searchParams] = useSearchParams()
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(true)

  const listingIds = searchParams.get('ids')?.split(',') || []

  useEffect(() => {
    const fetchComparison = async () => {
      if (listingIds.length < 2) {
        setLoading(false)
        return
      }

      try {
        const result = await api.compareListings(listingIds)
        setComparison(result)
      } catch (error) {
        console.error('Failed to fetch comparison:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchComparison()
  }, [listingIds.join(',')])

  if (loading) {
    return (
      <div className="compare-page loading">
        <Loader2 className="spinner" size={40} />
        <p>Generating AI comparison...</p>
      </div>
    )
  }

  if (listingIds.length < 2) {
    return (
      <div className="compare-page empty">
        <Scale size={64} />
        <h2>Compare Services</h2>
        <p>Select at least 2 services to compare</p>
        <Link to="/browse" className="btn btn-primary">
          Browse Services
        </Link>
      </div>
    )
  }

  if (!comparison?.listings) {
    return (
      <div className="compare-page error">
        <h2>Comparison not available</h2>
        <Link to="/browse" className="btn btn-primary">
          Back to Browse
        </Link>
      </div>
    )
  }

  const { listings, comparison: comparisonData } = comparison

  return (
    <div className="compare-page">
      <div className="container">
        {/* Header */}
        <div className="compare-header">
          <Link to="/browse" className="back-link">
            <ArrowLeft size={16} />
            Back to Browse
          </Link>
          <h1>
            <Scale size={28} />
            AI-Powered Comparison
          </h1>
          <p>Side-by-side analysis of {listings.length} services</p>
        </div>

        {/* Verdict */}
        {comparisonData?.verdict && (
          <motion.div
            className="verdict-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="verdict-icon">
              {comparison.aiPowered ? <Sparkles size={24} /> : <Trophy size={24} />}
            </div>
            <div className="verdict-content">
              <div className="verdict-title-row">
                <h3>{comparison.aiPowered ? 'AI Verdict' : 'Analysis'}</h3>
                <AIIndicator aiPowered={comparison.aiPowered} />
              </div>
              <p>{comparisonData.verdict}</p>
            </div>
          </motion.div>
        )}

        {/* Comparison Table */}
        <div className="comparison-table-wrapper">
          <table className="comparison-table">
            <thead>
              <tr>
                <th className="feature-header">Feature</th>
                {listings.map((listing) => (
                  <th key={listing.id} className="listing-header">
                    <div className="listing-header-content">
                      {comparisonData?.overallWinner === listing.id && (
                        <span className="winner-badge">
                          <Trophy size={12} /> Top Pick
                        </span>
                      )}
                      <h4>{listing.title}</h4>
                      <span className="listing-seller">
                        by {listing.seller?.name}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {/* Price Row */}
              <tr>
                <td className="feature-cell">
                  <DollarSign size={16} />
                  Price
                </td>
                {listings.map((listing) => (
                  <td
                    key={listing.id}
                    className={`value-cell ${
                      comparisonData?.dimensions?.find((d) => d.name === 'Price')?.winner === listing.id
                        ? 'winner'
                        : ''
                    }`}
                  >
                    <span className="value-main">${listing.price}</span>
                    {listing.priceUnit !== 'fixed' && (
                      <span className="value-sub">/{listing.priceUnit}</span>
                    )}
                  </td>
                ))}
              </tr>

              {/* Rating Row */}
              <tr>
                <td className="feature-cell">
                  <Star size={16} />
                  Rating
                </td>
                {listings.map((listing) => (
                  <td
                    key={listing.id}
                    className={`value-cell ${
                      comparisonData?.dimensions?.find((d) => d.name === 'Quality')?.winner === listing.id
                        ? 'winner'
                        : ''
                    }`}
                  >
                    <div className="rating-cell">
                      <Star className="star-filled" size={14} />
                      <span className="value-main">
                        {listing.metrics?.averageRating?.toFixed(1) || 'N/A'}
                      </span>
                      <span className="value-sub">
                        ({listing.metrics?.totalReviews || 0} reviews)
                      </span>
                    </div>
                  </td>
                ))}
              </tr>

              {/* Delivery Row */}
              <tr>
                <td className="feature-cell">
                  <Clock size={16} />
                  Delivery
                </td>
                {listings.map((listing) => (
                  <td key={listing.id} className="value-cell">
                    <span className="value-main">
                      {listing.attributes?.deliveryTime || 'Varies'}
                    </span>
                  </td>
                ))}
              </tr>

              {/* Completion Rate Row */}
              <tr>
                <td className="feature-cell">
                  <CheckCircle size={16} />
                  Completion
                </td>
                {listings.map((listing) => (
                  <td
                    key={listing.id}
                    className={`value-cell ${
                      comparisonData?.dimensions?.find((d) => d.name === 'Reliability')?.winner === listing.id
                        ? 'winner'
                        : ''
                    }`}
                  >
                    <span className="value-main">
                      {Math.round((listing.metrics?.completionRate || 0) * 100)}%
                    </span>
                  </td>
                ))}
              </tr>

              {/* Value Row */}
              <tr>
                <td className="feature-cell">
                  <Scale size={16} />
                  Value
                </td>
                {listings.map((listing) => {
                  const valueData = comparisonData?.dimensions?.find((d) => d.name === 'Value')
                  return (
                    <td
                      key={listing.id}
                      className={`value-cell ${valueData?.winner === listing.id ? 'winner' : ''}`}
                    >
                      <span className="value-main">
                        {valueData?.values?.[listing.id] || 'N/A'}
                      </span>
                    </td>
                  )
                })}
              </tr>
            </tbody>
          </table>
        </div>

        {/* Pros & Cons */}
        <div className="pros-cons-section">
          <h2>Analysis</h2>
          <div className="pros-cons-grid">
            {listings.map((listing) => {
              const analysis = comparisonData?.perListing?.[listing.id]
              return (
                <motion.div
                  key={listing.id}
                  className={`analysis-card ${
                    comparisonData?.overallWinner === listing.id ? 'winner' : ''
                  }`}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  {comparisonData?.overallWinner === listing.id && (
                    <div className="winner-ribbon">
                      <Trophy size={14} />
                      Top Pick
                    </div>
                  )}
                  <h3>{listing.title}</h3>
                  <span className="analysis-price">${listing.price}</span>

                  {analysis?.pros?.length > 0 && (
                    <div className="pros-list">
                      <h4>Pros</h4>
                      <ul>
                        {analysis.pros.map((pro, i) => (
                          <li key={i}>
                            <CheckCircle size={14} />
                            <span>{pro}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysis?.cons?.length > 0 && (
                    <div className="cons-list">
                      <h4>Cons</h4>
                      <ul>
                        {analysis.cons.map((con, i) => (
                          <li key={i}>
                            <X size={14} />
                            <span>{con}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {analysis?.bestFor && (
                    <div className="best-for">
                      <strong>Best for:</strong> {analysis.bestFor}
                    </div>
                  )}

                  <Link to={`/listing/${listing.id}`} className="btn btn-secondary">
                    View Details
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Compare

