import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  ArrowRight, 
  Sparkles, 
  Code, 
  Palette, 
  TrendingUp, 
  PenTool,
  Film,
  Cpu,
  Shield,
  Zap,
  Users
} from 'lucide-react'
import SearchBar from '../components/SearchBar'
import ListingCard from '../components/ListingCard'
import { api } from '../utils/api'
import './Home.css'

function Home() {
  const [sections, setSections] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [recResponse, catResponse] = await Promise.all([
          api.getHomeRecommendations(),
          api.getCategories(),
        ])
        setSections(recResponse.sections || [])
        setCategories(catResponse.categories || [])
      } catch (error) {
        console.error('Failed to fetch home data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const categoryIcons = {
    'Development': Code,
    'Design': Palette,
    'Marketing': TrendingUp,
    'Writing': PenTool,
    'Video': Film,
    'Data & AI': Cpu,
  }

  const features = [
    {
      icon: Sparkles,
      title: 'AI-Powered Matching',
      description: 'Describe what you need in plain English. Our AI understands context, budget, and preferences to find perfect matches.'
    },
    {
      icon: Shield,
      title: 'Verified Sellers',
      description: 'Every seller is verified with track records you can trust. See real reviews and completion rates.'
    },
    {
      icon: Zap,
      title: 'Smart Comparisons',
      description: 'Compare services side-by-side with AI-generated insights highlighting pros, cons, and best-fit scenarios.'
    },
    {
      icon: Users,
      title: 'Expert Community',
      description: 'Access top-tier talent across development, design, marketing, and more. Quality guaranteed.'
    },
  ]

  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-glow hero-glow-1" />
          <div className="hero-glow hero-glow-2" />
          <div className="hero-grid" />
        </div>

        <div className="container">
          <motion.div
            className="hero-content"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="hero-badge">
              <Sparkles size={14} />
              AI-Powered Discovery
            </span>
            <h1 className="hero-title">
              Find the Perfect Service<br />
              <span className="text-gradient">In Seconds, Not Hours</span>
            </h1>
            <p className="hero-description">
              Skip the endless scrolling. Describe what you need and let our AI 
              match you with vetted professionals who fit your budget, timeline, and requirements.
            </p>
            
            <SearchBar large autoFocus placeholder="What do you need help with today?" />
          </motion.div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="categories-section">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="section-header"
          >
            <h2>Explore Categories</h2>
            <p>Find services across all major categories</p>
          </motion.div>

          <div className="categories-grid">
            {categories.map((category, index) => {
              const Icon = categoryIcons[category.name] || Code
              return (
                <motion.div
                  key={category.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <Link
                    to={`/browse?category=${encodeURIComponent(category.name)}`}
                    className="category-card"
                  >
                    <div className="category-icon">
                      <Icon size={24} />
                    </div>
                    <div className="category-info">
                      <h3>{category.name}</h3>
                      <span>{category.count} services</span>
                    </div>
                    <ArrowRight className="category-arrow" size={18} />
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="section-header"
          >
            <h2>Why NexusMarket?</h2>
            <p>The smarter way to find and hire talent</p>
          </motion.div>

          <div className="features-grid">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="feature-card"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <div className="feature-icon">
                  <feature.icon size={24} />
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Recommendation Sections */}
      {sections.map((section, sectionIndex) => (
        <section key={section.title} className="listings-section">
          <div className="container">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              viewport={{ once: true }}
              className="section-header"
            >
              <h2>{section.title}</h2>
              <Link to="/browse" className="section-link">
                View all <ArrowRight size={16} />
              </Link>
            </motion.div>

            <div className="listings-grid">
              {section.items?.slice(0, 4).map((listing, index) => (
                <ListingCard
                  key={listing.id}
                  listing={listing}
                  index={index}
                />
              ))}
            </div>
          </div>
        </section>
      ))}

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <motion.div
            className="cta-content"
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
          >
            <div className="cta-glow" />
            <h2>Ready to find your perfect match?</h2>
            <p>
              Join thousands of businesses finding top talent through AI-powered recommendations.
            </p>
            <div className="cta-actions">
              <Link to="/browse" className="btn btn-primary btn-lg">
                Browse Services
                <ArrowRight size={18} />
              </Link>
              <button className="btn btn-secondary btn-lg">
                Learn More
              </button>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

export default Home

