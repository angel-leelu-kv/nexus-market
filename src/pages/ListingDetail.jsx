import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Star,
  CheckCircle,
  Clock,
  MapPin,
  Calendar,
  MessageCircle,
  Heart,
  Share2,
  ChevronRight,
  TrendingUp,
  Shield,
  Award,
  Loader2,
  ArrowLeft
} from 'lucide-react'
import { api } from '../utils/api'
import './ListingDetail.css'

function ListingDetail() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    const fetchListing = async () => {
      try {
        const result = await api.getListing(id)
        setData(result)
      } catch (error) {
        console.error('Failed to fetch listing:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchListing()
  }, [id])

  if (loading) {
    return (
      <div className="listing-detail loading">
        <Loader2 className="spinner" size={40} />
        <p>Loading listing details...</p>
      </div>
    )
  }

  if (!data?.listing) {
    return (
      <div className="listing-detail error">
        <h2>Listing not found</h2>
        <Link to="/browse" className="btn btn-primary">
          Browse All Services
        </Link>
      </div>
    )
  }

  const { listing, seller, reviews } = data

  const formatPrice = (price, unit) => {
    if (unit === 'monthly') return `$${price}/month`
    if (unit === 'hourly') return `$${price}/hour`
    return `$${price}`
  }

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'reviews', label: `Reviews (${reviews?.length || 0})` },
    { id: 'seller', label: 'About Seller' },
  ]

  return (
    <div className="listing-detail">
      <div className="container">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <Link to="/browse">
            <ArrowLeft size={16} />
            Back to Browse
          </Link>
          <ChevronRight size={14} />
          <Link to={`/browse?category=${encodeURIComponent(listing.category)}`}>
            {listing.category}
          </Link>
          <ChevronRight size={14} />
          <span>{listing.subcategory}</span>
        </div>

        <div className="listing-layout">
          {/* Main Content */}
          <div className="listing-main">
            {/* Header */}
            <motion.div
              className="listing-header"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="listing-badges">
                <span className="category-badge">{listing.category}</span>
                {listing.metrics?.salesCount > 50 && (
                  <span className="popular-badge">
                    <TrendingUp size={12} /> Popular
                  </span>
                )}
              </div>

              <h1>{listing.title}</h1>

              <div className="listing-meta">
                <div className="rating-display">
                  <Star className="star" size={18} />
                  <span className="rating-value">
                    {listing.metrics?.averageRating?.toFixed(1) || '0.0'}
                  </span>
                  <span className="rating-count">
                    ({listing.metrics?.totalReviews || 0} reviews)
                  </span>
                </div>
                <span className="meta-divider">•</span>
                <span className="sales-count">
                  {listing.metrics?.salesCount || 0} orders
                </span>
              </div>
            </motion.div>

            {/* Image Gallery */}
            <div className="listing-gallery">
              <div className="gallery-main">
                <div className="gallery-placeholder">
                  <span className="category-icon">
                    {getCategoryIcon(listing.category)}
                  </span>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="listing-tabs">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div className="tab-content">
              {activeTab === 'overview' && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="overview-tab"
                >
                  <div className="description-section">
                    <h3>About This Service</h3>
                    <p>{listing.description}</p>
                  </div>

                  {listing.attributes?.features && (
                    <div className="features-section">
                      <h3>What's Included</h3>
                      <ul className="features-list">
                        {listing.attributes.features.map((feature, i) => (
                          <li key={i}>
                            <CheckCircle size={16} />
                            <span>{feature}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {listing.attributes?.specifications && (
                    <div className="specs-section">
                      <h3>Specifications</h3>
                      <dl className="specs-list">
                        {Object.entries(listing.attributes.specifications).map(([key, value]) => (
                          <div key={key} className="spec-item">
                            <dt>{formatSpecKey(key)}</dt>
                            <dd>{Array.isArray(value) ? value.join(', ') : value}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  )}

                  {listing.attributes?.useCases && (
                    <div className="use-cases-section">
                      <h3>Best For</h3>
                      <div className="use-cases-grid">
                        {listing.attributes.useCases.map((useCase, i) => (
                          <span key={i} className="use-case-tag">
                            {useCase}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === 'reviews' && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="reviews-tab"
                >
                  {reviews?.length > 0 ? (
                    <div className="reviews-list">
                      {reviews.map((review) => (
                        <div key={review.id} className="review-card">
                          <div className="review-header">
                            <div className="review-rating">
                              {[...Array(5)].map((_, i) => (
                                <Star
                                  key={i}
                                  size={14}
                                  className={i < review.ratings.overall ? 'filled' : ''}
                                />
                              ))}
                            </div>
                            <span className="review-date">
                              {new Date(review.createdAt).toLocaleDateString()}
                            </span>
                          </div>
                          <h4>{review.title}</h4>
                          <p>{review.content}</p>
                          {review.sentiment?.highlights?.length > 0 && (
                            <div className="review-highlights">
                              {review.sentiment.highlights.map((h, i) => (
                                <span key={i} className="highlight-tag">
                                  ✓ {h}
                                </span>
                              ))}
                            </div>
                          )}
                          <div className="review-helpful">
                            <button>
                              👍 Helpful ({review.helpful})
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-reviews">
                      <MessageCircle size={48} />
                      <h4>No reviews yet</h4>
                      <p>Be the first to review this service</p>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === 'seller' && seller && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="seller-tab"
                >
                  <div className="seller-profile">
                    <img src={seller.avatar} alt={seller.name} className="seller-avatar-lg" />
                    <div className="seller-info">
                      <h3>
                        {seller.name}
                        {seller.verified && <CheckCircle className="verified" size={18} />}
                      </h3>
                      <p className="seller-level">{seller.verificationLevel} Seller</p>
                      <p className="seller-bio">{seller.bio}</p>
                    </div>
                  </div>

                  <div className="seller-stats-grid">
                    <div className="stat-card">
                      <TrendingUp size={20} />
                      <span className="stat-value">{seller.metrics?.totalSales}</span>
                      <span className="stat-label">Total Sales</span>
                    </div>
                    <div className="stat-card">
                      <Star size={20} />
                      <span className="stat-value">{seller.metrics?.averageRating?.toFixed(1)}</span>
                      <span className="stat-label">Rating</span>
                    </div>
                    <div className="stat-card">
                      <MessageCircle size={20} />
                      <span className="stat-value">{Math.round((seller.metrics?.responseRate || 0) * 100)}%</span>
                      <span className="stat-label">Response Rate</span>
                    </div>
                    <div className="stat-card">
                      <Award size={20} />
                      <span className="stat-value">{Math.round((seller.metrics?.repeatClientRate || 0) * 100)}%</span>
                      <span className="stat-label">Repeat Clients</span>
                    </div>
                  </div>

                  {seller.expertise && (
                    <div className="seller-expertise">
                      <h4>Expertise</h4>
                      <div className="skills-list">
                        {seller.expertise.primarySkills?.map((skill) => (
                          <span key={skill} className="skill-tag">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {seller.aiProfile?.strengths && (
                    <div className="seller-strengths">
                      <h4>Strengths</h4>
                      <ul>
                        {seller.aiProfile.strengths.map((strength, i) => (
                          <li key={i}>
                            <CheckCircle size={14} />
                            {strength}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="listing-sidebar">
            <div className="sidebar-card sticky">
              {/* Price */}
              <div className="price-section">
                <span className="price-label">Starting at</span>
                <span className="price-value">
                  {formatPrice(listing.price, listing.priceUnit)}
                </span>
              </div>

              {/* Quick Info */}
              <div className="quick-info">
                <div className="info-item">
                  <Clock size={16} />
                  <span>Delivery: {listing.attributes?.deliveryTime || 'Varies'}</span>
                </div>
                <div className="info-item">
                  <CheckCircle size={16} />
                  <span>{Math.round((listing.metrics?.completionRate || 0) * 100)}% completion rate</span>
                </div>
                <div className="info-item">
                  <MessageCircle size={16} />
                  <span>Response: {listing.metrics?.responseTime || 'Within 24h'}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="sidebar-actions">
                <button className="btn btn-primary btn-lg full-width">
                  Continue
                  <ChevronRight size={18} />
                </button>
                <button className="btn btn-secondary full-width">
                  <MessageCircle size={16} />
                  Contact Seller
                </button>
              </div>

              {/* Secondary Actions */}
              <div className="secondary-actions">
                <button className="icon-btn">
                  <Heart size={18} />
                  Save
                </button>
                <button className="icon-btn">
                  <Share2 size={18} />
                  Share
                </button>
              </div>

              {/* Seller Mini */}
              {seller && (
                <div className="seller-mini">
                  <img src={seller.avatar} alt={seller.name} className="seller-avatar" />
                  <div className="seller-mini-info">
                    <span className="seller-name">
                      {seller.name}
                      {seller.verified && <CheckCircle size={12} />}
                    </span>
                    <span className="seller-meta">
                      <Star size={12} /> {seller.metrics?.averageRating?.toFixed(1)} • {seller.metrics?.totalSales} sales
                    </span>
                  </div>
                </div>
              )}

              {/* Trust Badges */}
              <div className="trust-badges">
                <div className="trust-badge">
                  <Shield size={16} />
                  <span>Secure Payment</span>
                </div>
                <div className="trust-badge">
                  <CheckCircle size={16} />
                  <span>Verified Seller</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
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

function formatSpecKey(key) {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
}

export default ListingDetail

