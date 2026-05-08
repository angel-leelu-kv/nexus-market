import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Star, Clock, TrendingUp, CheckCircle } from 'lucide-react'
import './ListingCard.css'

function ListingCard({ listing, seller, index = 0, variant = 'default' }) {
  const formatPrice = (price, unit) => {
    if (unit === 'monthly') return `$${price}/mo`
    if (unit === 'hourly') return `$${price}/hr`
    return `$${price}`
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      className={`listing-card ${variant}`}
    >
      <Link to={`/listing/${listing.id}`} className="listing-card-link">
        {/* Image */}
        <div className="listing-card-image">
          <div className="listing-image-placeholder">
            <span className="listing-category-icon">
              {getCategoryIcon(listing.category)}
            </span>
          </div>
          {listing.metrics?.salesCount > 50 && (
            <span className="listing-badge popular">
              <TrendingUp size={12} /> Popular
            </span>
          )}
        </div>

        {/* Content */}
        <div className="listing-card-content">
          {/* Seller */}
          {seller && (
            <div className="listing-seller">
              <img
                src={seller.avatar}
                alt={seller.name}
                className="seller-avatar"
              />
              <span className="seller-name">{seller.name}</span>
              {seller.verified && (
                <CheckCircle className="verified-badge" size={14} />
              )}
            </div>
          )}

          {/* Title */}
          <h3 className="listing-title">{listing.title}</h3>

          {/* Description */}
          <p className="listing-description line-clamp-2">
            {listing.description}
          </p>

          {/* Stats */}
          <div className="listing-stats">
            <div className="listing-rating">
              <Star className="star-icon" size={14} />
              <span className="rating-value">
                {listing.metrics?.averageRating?.toFixed(1) || '0.0'}
              </span>
              <span className="rating-count">
                ({listing.metrics?.totalReviews || 0})
              </span>
            </div>
            {listing.attributes?.deliveryTime && (
              <div className="listing-delivery">
                <Clock size={14} />
                <span>{listing.attributes.deliveryTime}</span>
              </div>
            )}
          </div>

          {/* Tags */}
          <div className="listing-tags">
            {listing.attributes?.tags?.slice(0, 3).map((tag) => (
              <span key={tag} className="listing-tag">
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="listing-card-footer">
          <span className="listing-price-label">Starting at</span>
          <span className="listing-price">
            {formatPrice(listing.price, listing.priceUnit)}
          </span>
        </div>
      </Link>
    </motion.div>
  )
}

function getCategoryIcon(category) {
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

export default ListingCard

