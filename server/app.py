"""
================================
AI MARKETPLACE - PYTHON BACKEND
================================

Complete Python backend replacing Node.js server
Includes all API endpoints + AI Agent with tool calling

Run:
    python server/app.py
    or
    uvicorn server.app:app --host 0.0.0.0 --port 3001

Endpoints:
    GET  /api/health           - Health check
    GET  /api/ai-status        - AI status
    GET  /api/listings         - List all listings
    GET  /api/listings/{id}    - Get listing details
    GET  /api/sellers          - List all sellers
    GET  /api/sellers/{id}     - Get seller details
    GET  /api/categories       - Get categories
    GET  /api/home-recommendations - Home page recommendations
    POST /api/agent            - AI agent with tools (body: query or message + optional session_id)
    POST /api/chat             - Chat endpoint
    POST /api/recommend        - AI recommendations
    POST /api/compare          - Compare listings

When MARKETPLACE_API_BEARER_TOKEN is set, all /api/* routes require:
    Authorization: Bearer <that value>
If unset, bearer checks are skipped. OPTIONS preflight is never authenticated.
"""

import copy
import os
import json
import uuid
from netra import Netra, SpanType
from netra.decorators import agent
from netra.instrumentation.instruments import InstrumentSet
from netra.session_manager import SessionManager
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel
from opentelemetry import trace

from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

try:
    from server.prompt_variants import get_system_prompt
except ImportError:
    from prompt_variants import get_system_prompt  # when run as python server/app.py from server/


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s - %(message)s"))
    logger.addHandler(_handler)
SESSION_ID = str(uuid.uuid4())
Netra.set_session_id(SESSION_ID)

load_dotenv()

headers = f"x-api-key={os.getenv('NETRA_API_KEY')}"
Netra.init(
    app_name="NexusMarket",
    disable_batch=True,
    environment="dev",
    headers=headers,
    debug_mode=True,
    root_instruments={InstrumentSet.ALL},
    instruments={InstrumentSet.ALL}
    # block_instruments={InstrumentSet.ALL,InstrumentSet.FASTAPI},

)




from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.requests import Request

# ================================
# CONFIGURATION
# ================================

PORT = int(os.environ.get("PORT", 3001))
AI_MODEL = os.environ.get("AI_MODEL", "gemini-2.0-flash")

# Bearer auth for /api routes when set (Netra Auth tab: same value as this env var)
API_BEARER_TOKEN = (os.environ.get("MARKETPLACE_API_BEARER_TOKEN") or "").strip()

genai_client = genai.Client(
    api_key=os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"),
)

# ================================
# SAMPLE DATA - SELLERS
# ================================

sellers = [
    {
        "id": "seller-001",
        "name": "Alexandra Chen",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=alexandra",
        "bio": "Full-stack developer with 8 years of experience building scalable web applications. Specialized in React, Node.js, and cloud architecture.",
        "expertise": {
            "primarySkills": ["React", "Node.js", "TypeScript", "AWS", "PostgreSQL"],
            "industries": ["SaaS", "E-commerce", "FinTech"],
            "yearsExperience": 8,
            "certifications": ["AWS Solutions Architect", "Google Cloud Professional"],
            "languages": ["English", "Mandarin"],
        },
        "aiProfile": {
            "strengths": ["Excellent code quality", "Fast turnaround", "Clear communication"],
            "specialties": ["Complex web applications", "API design", "Performance optimization"],
            "communicationStyle": "Professional and thorough",
            "reliabilityScore": 0.96,
        },
        "metrics": {
            "totalSales": 247,
            "averageRating": 4.9,
            "responseRate": 0.98,
            "repeatClientRate": 0.42,
            "memberSince": "2020-03-15",
        },
        "verified": True,
        "verificationLevel": "pro",
    },
    {
        "id": "seller-002",
        "name": "Marcus Williams",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=marcus",
        "bio": "Creative brand designer helping startups and established businesses build memorable visual identities.",
        "expertise": {
            "primarySkills": ["Brand Design", "Logo Design", "UI/UX", "Figma", "Illustrator"],
            "industries": ["Startups", "Tech", "Healthcare", "Education"],
            "yearsExperience": 6,
            "certifications": ["Adobe Certified Expert"],
            "languages": ["English", "Spanish"],
        },
        "aiProfile": {
            "strengths": ["Creative concepts", "Quick iterations", "Brand storytelling"],
            "specialties": ["Startup branding", "Logo systems", "Design systems"],
            "communicationStyle": "Creative and collaborative",
            "reliabilityScore": 0.94,
        },
        "metrics": {
            "totalSales": 189,
            "averageRating": 4.8,
            "responseRate": 0.95,
            "repeatClientRate": 0.38,
            "memberSince": "2021-01-20",
        },
        "verified": True,
        "verificationLevel": "pro",
    },
    {
        "id": "seller-003",
        "name": "Sarah Mitchell",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=sarah",
        "bio": "SEO specialist and content strategist helping businesses rank higher and convert better.",
        "expertise": {
            "primarySkills": ["SEO", "Content Strategy", "Google Analytics", "Keyword Research", "Technical SEO"],
            "industries": ["E-commerce", "SaaS", "Local Business"],
            "yearsExperience": 5,
            "certifications": ["Google Analytics Certified", "HubSpot Content Marketing"],
            "languages": ["English"],
        },
        "aiProfile": {
            "strengths": ["Data-driven approach", "Measurable results", "Comprehensive audits"],
            "specialties": ["Technical SEO", "Content optimization", "Local SEO"],
            "communicationStyle": "Analytical and detailed",
            "reliabilityScore": 0.92,
        },
        "metrics": {
            "totalSales": 156,
            "averageRating": 4.7,
            "responseRate": 0.92,
            "repeatClientRate": 0.45,
            "memberSince": "2021-06-10",
        },
        "verified": True,
        "verificationLevel": "basic",
    },
    {
        "id": "seller-004",
        "name": "David Park",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=david",
        "bio": "Mobile app developer specializing in React Native and Flutter. Created apps with 1M+ downloads.",
        "expertise": {
            "primarySkills": ["React Native", "Flutter", "iOS", "Android", "Firebase"],
            "industries": ["Consumer Apps", "HealthTech", "Social"],
            "yearsExperience": 7,
            "certifications": ["Google Flutter Developer", "AWS Mobile"],
            "languages": ["English", "Korean"],
        },
        "aiProfile": {
            "strengths": ["Cross-platform expertise", "Performance optimization", "App Store experience"],
            "specialties": ["Consumer apps", "Social features", "Real-time functionality"],
            "communicationStyle": "Technical and efficient",
            "reliabilityScore": 0.95,
        },
        "metrics": {
            "totalSales": 134,
            "averageRating": 4.9,
            "responseRate": 0.97,
            "repeatClientRate": 0.51,
            "memberSince": "2020-09-01",
        },
        "verified": True,
        "verificationLevel": "pro",
    },
    {
        "id": "seller-005",
        "name": "Emma Rodriguez",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=emma",
        "bio": "Professional copywriter with a knack for converting readers into customers. Former agency lead.",
        "expertise": {
            "primarySkills": ["Copywriting", "Email Marketing", "Landing Pages", "Brand Voice", "A/B Testing"],
            "industries": ["DTC", "SaaS", "Finance", "Health"],
            "yearsExperience": 9,
            "certifications": ["Copyblogger Certified", "ConversionXL"],
            "languages": ["English", "Portuguese"],
        },
        "aiProfile": {
            "strengths": ["Conversion-focused", "Brand voice mastery", "Fast delivery"],
            "specialties": ["Sales pages", "Email sequences", "Website copy"],
            "communicationStyle": "Friendly and persuasive",
            "reliabilityScore": 0.93,
        },
        "metrics": {
            "totalSales": 312,
            "averageRating": 4.8,
            "responseRate": 0.94,
            "repeatClientRate": 0.55,
            "memberSince": "2019-11-15",
        },
        "verified": True,
        "verificationLevel": "enterprise",
    },
    {
        "id": "seller-006",
        "name": "James Thompson",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=james",
        "bio": "Video editor and motion graphics artist. 500+ projects completed for brands worldwide.",
        "expertise": {
            "primarySkills": ["Premiere Pro", "After Effects", "DaVinci Resolve", "Motion Graphics", "Color Grading"],
            "industries": ["YouTube", "Advertising", "Corporate", "Music"],
            "yearsExperience": 10,
            "certifications": ["Adobe Certified Professional"],
            "languages": ["English"],
        },
        "aiProfile": {
            "strengths": ["Fast turnaround", "Cinematic quality", "Creative storytelling"],
            "specialties": ["YouTube content", "Commercial ads", "Music videos"],
            "communicationStyle": "Visual and creative",
            "reliabilityScore": 0.91,
        },
        "metrics": {
            "totalSales": 523,
            "averageRating": 4.6,
            "responseRate": 0.89,
            "repeatClientRate": 0.48,
            "memberSince": "2019-05-20",
        },
        "verified": True,
        "verificationLevel": "pro",
    },
    {
        "id": "seller-007",
        "name": "Lisa Wang",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=lisa",
        "bio": "Data scientist and ML engineer helping companies leverage AI for business insights.",
        "expertise": {
            "primarySkills": ["Python", "TensorFlow", "PyTorch", "Data Analysis", "ML Ops"],
            "industries": ["FinTech", "Healthcare", "Retail", "Manufacturing"],
            "yearsExperience": 6,
            "certifications": ["Google ML Engineer", "AWS ML Specialty"],
            "languages": ["English", "Mandarin"],
        },
        "aiProfile": {
            "strengths": ["Production-ready models", "Clear documentation", "Business insight"],
            "specialties": ["Predictive analytics", "NLP", "Computer vision"],
            "communicationStyle": "Analytical and educational",
            "reliabilityScore": 0.94,
        },
        "metrics": {
            "totalSales": 87,
            "averageRating": 4.9,
            "responseRate": 0.96,
            "repeatClientRate": 0.62,
            "memberSince": "2021-02-28",
        },
        "verified": True,
        "verificationLevel": "pro",
    },
    {
        "id": "seller-008",
        "name": "Michael Brown",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=michael",
        "bio": "WordPress expert with 12+ years experience. Custom themes, plugins, and optimization.",
        "expertise": {
            "primarySkills": ["WordPress", "PHP", "WooCommerce", "Elementor", "Performance"],
            "industries": ["Small Business", "E-commerce", "Blogs", "Agencies"],
            "yearsExperience": 12,
            "certifications": ["WordPress Developer"],
            "languages": ["English", "German"],
        },
        "aiProfile": {
            "strengths": ["Deep WordPress knowledge", "Problem solving", "Affordable rates"],
            "specialties": ["Custom development", "Speed optimization", "Security"],
            "communicationStyle": "Patient and thorough",
            "reliabilityScore": 0.90,
        },
        "metrics": {
            "totalSales": 678,
            "averageRating": 4.5,
            "responseRate": 0.88,
            "repeatClientRate": 0.35,
            "memberSince": "2018-08-10",
        },
        "verified": True,
        "verificationLevel": "basic",
    },
]

