/**
 * ================================
 * AI MARKETPLACE DATA MODELS
 * ================================
 * 
 * Core data structures for the marketplace.
 * All AI recommendations MUST map to these real data structures.
 */

// ================================
// LISTING MODEL
// ================================
export const ListingSchema = {
  id: 'string',           // Unique identifier
  title: 'string',        // Product/service name
  description: 'string',  // Detailed description
  category: 'string',     // Primary category
  subcategory: 'string',  // Secondary classification
  
  // Pricing
  price: 'number',
  priceUnit: 'string',    // 'fixed', 'hourly', 'monthly', 'negotiable'
  currency: 'string',
  
  // Attributes (for AI matching)
  attributes: {
    tags: ['string'],           // Searchable tags
    features: ['string'],       // Key features
    specifications: {},         // Category-specific specs
    targetAudience: ['string'], // Who is this for
    useCases: ['string'],       // What problems it solves
    skillLevel: 'string',       // beginner, intermediate, advanced
    deliveryTime: 'string',     // Estimated delivery
    location: 'string',         // Geographic availability
  },
  
  // Metrics
  metrics: {
    averageRating: 'number',
    totalReviews: 'number',
    salesCount: 'number',
    viewCount: 'number',
    responseTime: 'string',
    completionRate: 'number',
  },
  
  // Media
  images: ['string'],
  videos: ['string'],
  
  // Seller reference
  sellerId: 'string',
  
  // Status
  status: 'string',       // active, paused, sold
  availability: 'boolean',
  stockCount: 'number',
  
  // Timestamps
  createdAt: 'date',
  updatedAt: 'date',
}

// ================================
// SELLER MODEL
// ================================
export const SellerSchema = {
  id: 'string',
  name: 'string',
  avatar: 'string',
  bio: 'string',
  
  // Expertise (for AI analysis)
  expertise: {
    primarySkills: ['string'],
    industries: ['string'],
    yearsExperience: 'number',
    certifications: ['string'],
    languages: ['string'],
  },
  
  // AI-generated profile
  aiProfile: {
    strengths: ['string'],      // Generated from reviews & performance
    specialties: ['string'],    // Derived from listing patterns
    communicationStyle: 'string',
    reliabilityScore: 'number',
  },
  
  // Metrics
  metrics: {
    totalSales: 'number',
    averageRating: 'number',
    responseRate: 'number',
    repeatClientRate: 'number',
    memberSince: 'date',
  },
  
  // Verification
  verified: 'boolean',
  verificationLevel: 'string', // basic, pro, enterprise
}

// ================================
// REVIEW MODEL
// ================================
export const ReviewSchema = {
  id: 'string',
  listingId: 'string',
  sellerId: 'string',
  buyerId: 'string',
  
  // Rating breakdown
  ratings: {
    overall: 'number',
    quality: 'number',
    communication: 'number',
    value: 'number',
    delivery: 'number',
  },
  
  // Content
  title: 'string',
  content: 'string',
  
  // AI analysis
  sentiment: {
    score: 'number',      // -1 to 1
    label: 'string',      // negative, neutral, positive
    highlights: ['string'], // Key positive points
    concerns: ['string'],   // Key negative points
  },
  
  // Metadata
  verified: 'boolean',
  helpful: 'number',
  createdAt: 'date',
}

// ================================
// USER INTENT MODEL
// ================================
export const UserIntentSchema = {
  id: 'string',
  rawQuery: 'string',     // Original natural language input
  
  // Parsed intent
  parsed: {
    primaryNeed: 'string',        // What they're looking for
    purpose: 'string',            // Why they need it
    constraints: {
      budget: { min: 'number', max: 'number' },
      timeline: 'string',
      location: 'string',
      quality: 'string',          // economy, standard, premium
    },
    preferences: ['string'],      // Nice-to-haves
    dealbreakers: ['string'],     // Must-not-have
  },
  
  // Confidence
  parseConfidence: 'number',
  ambiguities: ['string'],        // Parts that need clarification
  
  // Session
  userId: 'string',
  sessionId: 'string',
  timestamp: 'date',
}

// ================================
// RECOMMENDATION MODEL
// ================================
export const RecommendationSchema = {
  id: 'string',
  intentId: 'string',
  listingId: 'string',
  
  // Scoring
  scores: {
    overall: 'number',            // 0-100 final score
    relevance: 'number',          // How well it matches intent
    quality: 'number',            // Based on reviews/metrics
    value: 'number',              // Price vs. quality ratio
    trustworthiness: 'number',    // Seller reliability
  },
  
  // Explanation (MUST cite real attributes)
  explanation: {
    summary: 'string',            // One-line why
    matchedAttributes: [{
      attribute: 'string',
      userNeed: 'string',
      listingValue: 'string',
      matchStrength: 'string',    // exact, close, partial
    }],
    strengths: ['string'],        // Why this is good
    considerations: ['string'],   // Potential concerns
    comparedToAlternatives: 'string', // Position vs others
  },
  
  // Ranking
  rank: 'number',
  confidence: 'number',
  
  timestamp: 'date',
}

// ================================
// COMPARISON MODEL
// ================================
export const ComparisonSchema = {
  id: 'string',
  intentId: 'string',
  listingIds: ['string'],
  
  // AI-generated comparison
  comparison: {
    dimensions: [{
      name: 'string',           // e.g., "Price", "Quality", "Speed"
      weight: 'number',         // Importance based on user intent
      values: {},               // listingId -> value mapping
      winner: 'string',         // listingId of best for this dimension
    }],
    
    perListing: {
      // listingId -> { pros: [], cons: [], bestFor: string }
    },
    
    overallWinner: 'string',
    winnerRationale: 'string',
    
    verdict: 'string',          // AI's final recommendation
  },
  
  timestamp: 'date',
}

export default {
  ListingSchema,
  SellerSchema,
  ReviewSchema,
  UserIntentSchema,
  RecommendationSchema,
  ComparisonSchema,
}

