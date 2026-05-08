import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Star, CheckCircle, Zap, TrendingUp, Clock, DollarSign } from 'lucide-react'
import './RecommendationCard.css'

function RecommendationCard({ recommendation, index = 0 }) {
  const { listing, seller, scores, explanation, rank } = recommendation

  const getMatchLabel = (score) => {
    if (score >= 80) return { text: 'Excellent Match', color: 'success' }
    if (score >= 60) return { text: 'Strong Match', color: 'primary' }
    if (score >= 40) return { text: 'Good Match', color: 'warning' }
    return { text: 'Potential Match', color: 'default' }
  }

  const matchLabel = getMatchLabel(scores?.overall || 0)

  return (
    <motion.div
      className="recommendation-card"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
    >
      {/* Rank Badge */}
      {rank <= 3 && (
        <div className={`rank-badge rank-${rank}`}>
          {rank === 1 ? '🥇' : rank === 2 ? '🥈' : '🥉'} #{rank}
        </div>
      )}

      <Link to={`/listing/${listing.id}`} className="recommendation-link">
        <div className="recommendation-content">
          {/* Header */}
          <div className="recommendation-header">
            <div className="recommendation-meta">
              <span className={`match-badge ${matchLabel.color}`}>
                <Zap size={12} />
                {scores?.overall || 0}% Match
              </span>
              <span className="category-badge">{listing.category}</span>
            </div>
            <div className="listing-price-tag">
              ${listing.price}
              {listing.priceUnit !== 'fixed' && `/${listing.priceUnit === 'monthly' ? 'mo' : 'hr'}`}
            </div>
          </div>

          {/* Title & Seller */}
          <h3 className="recommendation-title">{listing.title}</h3>

          {seller && (
            <div className="recommendation-seller">
              <img src={seller.avatar} alt={seller.name} className="seller-avatar" />
              <span className="seller-name">{seller.name}</span>
              {seller.verified && <CheckCircle className="verified-icon" size={14} />}
              <span className="seller-level">{seller.verificationLevel}</span>
            </div>
          )}

          {/* AI Explanation */}
          {explanation && (
            <div className="ai-explanation">
              <div className="explanation-summary">
                <Zap className="ai-icon" size={14} />
                <span>{explanation.summary}</span>
              </div>

              {explanation.strengths?.length > 0 && (
                <ul className="explanation-points">
                  {explanation.strengths.slice(0, 2).map((strength, i) => (
                    <li key={i}>
                      <CheckCircle size={12} />
                      <span>{strength}</span>
                    </li>
                  ))}
                </ul>
              )}

              {explanation.considerations?.length > 0 && (
                <div className="explanation-note">
                  {explanation.considerations[0]}
                </div>
              )}
            </div>
          )}

          {/* Score Breakdown */}
          <div className="score-breakdown">
            <div className="score-item">
              <TrendingUp size={14} />
              <span className="score-label">Relevance</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${scores?.relevance || 0}%` }} />
              </div>
            </div>
            <div className="score-item">
              <Star size={14} />
              <span className="score-label">Quality</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${scores?.quality || 0}%` }} />
              </div>
            </div>
            <div className="score-item">
              <DollarSign size={14} />
              <span className="score-label">Value</span>
              <div className="score-bar">
                <div className="score-fill" style={{ width: `${scores?.value || 0}%` }} />
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="recommendation-stats">
            <div className="stat">
              <Star className="star-filled" size={14} />
              <span>{listing.metrics?.averageRating?.toFixed(1) || '0.0'}</span>
              <span className="stat-label">({listing.metrics?.totalReviews || 0} reviews)</span>
            </div>
            <div className="stat">
              <Clock size={14} />
              <span>{listing.attributes?.deliveryTime || 'Varies'}</span>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

export default RecommendationCard