# ================================
# SAMPLE DATA - LISTINGS
# ================================

listings = [
    {
        "id": "listing-001",
        "title": "Custom React Web Application Development",
        "description": "I will build a modern, scalable React web application tailored to your business needs. Includes responsive design, API integration, user authentication, and deployment assistance.",
        "category": "Development",
        "subcategory": "Web Development",
        "price": 2500,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["react", "web app", "frontend", "javascript", "custom development"],
            "features": ["Responsive design", "API integration", "User authentication", "Modern UI", "Performance optimized"],
            "deliveryTime": "2-4 weeks",
        },
        "metrics": {"averageRating": 4.9, "totalReviews": 89, "salesCount": 124, "responseTime": "< 1 hour"},
        "sellerId": "seller-001",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-002",
        "title": "Full Stack Node.js API Development",
        "description": "Professional REST or GraphQL API development using Node.js. Includes database design, authentication, documentation, and cloud deployment.",
        "category": "Development",
        "subcategory": "Backend Development",
        "price": 1800,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["nodejs", "api", "backend", "rest", "graphql"],
            "features": ["RESTful or GraphQL", "JWT authentication", "Database integration", "API documentation"],
            "deliveryTime": "1-3 weeks",
        },
        "metrics": {"averageRating": 4.9, "totalReviews": 67, "salesCount": 98, "responseTime": "< 1 hour"},
        "sellerId": "seller-001",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-003",
        "title": "React Native Mobile App Development",
        "description": "Cross-platform mobile app development using React Native. One codebase for iOS and Android with native performance.",
        "category": "Development",
        "subcategory": "Mobile Development",
        "price": 4500,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["react native", "mobile app", "ios", "android", "cross-platform"],
            "features": ["Cross-platform", "Native performance", "Push notifications", "App store submission"],
            "deliveryTime": "4-8 weeks",
        },
        "metrics": {"averageRating": 4.9, "totalReviews": 52, "salesCount": 78, "responseTime": "< 2 hours"},
        "sellerId": "seller-004",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-004",
        "title": "Budget-Friendly WordPress Website",
        "description": "Professional WordPress website setup with a premium theme. Perfect for small businesses, blogs, and portfolios.",
        "category": "Development",
        "subcategory": "Web Development",
        "price": 350,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["wordpress", "website", "small business", "affordable", "blog"],
            "features": ["Premium theme", "Responsive design", "Basic SEO", "Contact forms"],
            "deliveryTime": "3-5 days",
        },
        "metrics": {"averageRating": 4.5, "totalReviews": 234, "salesCount": 456, "responseTime": "< 3 hours"},
        "sellerId": "seller-008",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-005",
        "title": "Complete Brand Identity Design Package",
        "description": "Full brand identity design including logo, color palette, typography, and brand guidelines.",
        "category": "Design",
        "subcategory": "Brand Design",
        "price": 1500,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["branding", "logo", "brand identity", "visual design", "brand guidelines"],
            "features": ["Logo design", "Color palette", "Typography system", "Brand guidelines", "Social media kit"],
            "deliveryTime": "2-3 weeks",
        },
        "metrics": {"averageRating": 4.8, "totalReviews": 76, "salesCount": 112, "responseTime": "< 2 hours"},
        "sellerId": "seller-002",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-006",
        "title": "Professional Logo Design",
        "description": "Custom logo design with multiple concepts and revisions. Modern, memorable logos that work across all applications.",
        "category": "Design",
        "subcategory": "Logo Design",
        "price": 450,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["logo", "logo design", "branding", "startup", "business"],
            "features": ["3 initial concepts", "2 revision rounds", "All file formats", "Color variations"],
            "deliveryTime": "5-7 days",
        },
        "metrics": {"averageRating": 4.8, "totalReviews": 98, "salesCount": 167, "responseTime": "< 1 hour"},
        "sellerId": "seller-002",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-007",
        "title": "Comprehensive SEO Audit & Strategy",
        "description": "In-depth SEO audit with actionable recommendations. Includes technical SEO analysis, keyword research, and 90-day action plan.",
        "category": "Marketing",
        "subcategory": "SEO",
        "price": 800,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["seo", "seo audit", "keyword research", "technical seo", "rankings"],
            "features": ["Technical audit", "Keyword research", "Competitor analysis", "90-day plan"],
            "deliveryTime": "5-7 days",
        },
        "metrics": {"averageRating": 4.7, "totalReviews": 65, "salesCount": 89, "responseTime": "< 4 hours"},
        "sellerId": "seller-003",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-008",
        "title": "Monthly SEO Management",
        "description": "Ongoing SEO management service. Monthly optimizations, content recommendations, link building, and performance reporting.",
        "category": "Marketing",
        "subcategory": "SEO",
        "price": 1200,
        "priceUnit": "monthly",
        "currency": "USD",
        "attributes": {
            "tags": ["seo", "monthly seo", "link building", "content optimization"],
            "features": ["Monthly optimizations", "Content strategy", "Link building", "Performance reports"],
            "deliveryTime": "Ongoing",
        },
        "metrics": {"averageRating": 4.7, "totalReviews": 43, "salesCount": 56, "responseTime": "< 4 hours"},
        "sellerId": "seller-003",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-009",
        "title": "High-Converting Website Copywriting",
        "description": "Persuasive website copy that converts visitors into customers. Research-backed, SEO-friendly copy.",
        "category": "Writing",
        "subcategory": "Copywriting",
        "price": 950,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["copywriting", "website copy", "conversion", "sales copy", "seo copywriting"],
            "features": ["5-page website", "SEO optimized", "Conversion focused", "Brand voice"],
            "deliveryTime": "7-10 days",
        },
        "metrics": {"averageRating": 4.8, "totalReviews": 123, "salesCount": 198, "responseTime": "< 2 hours"},
        "sellerId": "seller-005",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-010",
        "title": "Email Marketing Sequence",
        "description": "Strategic email sequence design and copywriting. Welcome sequences, nurture campaigns, or sales funnels.",
        "category": "Writing",
        "subcategory": "Email Marketing",
        "price": 650,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["email", "email marketing", "email sequence", "nurture", "sales funnel"],
            "features": ["5-email sequence", "Subject lines", "CTAs", "Personalization"],
            "deliveryTime": "5-7 days",
        },
        "metrics": {"averageRating": 4.9, "totalReviews": 87, "salesCount": 145, "responseTime": "< 2 hours"},
        "sellerId": "seller-005",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-011",
        "title": "Professional YouTube Video Editing",
        "description": "High-quality video editing for YouTube creators. Includes cuts, transitions, color grading, and sound design.",
        "category": "Video",
        "subcategory": "Video Editing",
        "price": 200,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["video editing", "youtube", "video production", "content creator"],
            "features": ["Professional cuts", "Color grading", "Sound design", "Graphics/text", "Thumbnail"],
            "deliveryTime": "3-5 days",
        },
        "metrics": {"averageRating": 4.6, "totalReviews": 187, "salesCount": 289, "responseTime": "< 3 hours"},
        "sellerId": "seller-006",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-012",
        "title": "Motion Graphics & Animation",
        "description": "Custom motion graphics and animations for your brand. Logo animations, explainer videos, social media content.",
        "category": "Video",
        "subcategory": "Motion Graphics",
        "price": 800,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["motion graphics", "animation", "logo animation", "explainer", "after effects"],
            "features": ["Custom animation", "Sound design", "Multiple formats", "Source files"],
            "deliveryTime": "7-10 days",
        },
        "metrics": {"averageRating": 4.7, "totalReviews": 78, "salesCount": 123, "responseTime": "< 4 hours"},
        "sellerId": "seller-006",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-013",
        "title": "Custom Machine Learning Model Development",
        "description": "End-to-end ML model development for your business. Predictive analytics, NLP, and computer vision.",
        "category": "Data & AI",
        "subcategory": "Machine Learning",
        "price": 5000,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["machine learning", "ai", "ml model", "predictive analytics", "data science"],
            "features": ["Custom model", "Data pipeline", "Model training", "Deployment support", "Documentation"],
            "deliveryTime": "4-8 weeks",
        },
        "metrics": {"averageRating": 4.9, "totalReviews": 34, "salesCount": 45, "responseTime": "< 4 hours"},
        "sellerId": "seller-007",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-014",
        "title": "Data Analysis & Visualization Dashboard",
        "description": "Transform your data into actionable insights. Custom dashboards and analysis using Python and visualization tools.",
        "category": "Data & AI",
        "subcategory": "Data Analysis",
        "price": 1500,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["data analysis", "dashboard", "visualization", "business intelligence"],
            "features": ["Data cleaning", "Analysis", "Interactive dashboard", "Insights report"],
            "deliveryTime": "1-2 weeks",
        },
        "metrics": {"averageRating": 4.8, "totalReviews": 56, "salesCount": 78, "responseTime": "< 3 hours"},
        "sellerId": "seller-007",
        "status": "active",
        "availability": True,
    },
    {
        "id": "listing-015",
        "title": "Quick Logo Design - 24 Hour Delivery",
        "description": "Fast, professional logo design with 24-hour turnaround. Perfect for startups needing quality design quickly.",
        "category": "Design",
        "subcategory": "Logo Design",
        "price": 150,
        "priceUnit": "fixed",
        "currency": "USD",
        "attributes": {
            "tags": ["logo", "fast", "quick", "affordable", "startup"],
            "features": ["2 concepts", "1 revision", "Standard formats", "24-hour delivery"],
            "deliveryTime": "24 hours",
        },
        "metrics": {"averageRating": 4.3, "totalReviews": 312, "salesCount": 567, "responseTime": "< 1 hour"},
        "sellerId": "seller-002",
        "status": "active",
        "availability": True,
    },
]

# ================================
# SAMPLE DATA - REVIEWS
# ================================

reviews = [
    {
        "id": "review-001",
        "listingId": "listing-001",
        "sellerId": "seller-001",
        "ratings": {"overall": 5, "quality": 5, "communication": 5, "value": 5},
        "title": "Exceptional work on our dashboard",
        "content": "Alexandra delivered beyond expectations. The React app is clean, well-documented, and performs flawlessly.",
        "verified": True,
        "helpful": 24,
        "createdAt": "2024-01-05",
    },
    {
        "id": "review-002",
        "listingId": "listing-005",
        "sellerId": "seller-002",
        "ratings": {"overall": 5, "quality": 5, "communication": 5, "value": 5},
        "title": "Our brand finally has an identity",
        "content": "Marcus understood our vision perfectly. The brand package is cohesive, modern, and exactly what we needed.",
        "verified": True,
        "helpful": 15,
        "createdAt": "2024-01-02",
    },
    {
        "id": "review-003",
        "listingId": "listing-009",
        "sellerId": "seller-005",
        "ratings": {"overall": 5, "quality": 5, "communication": 5, "value": 5},
        "title": "Copy that converts!",
        "content": "Emma rewrote our homepage and we saw a 40% increase in conversions within a month.",
        "verified": True,
        "helpful": 45,
        "createdAt": "2023-12-15",
    },
]

