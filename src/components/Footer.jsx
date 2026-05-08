import { Link } from 'react-router-dom'
import { Sparkles, Github, Twitter, Linkedin } from 'lucide-react'
import './Footer.css'

function Footer() {
  const currentYear = new Date().getFullYear()

  const footerLinks = {
    marketplace: [
      { label: 'Browse All', path: '/browse' },
      { label: 'Development', path: '/browse?category=Development' },
      { label: 'Design', path: '/browse?category=Design' },
      { label: 'Marketing', path: '/browse?category=Marketing' },
      { label: 'Writing', path: '/browse?category=Writing' },
    ],
    resources: [
      { label: 'How It Works', path: '#' },
      { label: 'AI Matching', path: '#' },
      { label: 'For Sellers', path: '#' },
      { label: 'For Buyers', path: '#' },
    ],
    company: [
      { label: 'About', path: '#' },
      { label: 'Careers', path: '#' },
      { label: 'Blog', path: '#' },
      { label: 'Contact', path: '#' },
    ],
    legal: [
      { label: 'Privacy Policy', path: '#' },
      { label: 'Terms of Service', path: '#' },
      { label: 'Cookie Policy', path: '#' },
    ],
  }

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-top">
          {/* Brand */}
          <div className="footer-brand">
            <Link to="/" className="footer-logo">
              <div className="logo-icon">
                <Sparkles size={20} />
              </div>
              <span>NexusMarket</span>
            </Link>
            <p className="footer-tagline">
              AI-powered marketplace connecting you with the perfect services and talent.
              Describe what you need, and let our intelligent matching do the rest.
            </p>
            <div className="footer-social">
              <a href="#" className="social-link" aria-label="Twitter">
                <Twitter size={18} />
              </a>
              <a href="#" className="social-link" aria-label="GitHub">
                <Github size={18} />
              </a>
              <a href="#" className="social-link" aria-label="LinkedIn">
                <Linkedin size={18} />
              </a>
            </div>
          </div>

          {/* Links */}
          <div className="footer-links-grid">
            <div className="footer-links-column">
              <h4>Marketplace</h4>
              {footerLinks.marketplace.map((link) => (
                <Link key={link.label} to={link.path}>
                  {link.label}
                </Link>
              ))}
            </div>
            <div className="footer-links-column">
              <h4>Resources</h4>
              {footerLinks.resources.map((link) => (
                <Link key={link.label} to={link.path}>
                  {link.label}
                </Link>
              ))}
            </div>
            <div className="footer-links-column">
              <h4>Company</h4>
              {footerLinks.company.map((link) => (
                <Link key={link.label} to={link.path}>
                  {link.label}
                </Link>
              ))}
            </div>
            <div className="footer-links-column">
              <h4>Legal</h4>
              {footerLinks.legal.map((link) => (
                <Link key={link.label} to={link.path}>
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; {currentYear} NexusMarket. All rights reserved.</p>
          <p className="footer-made">
            Made with <span className="heart">♥</span> using AI
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer

