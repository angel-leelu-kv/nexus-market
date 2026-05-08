import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Menu, X, Sparkles, User, Bell } from 'lucide-react'
import AIStatusBadge from './AIStatusBadge'
import './Navbar.css'

function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const location = useLocation()
  const navigate = useNavigate()

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/browse?q=${encodeURIComponent(searchQuery)}`)
      setSearchQuery('')
    }
  }

  const navLinks = [
    { path: '/', label: 'Home' },
    { path: '/browse', label: 'Browse' },
    { path: '/browse?category=Development', label: 'Development' },
    { path: '/browse?category=Design', label: 'Design' },
  ]

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <div className="logo-icon">
            <Sparkles size={24} />
          </div>
          <span className="logo-text">NexusMarket</span>
        </Link>

        {/* Desktop Nav */}
        <div className="navbar-center">
          <form className="navbar-search" onSubmit={handleSearch}>
            <Search className="search-icon" size={18} />
            <input
              type="text"
              placeholder="Search services or describe what you need..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <kbd className="search-kbd">⌘K</kbd>
          </form>
        </div>

        {/* Desktop Links */}
        <div className="navbar-links">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Actions */}
        <div className="navbar-actions">
          <AIStatusBadge />
          <button className="action-btn">
            <Bell size={20} />
          </button>
          <button className="action-btn user-btn">
            <User size={20} />
          </button>
          <button
            className="mobile-menu-btn"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            className="mobile-menu"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <form className="mobile-search" onSubmit={handleSearch}>
              <Search className="search-icon" size={18} />
              <input
                type="text"
                placeholder="Search services..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </form>
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className="mobile-nav-link"
                onClick={() => setIsMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}

export default Navbar