# ================================
# USER DATA STORES (in-memory; keyed by session_id)
# ================================

SHORTLIST_STORE: Dict[str, List[str]] = {}  # session_id -> list of listing_ids
ALERTS_STORE: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> list of {id, category?, max_price?, seller_id?}
INQUIRIES_STORE: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> list of {id, listing_id, message, deadline, budget, created_at}
SUPPORT_TICKETS_STORE: Dict[str, List[Dict[str, Any]]] = {}  # session_id -> list of {id, type, message, order_id?, status, created_at}
USER_REVIEWS_STORE: List[Dict[str, Any]] = []  # all submitted reviews (append-only)
REFERRAL_LINKS_STORE: Dict[str, str] = {}  # session_id -> referral_link

# FAQ / help content for get_help tool
HELP_TOPICS: Dict[str, str] = {
    "how it works": "NexusMarket is a freelance services marketplace. Browse or search listings, compare options, and send an inquiry to start a project. Sellers respond with a proposal and timeline. You pay when you're happy with the work.",
    "payment": "Payments are held securely until you approve the delivered work. We support major cards and PayPal. Refunds follow our satisfaction guarantee policy.",
    "refund": "If the delivered work doesn't meet the agreed scope, you can request revisions or a refund through our resolution center. See our Refund Policy for details.",
    "hire": "To hire: 1) Find a listing you like, 2) Use 'Create inquiry' or message the seller with your requirements and budget, 3) Accept their proposal and pay to start.",
    "seller": "Sellers are freelancers and agencies. Each has a profile with skills, reviews, and ratings. You can compare multiple sellers before deciding.",
    "default": "I can help you search listings, compare services, get recommendations, save items to a shortlist, create project inquiries, leave reviews, set alerts, get marketplace insights, and answer questions about how NexusMarket works. What would you like to do?",
}

# ================================
# AI TOOL DEFINITIONS
# ================================

MARKETPLACE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_listings",
            "description": "Search for service listings in the marketplace",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "category": {"type": "string", "description": "Category filter"},
                    "max_price": {"type": "number", "description": "Maximum price"},
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_listing_details",
            "description": "Get details of a specific listing",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {"type": "string", "description": "Listing ID"}
                },
                "required": ["listing_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_listings",
            "description": "Compare multiple listings",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of listing IDs to compare"
                    }
                },
                "required": ["listing_ids"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": "Get personalized recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "need": {"type": "string", "description": "What the user needs"},
                    "budget": {"type": "string", "description": "Budget level: low/medium/high"}
                },
                "required": ["need"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_shortlist",
            "description": "Save a listing to the user's shortlist for later",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {"type": "string", "description": "Listing ID to save"}
                },
                "required": ["listing_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_shortlist",
            "description": "Get the user's saved shortlist of listings",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_shortlist",
            "description": "Remove a listing from the user's shortlist",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {"type": "string", "description": "Listing ID to remove"}
                },
                "required": ["listing_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_help",
            "description": "Get help or FAQ answer about NexusMarket (how it works, payment, refund, hire, seller)",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic: how it works, payment, refund, hire, seller, or leave empty for overview"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_review",
            "description": "Submit a review for a listing after purchase",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {"type": "string", "description": "Listing ID reviewed"},
                    "rating": {"type": "integer", "description": "Overall rating 1-5"},
                    "title": {"type": "string", "description": "Short review title"},
                    "content": {"type": "string", "description": "Review text"}
                },
                "required": ["listing_id", "rating", "title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_inquiry",
            "description": "Create a project inquiry to send to a seller (express interest and share requirements)",
            "parameters": {
                "type": "object",
                "properties": {
                    "listing_id": {"type": "string", "description": "Listing ID to inquire about"},
                    "message": {"type": "string", "description": "Your message to the seller"},
                    "deadline": {"type": "string", "description": "When you need it by (e.g. next week)"},
                    "budget": {"type": "string", "description": "Your budget (e.g. 500, under 1000)"}
                },
                "required": ["listing_id", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_budget_split",
            "description": "Suggest how to split a total budget across project goals (e.g. logo, website, copy)",
            "parameters": {
                "type": "object",
                "properties": {
                    "total_budget": {"type": "number", "description": "Total budget in dollars"},
                    "goals": {"type": "string", "description": "Comma-separated goals e.g. logo, website, social kit"}
                },
                "required": ["total_budget", "goals"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_marketplace_insights",
            "description": "Get marketplace insights for sellers: top categories, demand, pricing tips",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Optional category to get insights for"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_alert",
            "description": "Create an alert to be notified when new listings match (e.g. category, max price, or seller)",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Category to watch"},
                    "max_price": {"type": "number", "description": "Max price filter"},
                    "seller_id": {"type": "string", "description": "Notify when this seller has new listings"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_alerts",
            "description": "Get the user's active alerts",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_alert",
            "description": "Delete one of the user's alerts",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_id": {"type": "string", "description": "Alert ID to remove"}
                },
                "required": ["alert_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support ticket for an order issue or report",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_type": {"type": "string", "description": "Type: order_issue, report_seller, payment, other"},
                    "message": {"type": "string", "description": "Description of the issue"},
                    "order_id": {"type": "string", "description": "Related order ID if applicable"}
                },
                "required": ["ticket_type", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_support_status",
            "description": "Check status of the user's support tickets",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "Specific ticket ID, or omit for all"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_referral_info",
            "description": "Get info about the referral program (invite friends, rewards)",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_referral_link",
            "description": "Create a referral link for the user to share",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

# GenAI tools: one Tool with all function declarations (for generate_content)
GENAI_TOOLS = [
    genai_types.Tool(
        function_declarations=[
            genai_types.FunctionDeclaration(
                name=t["function"]["name"],
                description=t["function"].get("description", ""),
                parameters_json_schema=t["function"]["parameters"],
            )
            for t in MARKETPLACE_TOOLS
        ]
    )
]

# ================================
# TOOL EXECUTION
# ================================

def execute_tool(tool_name: str, args: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute a marketplace tool and return results. session_id required for user-specific tools."""
    print(f"   🔧 Tool: {tool_name} | Args: {args}")
    
    # Wrap tool execution in a Netra span so it appears in traces
    with Netra.start_span(f"tool.{tool_name}", as_type=SpanType.TOOL):
        if tool_name == "search_listings":
            return tool_search_listings(args)
        elif tool_name == "get_listing_details":
            return tool_get_listing_details(args)
        elif tool_name == "compare_listings":
            return tool_compare_listings(args)
        elif tool_name == "get_recommendations":
            return tool_get_recommendations(args)
        elif tool_name == "add_to_shortlist":
            return tool_add_to_shortlist(args, session_id)
        elif tool_name == "get_my_shortlist":
            return tool_get_my_shortlist(session_id)
        elif tool_name == "remove_from_shortlist":
            return tool_remove_from_shortlist(args, session_id)
        elif tool_name == "get_help":
            return tool_get_help(args)
        elif tool_name == "submit_review":
            return tool_submit_review(args)
        elif tool_name == "create_inquiry":
            return tool_create_inquiry(args, session_id)
        elif tool_name == "suggest_budget_split":
            return tool_suggest_budget_split(args)
        elif tool_name == "get_marketplace_insights":
            return tool_get_marketplace_insights(args)
        elif tool_name == "create_alert":
            return tool_create_alert(args, session_id)
        elif tool_name == "get_my_alerts":
            return tool_get_my_alerts(session_id)
        elif tool_name == "delete_alert":
            return tool_delete_alert(args, session_id)
        elif tool_name == "create_support_ticket":
            return tool_create_support_ticket(args, session_id)
        elif tool_name == "get_support_status":
            return tool_get_support_status(args, session_id)
        elif tool_name == "get_referral_info":
            return tool_get_referral_info()
        elif tool_name == "create_referral_link":
            return tool_create_referral_link(session_id)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

from netra.decorators import task

@task(name="tool_search_listings")
def tool_search_listings(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get("query", "").lower()
    category = args.get("category")
    max_price = args.get("max_price")
    
    results = listings.copy()
    
    if category:
        results = [l for l in results if l["category"].lower() == category.lower()]
    
    if max_price:
        results = [l for l in results if l["price"] <= max_price]
    
    # Score by relevance
    scored = []
    for listing in results:
        text = f"{listing['title']} {listing['category']} {listing.get('description', '')}".lower()
        score = sum(1 for word in query.split() if word in text)
        scored.append({**listing, "score": score})
    
    scored.sort(key=lambda x: (-x["score"], -x["metrics"]["averageRating"]))
    
    return {"query": query, "results": scored[:5], "total": len(scored)}

@task(name="tool_get_listing_details")
def tool_get_listing_details(args: Dict[str, Any]) -> Dict[str, Any]:
    listing_id = args.get("listing_id")
    listing = next((l for l in listings if l["id"] == listing_id), None)
    
    if not listing:
        return {"error": f"Listing not found: {listing_id}"}
    
    seller = next((s for s in sellers if s["id"] == listing["sellerId"]), None)
    listing_reviews = [r for r in reviews + USER_REVIEWS_STORE if r.get("listingId") == listing_id]
    return {**listing, "seller": seller, "reviews": listing_reviews}

@task(name="tool_compare_listings")
def tool_compare_listings(args: Dict[str, Any]) -> Dict[str, Any]:
    listing_ids = args.get("listing_ids", [])
    found = [l for l in listings if l["id"] in listing_ids]
    
    if len(found) < 2:
        return {"error": "Need at least 2 listings to compare"}
    
    cheapest = min(found, key=lambda x: x["price"])
    best_rated = max(found, key=lambda x: x["metrics"]["averageRating"])
    
    return {
        "listings": found,
        "analysis": {
            "cheapest": {"id": cheapest["id"], "title": cheapest["title"], "price": cheapest["price"]},
            "best_rated": {"id": best_rated["id"], "title": best_rated["title"], "rating": best_rated["metrics"]["averageRating"]}
        }
    }

@task(name="tool_get_recommendations")
def tool_get_recommendations(args: Dict[str, Any]) -> Dict[str, Any]:
    need = args.get("need", "").lower()
    budget = args.get("budget", "any")
    
    results = listings.copy()
    
    if budget == "low":
        results = [l for l in results if l["price"] < 500]
    elif budget == "medium":
        results = [l for l in results if 500 <= l["price"] < 2000]
    elif budget == "high":
        results = [l for l in results if l["price"] >= 2000]
    
    scored = []
    for listing in results:
        text = f"{listing['title']} {listing['category']}".lower()
        score = sum(1 for word in need.split() if word in text)
        scored.append({**listing, "relevance": score})
    
    scored.sort(key=lambda x: (-x["relevance"], -x["metrics"]["averageRating"]))
    
    return {"need": need, "budget": budget, "recommendations": scored[:4]}


# ---------- Shortlist ----------
@task(name="tool_add_to_shortlist")
def tool_add_to_shortlist(args: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"error": "Session required. Please continue the conversation."}
    listing_id = args.get("listing_id")
    if not listing_id or next((l for l in listings if l["id"] == listing_id), None) is None:
        return {"error": "Invalid or unknown listing_id"}
    SHORTLIST_STORE.setdefault(session_id, [])
    if listing_id not in SHORTLIST_STORE[session_id]:
        SHORTLIST_STORE[session_id].append(listing_id)
    return {"success": True, "message": f"Added listing {listing_id} to your shortlist.", "shortlist": SHORTLIST_STORE[session_id]}


@task(name="tool_get_my_shortlist")
def tool_get_my_shortlist(session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"error": "Session required.", "shortlist": []}
    ids = SHORTLIST_STORE.get(session_id, [])
    items = [next((l for l in listings if l["id"] == lid), None) for lid in ids]
    items = [l for l in items if l is not None]
    return {"shortlist": items, "count": len(items)}


@task(name="tool_remove_from_shortlist")
def tool_remove_from_shortlist(args: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"error": "Session required."}
    listing_id = args.get("listing_id")
    SHORTLIST_STORE.setdefault(session_id, [])
    if listing_id in SHORTLIST_STORE[session_id]:
        SHORTLIST_STORE[session_id].remove(listing_id)
    return {"success": True, "message": f"Removed from shortlist.", "shortlist": SHORTLIST_STORE[session_id]}


# ---------- Help / FAQ ----------
@task(name="tool_get_help")
def tool_get_help(args: Dict[str, Any]) -> Dict[str, Any]:
    topic = (args.get("topic") or "default").strip().lower()
    answer = HELP_TOPICS.get(topic) or HELP_TOPICS.get("default")
    return {"topic": topic, "answer": answer, "topics_available": list(HELP_TOPICS.keys())}


# ---------- Submit review ----------
@task(name="tool_submit_review")
def tool_submit_review(args: Dict[str, Any]) -> Dict[str, Any]:
    listing_id = args.get("listing_id")
    listing = next((l for l in listings if l["id"] == listing_id), None)
    if not listing:
        return {"error": f"Listing not found: {listing_id}"}
    rating = max(1, min(5, int(args.get("rating", 5))))
    title = (args.get("title") or "Great experience")[:200]
    content = (args.get("content") or "")[:2000]
    seller_id = listing["sellerId"]
    review_id = f"review-{len(reviews) + len(USER_REVIEWS_STORE) + 1}"
    review = {
        "id": review_id,
        "listingId": listing_id,
        "sellerId": seller_id,
        "ratings": {"overall": rating, "quality": rating, "communication": rating, "value": rating},
        "title": title,
        "content": content,
        "verified": False,
        "helpful": 0,
        "createdAt": "2024-02-04",
    }
    USER_REVIEWS_STORE.append(review)
    return {"success": True, "message": "Thank you! Your review has been submitted.", "review_id": review_id}


# ---------- Inquiry ----------
@task(name="tool_create_inquiry")
def tool_create_inquiry(args: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"error": "Session required."}
    listing_id = args.get("listing_id")
    listing = next((l for l in listings if l["id"] == listing_id), None)
    if not listing:
        return {"error": f"Listing not found: {listing_id}"}
    message = (args.get("message") or "")[:2000]
    deadline = (args.get("deadline") or "Flexible")[:200]
    budget = (args.get("budget") or "To be discussed")[:200]
    inquiry_id = f"inq-{session_id[:8]}-{len(INQUIRIES_STORE.get(session_id, [])) + 1}"
    inquiry = {"id": inquiry_id, "listing_id": listing_id, "listing_title": listing.get("title"), "message": message, "deadline": deadline, "budget": budget, "status": "sent", "created_at": "2024-02-04"}
    INQUIRIES_STORE.setdefault(session_id, []).append(inquiry)
    return {"success": True, "message": "Your inquiry has been sent to the seller.", "inquiry_id": inquiry_id}


# ---------- Budget planner ----------
@task(name="tool_suggest_budget_split")
def tool_suggest_budget_split(args: Dict[str, Any]) -> Dict[str, Any]:
    total = max(0, float(args.get("total_budget", 0)))
    goals_str = (args.get("goals") or "project").strip()
    goals = [g.strip() for g in goals_str.split(",") if g.strip()] or ["project"]
    n = len(goals)
    share = total / n if n else 0
    split = [{"goal": g, "suggested_budget": round(share, 2)} for g in goals]
    return {"total_budget": total, "goals": goals, "split": split, "message": f"Suggested split for ${total} across {n} goal(s). Use search or get_recommendations per goal."}


# ---------- Marketplace insights (seller tips) ----------
@task(name="tool_get_marketplace_insights")
def tool_get_marketplace_insights(args: Dict[str, Any]) -> Dict[str, Any]:
    category = (args.get("category") or "").strip()
    categories = list(set(l["category"] for l in listings))
    by_cat = {c: [l for l in listings if l["category"] == c] for c in categories}
    insights = []
    for c in categories:
        items = by_cat[c]
        if category and c.lower() != category.lower():
            continue
        avg_price = sum(l["price"] for l in items) / len(items) if items else 0
        avg_rating = sum(l["metrics"]["averageRating"] for l in items) / len(items) if items else 0
        insights.append({"category": c, "listing_count": len(items), "avg_price": round(avg_price, 2), "avg_rating": round(avg_rating, 2)})
    tip = "Listings with clear titles and 4.5+ ratings get more inquiries. Consider offering a 'starter' package at a lower price point."
    return {"insights": insights, "tip": tip, "categories": categories}


# ---------- Alerts ----------
@task(name="tool_create_alert")
def tool_create_alert(args: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"error": "Session required."}
    alert_id = f"alert-{session_id[:8]}-{len(ALERTS_STORE.get(session_id, [])) + 1}"
    alert = {"id": alert_id, "category": args.get("category"), "max_price": args.get("max_price"), "seller_id": args.get("seller_id")}
    ALERTS_STORE.setdefault(session_id, []).append(alert)
    return {"success": True, "message": "Alert created. We'll notify you when there's a match.", "alert_id": alert_id}


@task(name="tool_get_my_alerts")
def tool_get_my_alerts(session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"alerts": []}
    return {"alerts": ALERTS_STORE.get(session_id, [])}


@task(name="tool_delete_alert")
def tool_delete_alert(args: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"error": "Session required."}
    alert_id = args.get("alert_id")
    alerts = ALERTS_STORE.get(session_id, [])
    ALERTS_STORE[session_id] = [a for a in alerts if a.get("id") != alert_id]
    return {"success": True, "message": "Alert removed.", "alerts": ALERTS_STORE[session_id]}


# ---------- Support ----------
@task(name="tool_create_support_ticket")
def tool_create_support_ticket(args: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"error": "Session required."}
    ticket_type = (args.get("ticket_type") or "other")[:50]
    message = (args.get("message") or "")[:2000]
    order_id = args.get("order_id")
    ticket_id = f"ticket-{session_id[:8]}-{len(SUPPORT_TICKETS_STORE.get(session_id, [])) + 1}"
    ticket = {"id": ticket_id, "type": ticket_type, "message": message, "order_id": order_id, "status": "open", "created_at": "2024-02-04"}
    SUPPORT_TICKETS_STORE.setdefault(session_id, []).append(ticket)
    return {"success": True, "message": "Support ticket created. We'll get back to you soon.", "ticket_id": ticket_id}


@task(name="tool_get_support_status")
def tool_get_support_status(args: Dict[str, Any], session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return {"tickets": []}
    tickets = SUPPORT_TICKETS_STORE.get(session_id, [])
    ticket_id = args.get("ticket_id")
    if ticket_id:
        tickets = [t for t in tickets if t.get("id") == ticket_id]
    return {"tickets": tickets}


# ---------- Referral ----------
@task(name="tool_get_referral_info")
def tool_get_referral_info() -> Dict[str, Any]:
    return {"message": "Invite friends to NexusMarket! You get 10% credit when they complete their first order, and they get 10% off. No limit on referrals."}


@task(name="tool_create_referral_link")
def tool_create_referral_link(session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        session_id = str(uuid.uuid4())
    link = f"https://nexusmarket.demo/invite?ref={session_id[:12]}"
    REFERRAL_LINKS_STORE[session_id] = link
    return {"success": True, "referral_link": link, "message": "Share this link with friends."}


# ================================
# CONVERSATION MEMORY
# ================================
# In-memory store: session_id -> list of message dicts (user/assistant/tool only, no system)
# Capped to avoid unbounded growth and token limits.
CONVERSATION_STORE: Dict[str, List[Dict[str, Any]]] = {}
MAX_HISTORY_MESSAGES = 50


def _openai_messages_to_genai(messages: List[Dict[str, Any]]) -> tuple[Optional[str], List]:
    """Convert OpenAI-style messages to (system_instruction, list of GenAI Content)."""
    system_instruction = None
    contents = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            system_instruction = m.get("content") or ""
            continue
        if role == "user":
            contents.append(
                genai_types.Content(
                    role="user",
                    parts=[genai_types.Part.from_text(text=(m.get("content") or ""))],
                )
            )
            continue
        if role == "assistant":
            tool_calls = m.get("tool_calls")
            if tool_calls:
                parts = [
                    genai_types.Part.from_function_call(
                        name=tc["function"]["name"],
                        args=json.loads(tc["function"].get("arguments") or "{}"),
                    )
                    for tc in tool_calls
                ]
                if m.get("content"):
                    parts.insert(0, genai_types.Part.from_text(text=m["content"]))
                contents.append(genai_types.Content(role="model", parts=parts))
            else:
                contents.append(
                    genai_types.Content(
                        role="model",
                        parts=[genai_types.Part.from_text(text=(m.get("content") or ""))],
                    )
                )
            continue
        if role == "tool":
            try:
                response = json.loads(m.get("content") or "{}")
            except json.JSONDecodeError:
                response = {"result": m.get("content", "")}
            contents.append(
                genai_types.Content(
                    role="tool",
                    parts=[
                        genai_types.Part.from_function_response(
                            name=m.get("name", ""),
                            response=response,
                        )
                    ],
                )
            )
    return system_instruction, contents


def _messages_to_store(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a deep copy of messages for storage/replay (JSON-serializable)."""
    return copy.deepcopy(messages)


# ================================
# AI AGENT
# ================================

@agent(name="NexusMarket")
def marketplace_agent(
    query: str,
    context: Optional[Dict] = None,
    previous_messages: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Main AI Agent with tool calling and optional conversation history."""
    session_id = (context or {}).get("session_id") or str(uuid.uuid4())
    prompt_variant = os.environ.get("AGENT_PROMPT_VARIANT", "default")
    # system_prompt = get_system_prompt(prompt_variant)
    result = Netra.prompts.get_prompt(name="PROMPT_DEFAULT").get("messages")
    system_prompt = result[0].get("content")

    # Build messages: system + previous conversation + current user message
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if previous_messages:
        messages.extend(previous_messages)
    messages.append({"role": "user", "content": query})
    
    # Index of first message from this turn (user message); used to extract new_messages later
    start_index_this_turn = len(messages) - 1

    tools_used = []
    final_response = "I couldn't process your request. Please try again."

    # Agent loop (GenAI with manual tool handling)
    for iteration in range(5):
        system_instruction, genai_contents = _openai_messages_to_genai(messages)
        response = genai_client.models.generate_content(
            model=AI_MODEL,
            contents=genai_contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_instruction or "",
                tools=GENAI_TOOLS,
                temperature=0.7,
                max_output_tokens=65536,
                automatic_function_calling=genai_types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        # Support both response.function_calls and candidates[0].content.parts
        function_calls = list(getattr(response, "function_calls", None) or [])
        if not function_calls and response.candidates:
            for part in (response.candidates[0].content.parts or []):
                fc = getattr(part, "function_call", None)
                if fc is not None:
                    function_calls.append(part)

        if function_calls:
            # Build assistant message in OpenAI format for conversation store
            assistant_msg = {
                "role": "assistant",
                "content": (response.text or "") if response else "",
                "tool_calls": [],
            }
            for fc in function_calls:
                fc_id = getattr(fc, "id", None) or str(uuid.uuid4())
                fc_name = getattr(fc, "name", None) or (getattr(fc, "function_call", None) and getattr(fc.function_call, "name", None)) or ""
                fc_args = {}
                if hasattr(fc, "function_call") and fc.function_call is not None:
                    fc_args = getattr(fc.function_call, "args", None) or {}
                elif hasattr(fc, "args"):
                    fc_args = fc.args or {}
                assistant_msg["tool_calls"].append({
                    "id": fc_id,
                    "type": "function",
                    "function": {"name": fc_name, "arguments": json.dumps(fc_args)},
                })
            messages.append(assistant_msg)

            for fc in function_calls:
                fc_id = getattr(fc, "id", None) or str(uuid.uuid4())
                fc_name = getattr(fc, "name", None) or (getattr(fc, "function_call", None) and getattr(fc.function_call, "name", None)) or ""
                fc_args = {}
                if hasattr(fc, "function_call") and fc.function_call is not None:
                    fc_args = getattr(fc.function_call, "args", None) or {}
                elif hasattr(fc, "args"):
                    fc_args = fc.args or {}
                result = execute_tool(fc_name, fc_args, session_id=session_id)
                tools_used.append(fc_name)
                messages.append({
                    "role": "tool",
                    "tool_call_id": fc_id,
                    "name": fc_name,
                    "content": json.dumps(result),
                })
            continue

        final_response = (response.text or final_response) if response else final_response
        break

    Netra.set_root_input(str(query))
    Netra.set_root_output(str(final_response))

    # Add tools_used as a span attribute so it appears in Netra metadata
    # Try multiple methods to get the current span
    current_span = None
    try:
        current_span = SessionManager.get_current_span()
    except Exception:
        try:
            current_span = trace.get_current_span()
        except Exception:
            pass
    
    if current_span and current_span.is_recording():
        # Set tools_used as both JSON string and individual attributes
        current_span.set_attribute("netra.tools_used", json.dumps(tools_used))
        current_span.set_attribute("netra.tools_count", str(len(tools_used)))
        # Also set as entity attribute to match the pattern
        if tools_used:
            current_span.set_attribute("netra.entity.tools_used", json.dumps(tools_used))
            for i, tool in enumerate(tools_used):
                current_span.set_attribute(f"netra.tool.{i}.name", tool)

    # Messages added this turn (user + assistant + tool) for conversation memory
    new_messages = _messages_to_store(messages[start_index_this_turn:])

    return {
        "response": final_response,
        "tools_used": tools_used,
        "session_id": session_id,
        "ai_powered": True,
        "new_messages": new_messages,
    }


# ================================
# REQUEST/RESPONSE MODELS
# ================================

class AgentRequest(BaseModel):
    """Body for POST /api/agent. Use `query` or `message` (Netra/Cursor agent webhooks often send `message`)."""
    query: Optional[str] = None
    message: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None  # omit to start new conversation; send to continue

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}
    session_id: Optional[str] = None  # omit to start new conversation; send to continue

class RecommendRequest(BaseModel):
    query: str

class CompareRequest(BaseModel):
    listingIds: List[str]
    query: Optional[str] = ""

# ================================
# FASTAPI APP
# ================================

app = FastAPI(title="AI Marketplace API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def bearer_auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)
    path = request.url.path
    if path.startswith("/api") and API_BEARER_TOKEN:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )
        token = auth_header.removeprefix("Bearer ").strip()
        if token != API_BEARER_TOKEN:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    return await call_next(request)


# ---------- Health & Status ----------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "ai_agent": {"status": "ok", "model": AI_MODEL},
        "data": {"listings": len(listings), "sellers": len(sellers)}
    }


@app.get("/api/ai-status")
def ai_status():
    return {
        "configured": True,
        "model": AI_MODEL,
        "tools": [t["function"]["name"] for t in MARKETPLACE_TOOLS],
        "provider": "Google GenAI",
    }


# ---------- Data Endpoints ----------

@app.get("/api/listings")
def get_listings(
    category: Optional[str] = Query(None),
    minPrice: Optional[float] = Query(None, alias="minPrice"),
    maxPrice: Optional[float] = Query(None, alias="maxPrice"),
    sort: Optional[str] = Query(None),
    search: Optional[str] = Query("")
):
    result = listings.copy()
    
    if category:
        result = [l for l in result if l["category"].lower() == category.lower()]
    if minPrice:
        result = [l for l in result if l["price"] >= minPrice]
    if maxPrice:
        result = [l for l in result if l["price"] <= maxPrice]
    if search:
        search_lower = search.lower()
        result = [l for l in result if search_lower in l["title"].lower() or search_lower in l.get("description", "").lower()]
    
    if sort == "price_asc":
        result.sort(key=lambda x: x["price"])
    elif sort == "price_desc":
        result.sort(key=lambda x: -x["price"])
    elif sort == "rating":
        result.sort(key=lambda x: -x["metrics"]["averageRating"])
    else:
        result.sort(key=lambda x: -x["metrics"]["averageRating"])
    
    return {"listings": result, "total": len(result)}


@app.get("/api/listings/{listing_id}")
def get_listing(listing_id: str):
    listing = next((l for l in listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail="Not found")
    
    seller = next((s for s in sellers if s["id"] == listing["sellerId"]), None)
    listing_reviews = [r for r in reviews if r["listingId"] == listing_id]
    
    return {"listing": listing, "seller": seller, "reviews": listing_reviews}


@app.get("/api/sellers")
def get_sellers():
    return {"sellers": sellers}


@app.get("/api/sellers/{seller_id}")
def get_seller(seller_id: str):
    seller = next((s for s in sellers if s["id"] == seller_id), None)
    if not seller:
        raise HTTPException(status_code=404, detail="Not found")
    
    seller_listings = [l for l in listings if l["sellerId"] == seller_id]
    seller_reviews = [r for r in reviews if r["sellerId"] == seller_id]
    
    return {"seller": seller, "listings": seller_listings, "reviews": seller_reviews}


@app.get("/api/categories")
def get_categories():
    categories = list(set(l["category"] for l in listings))
    return {
        "categories": [{"name": cat, "count": len([l for l in listings if l["category"] == cat])} for cat in categories]
    }


@app.get("/api/home-recommendations")
def home_recommendations():
    top_rated = sorted(listings, key=lambda x: -x["metrics"]["averageRating"])[:4]
    most_popular = sorted(listings, key=lambda x: -x["metrics"]["salesCount"])[:4]
    best_value = [l for l in listings if l["price"] < 1000 and l["metrics"]["averageRating"] >= 4.5][:4]
    
    return {
        "sections": [
            {"title": "Top Rated", "items": top_rated},
            {"title": "Most Popular", "items": most_popular},
            {"title": "Best Value", "items": best_value},
        ]
    }


# ---------- AI Endpoints ----------

@app.post("/api/agent")
def agent_endpoint(request_data: AgentRequest):
    session_id = request_data.session_id or str(uuid.uuid4())
    Netra.set_session_id(session_id)
    user_text = (request_data.query or request_data.message or "").strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Query or message required")
    
    previous_messages = CONVERSATION_STORE.get(session_id, [])
    context = dict(request_data.context or {})
    context["session_id"] = session_id

    try:
        print(f"\n📨 Agent query: {user_text} (session_id={session_id}) " + f"Trace ID: {Netra.get_trace_id()}")
        result = marketplace_agent(
            user_text,
            context=context,
            previous_messages=previous_messages if previous_messages else None,
        )
        new_messages = result.pop("new_messages", [])
        if new_messages:
            CONVERSATION_STORE[session_id] = (
                previous_messages + _messages_to_store(new_messages)
            )[-MAX_HISTORY_MESSAGES:]
        return result
    except Exception as e:
        print(f"❌ Agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat_endpoint(request_data: ChatRequest):
    if not request_data.message:
        raise HTTPException(status_code=400, detail="Message required")
    
    trace_id = Netra.get_trace_id()
    print(f"🔗 Trace ID: {trace_id}")
    
    session_id = request_data.session_id or str(uuid.uuid4())
    Netra.set_session_id(session_id)
    previous_messages = CONVERSATION_STORE.get(session_id, [])
    context = dict(request_data.context or {})
    context["session_id"] = session_id

    search_keywords = ["need", "looking", "find", "want", "search", "help", "recommend", "show"]
    is_search = any(kw in request_data.message.lower() for kw in search_keywords)
    
    try:
        if is_search:
            result = marketplace_agent(
                request_data.message,
                context=context,
                previous_messages=previous_messages if previous_messages else None,
            )
            new_messages = result.pop("new_messages", [])
            if new_messages:
                CONVERSATION_STORE[session_id] = (
                    previous_messages + _messages_to_store(new_messages)
                )[-MAX_HISTORY_MESSAGES:]
            result["session_id"] = session_id
            result["trace_id"] = Netra.get_trace_id()
            return result
        else:
            # Simple chat: use history for context
            system_msg = {"role": "system", "content": "You are a helpful assistant for NexusMarket. Be concise."}
            messages_for_api = [system_msg] + _messages_to_store(previous_messages) + [
                {"role": "user", "content": request_data.message}
            ]
            system_instruction, genai_contents = _openai_messages_to_genai(
                messages_for_api[-MAX_HISTORY_MESSAGES - 2:]  # keep under cap + system + current
            )
            response = genai_client.models.generate_content(
                model=AI_MODEL,
                contents=genai_contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=system_instruction or "",
                    temperature=0.7,
                    max_output_tokens=65536,
                ),
            )
            print("--------------------------------")
            print(f"🔍 Chat response: {response}")
            print("--------------------------------")
            assistant_content = response.text or ""
            print(f"🔍 Assistant content: {assistant_content}")
            print("--------------------------------")
            # Persist this turn for memory
            new_messages = [
                {"role": "user", "content": request_data.message},
                {"role": "assistant", "content": assistant_content},
            ]
            CONVERSATION_STORE[session_id] = (
                previous_messages + _messages_to_store(new_messages)
            )[-MAX_HISTORY_MESSAGES:]
            return {
                "response": assistant_content,
                "session_id": session_id,
                "ai_powered": True,
                "trace_id": Netra.get_trace_id(),
            }
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend")
def recommend_endpoint(request_data: RecommendRequest):
    if not request_data.query or len(request_data.query) < 3:
        raise HTTPException(status_code=400, detail="Query required (min 3 chars)")
    
    try:
        result = marketplace_agent(request_data.query)
        return {
            "intent": {"rawQuery": request_data.query},
            "recommendations": [],
            "aiResponse": result["response"],
            "toolsUsed": result["tools_used"],
            "aiPowered": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
def compare_endpoint(request_data: CompareRequest):
    if not request_data.listingIds or len(request_data.listingIds) < 2:
        raise HTTPException(status_code=400, detail="At least 2 listing IDs required")
    
    try:
        compare_query = f"Compare these listings: {', '.join(request_data.listingIds)}. {request_data.query}"
        result = marketplace_agent(compare_query)
        
        compare_listings_data = []
        for lid in request_data.listingIds:
            listing = next((l for l in listings if l["id"] == lid), None)
            if listing:
                seller = next((s for s in sellers if s["id"] == listing["sellerId"]), None)
                compare_listings_data.append({**listing, "seller": seller})
        
        return {
            "listings": compare_listings_data,
            "aiAnalysis": result["response"],
            "toolsUsed": result["tools_used"],
            "aiPowered": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================
# MAIN
# ================================

if __name__ == "__main__":
    import uvicorn
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           🚀 AI MARKETPLACE - PYTHON BACKEND                 ║
╠══════════════════════════════════════════════════════════════╣
║  Port: {PORT}                                                  ║
║  Model: {AI_MODEL:<20}                            ║
║  Data: {len(listings)} listings | {len(sellers)} sellers                       ║
╠══════════════════════════════════════════════════════════════╣
║  🔧 Tools: search, details, compare, recommend, shortlist,  ║
║            help, review, inquiry, budget split, insights,    ║
║            alerts, support, referral                         ║
╠══════════════════════════════════════════════════════════════╣
║  📡 Endpoints:                                               ║
║     GET  /api/health           GET  /api/ai-status           ║
║     GET  /api/listings         GET  /api/listings/{{id}}      ║
║     GET  /api/sellers          GET  /api/sellers/{{id}}       ║
║     GET  /api/categories       GET  /api/home-recommendations║
║     POST /api/agent            POST /api/chat                ║
║     POST /api/recommend        POST /api/compare             ║
╚══════════════════════════════════════════════════════════════╝
""")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

