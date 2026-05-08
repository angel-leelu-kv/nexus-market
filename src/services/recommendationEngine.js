/**
 * ================================
 * AI RECOMMENDATION ENGINE
 * ================================
 * 
 * Core recommendation logic that:
 * 1. Parses natural language intent
 * 2. Scores all listings
 * 3. Ranks and explains results
 * 
 * CRITICAL: All recommendations MUST map to real listings.
 * NO hallucinated data allowed.
 */

// ================================
// INTENT PARSER
// ================================
export class IntentParser {
  /**
   * Parse natural language query into structured intent
   * @param {string} query - User's natural language input
   * @returns {Object} Parsed intent object
   */
  static parse(query) {
    const normalized = query.toLowerCase().trim();
    
    // Extract budget constraints
    const budget = this.extractBudget(normalized);
    
    // Extract timeline
    const timeline = this.extractTimeline(normalized);
    
    // Extract primary need and purpose
    const { need, purpose } = this.extractNeedAndPurpose(normalized);
    
    // Extract quality preference
    const quality = this.extractQualityLevel(normalized);
    
    // Extract category hints
    const categoryHints = this.extractCategories(normalized);
    
    // Calculate parse confidence
    const confidence = this.calculateConfidence({ need, purpose, budget, timeline });
    
    // Identify ambiguities
    const ambiguities = this.identifyAmbiguities({ need, purpose, budget, timeline, query: normalized });
    
    return {
      rawQuery: query,
      parsed: {
        primaryNeed: need,
        purpose: purpose,
        constraints: {
          budget,
          timeline,
          quality,
        },
        categoryHints,
        preferences: this.extractPreferences(normalized),
        dealbreakers: this.extractDealbreakers(normalized),
      },
      parseConfidence: confidence,
      ambiguities,
      timestamp: new Date().toISOString(),
    };
  }
  
  static extractBudget(query) {
    const budgetPatterns = [
      /under\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)/i,
      /below\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)/i,
      /max(?:imum)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)/i,
      /budget\s*(?:of|is)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)/i,
      /\$(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:or\s*less|max)/i,
      /(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|usd)/i,
      /between\s*\$?(\d+(?:,\d{3})*)\s*(?:and|-)\s*\$?(\d+(?:,\d{3})*)/i,
      /\$(\d+(?:,\d{3})*)\s*-\s*\$?(\d+(?:,\d{3})*)/i,
    ];
    
    for (const pattern of budgetPatterns) {
      const match = query.match(pattern);
      if (match) {
        if (match[2]) {
          return {
            min: parseFloat(match[1].replace(/,/g, '')),
            max: parseFloat(match[2].replace(/,/g, '')),
          };
        }
        return {
          min: 0,
          max: parseFloat(match[1].replace(/,/g, '')),
        };
      }
    }
    
    // Check for price descriptors
    if (/cheap|affordable|budget|economical|inexpensive/i.test(query)) {
      return { min: 0, max: 100, descriptor: 'budget' };
    }
    if (/premium|luxury|high[- ]end|expensive|top[- ]tier/i.test(query)) {
      return { min: 500, max: null, descriptor: 'premium' };
    }
    
    return null;
  }
  
  static extractTimeline(query) {
    const timelinePatterns = [
      { pattern: /asap|urgent|immediately|right now|today/i, value: 'immediate' },
      { pattern: /this week|within a week|few days/i, value: 'this_week' },
      { pattern: /next week|in a week/i, value: 'next_week' },
      { pattern: /this month|within a month|few weeks/i, value: 'this_month' },
      { pattern: /no rush|flexible|whenever|no deadline/i, value: 'flexible' },
      { pattern: /(\d+)\s*days?/i, value: (m) => `${m[1]}_days` },
      { pattern: /(\d+)\s*weeks?/i, value: (m) => `${m[1]}_weeks` },
      { pattern: /(\d+)\s*months?/i, value: (m) => `${m[1]}_months` },
    ];
    
    for (const { pattern, value } of timelinePatterns) {
      const match = query.match(pattern);
      if (match) {
        return typeof value === 'function' ? value(match) : value;
      }
    }
    
    return null;
  }
  
  static extractNeedAndPurpose(query) {
    // Common patterns for expressing needs
    const needPatterns = [
      /(?:i\s+)?need\s+(?:a\s+)?(.+?)(?:\s+for|\s+to|\s+that|\s+which|\s+within|$)/i,
      /looking\s+for\s+(?:a\s+)?(.+?)(?:\s+for|\s+to|\s+that|\s+which|\s+within|$)/i,
      /want\s+(?:a\s+)?(.+?)(?:\s+for|\s+to|\s+that|\s+which|\s+within|$)/i,
      /searching\s+for\s+(?:a\s+)?(.+?)(?:\s+for|\s+to|\s+that|\s+which|\s+within|$)/i,
      /find\s+(?:me\s+)?(?:a\s+)?(.+?)(?:\s+for|\s+to|\s+that|\s+which|\s+within|$)/i,
    ];
    
    const purposePatterns = [
      /for\s+(?:my\s+)?(.+?)(?:\s+under|\s+within|\s+budget|$)/i,
      /to\s+(.+?)(?:\s+under|\s+within|\s+budget|$)/i,
    ];
    
    let need = '';
    let purpose = '';
    
    for (const pattern of needPatterns) {
      const match = query.match(pattern);
      if (match && match[1]) {
        need = match[1].trim();
        break;
      }
    }
    
    for (const pattern of purposePatterns) {
      const match = query.match(pattern);
      if (match && match[1]) {
        purpose = match[1].trim();
        break;
      }
    }
    
    // Fallback: use the whole query as need if parsing fails
    if (!need) {
      need = query
        .replace(/under\s*\$?\d+/gi, '')
        .replace(/budget\s*\$?\d+/gi, '')
        .replace(/within\s*\d+\s*\w+/gi, '')
        .trim();
    }
    
    return { need, purpose };
  }
  
  static extractQualityLevel(query) {
    if (/cheap|budget|economical|basic|simple/i.test(query)) return 'economy';
    if (/premium|luxury|high[- ]end|top[- ]tier|best|professional/i.test(query)) return 'premium';
    if (/good|quality|reliable|decent/i.test(query)) return 'standard';
    return 'standard';
  }
  
  static extractCategories(query) {
    const categoryKeywords = {
      'development': ['developer', 'programming', 'coding', 'software', 'app', 'website', 'web'],
      'design': ['designer', 'design', 'logo', 'graphic', 'ui', 'ux', 'branding'],
      'writing': ['writer', 'writing', 'content', 'copywriting', 'article', 'blog'],
      'marketing': ['marketing', 'seo', 'social media', 'advertising', 'promotion'],
      'video': ['video', 'animation', 'editing', 'motion'],
      'consulting': ['consultant', 'consulting', 'advisor', 'strategy'],
      'photography': ['photographer', 'photography', 'photo', 'headshot'],
      'music': ['music', 'audio', 'sound', 'voiceover', 'podcast'],
    };
    
    const matches = [];
    for (const [category, keywords] of Object.entries(categoryKeywords)) {
      if (keywords.some(kw => query.includes(kw))) {
        matches.push(category);
      }
    }
    
    return matches;
  }
  
  static extractPreferences(query) {
    const preferences = [];
    
    if (/experience[d]?|expert|senior|veteran/i.test(query)) preferences.push('experienced');
    if (/fast|quick|speedy/i.test(query)) preferences.push('fast_delivery');
    if (/communicat|responsive/i.test(query)) preferences.push('good_communication');
    if (/portfolio|samples|examples/i.test(query)) preferences.push('portfolio_available');
    if (/local|nearby|same city/i.test(query)) preferences.push('local');
    if (/english|native speaker/i.test(query)) preferences.push('native_english');
    if (/revision|unlimited changes/i.test(query)) preferences.push('revisions_included');
    
    return preferences;
  }
  
  static extractDealbreakers(query) {
    const dealbreakers = [];
    
    if (/no\s+(?:long|extended)\s+wait/i.test(query)) dealbreakers.push('slow_delivery');
    if (/no\s+beginners?/i.test(query)) dealbreakers.push('inexperienced');
    if (/avoid\s+cheap/i.test(query)) dealbreakers.push('low_quality');
    
    return dealbreakers;
  }
  
  static calculateConfidence({ need, purpose, budget, timeline }) {
    let confidence = 0.5; // Base confidence
    
    if (need && need.length > 3) confidence += 0.2;
    if (purpose) confidence += 0.1;
    if (budget) confidence += 0.1;
    if (timeline) confidence += 0.1;
    
    return Math.min(confidence, 1);
  }
  
  static identifyAmbiguities({ need, purpose, budget, timeline, query }) {
    const ambiguities = [];
    
    if (!need || need.length < 5) {
      ambiguities.push('What specifically are you looking for?');
    }
    if (!budget) {
      ambiguities.push('What is your budget range?');
    }
    if (!timeline) {
      ambiguities.push('When do you need this delivered?');
    }
    if (query.includes('?')) {
      ambiguities.push('Please rephrase as a need statement for better results');
    }
    
    return ambiguities;
  }
}

// ================================
// LISTING SCORER
// ================================
export class ListingScorer {
  /**
   * Score a listing against parsed intent
   * @param {Object} listing - The listing to score
   * @param {Object} intent - Parsed user intent
   * @param {Object} seller - Seller data
   * @param {Array} reviews - Listing reviews
   * @returns {Object} Detailed scoring
   */
  static score(listing, intent, seller, reviews = []) {
    const scores = {
      relevance: this.scoreRelevance(listing, intent),
      quality: this.scoreQuality(listing, reviews),
      value: this.scoreValue(listing, intent),
      trustworthiness: this.scoreTrustworthy(seller, listing),
    };
    
    // Weight the scores based on user preferences
    const weights = this.calculateWeights(intent);
    
    const overall = 
      scores.relevance * weights.relevance +
      scores.quality * weights.quality +
      scores.value * weights.value +
      scores.trustworthiness * weights.trustworthiness;
    
    return {
      scores: {
        ...scores,
        overall: Math.round(overall),
      },
      weights,
      matchedAttributes: this.findMatchedAttributes(listing, intent),
    };
  }
  
  static scoreRelevance(listing, intent) {
    let score = 0;
    const parsed = intent.parsed;
    
    // Category match
    if (parsed.categoryHints?.length > 0) {
      const categoryMatch = parsed.categoryHints.some(cat => 
        listing.category?.toLowerCase().includes(cat) ||
        listing.subcategory?.toLowerCase().includes(cat)
      );
      if (categoryMatch) score += 30;
    }
    
    // Keyword matching in title and description
    const needWords = parsed.primaryNeed?.toLowerCase().split(/\s+/) || [];
    const listingText = `${listing.title} ${listing.description}`.toLowerCase();
    
    const matchedWords = needWords.filter(word => 
      word.length > 2 && listingText.includes(word)
    );
    score += Math.min(40, matchedWords.length * 10);
    
    // Tag matching
    if (listing.attributes?.tags) {
      const tagMatches = listing.attributes.tags.filter(tag =>
        needWords.some(word => tag.toLowerCase().includes(word))
      );
      score += Math.min(20, tagMatches.length * 5);
    }
    
    // Use case matching
    if (listing.attributes?.useCases && parsed.purpose) {
      const purposeMatch = listing.attributes.useCases.some(uc =>
        uc.toLowerCase().includes(parsed.purpose.toLowerCase())
      );
      if (purposeMatch) score += 10;
    }
    
    return Math.min(100, score);
  }
  
  static scoreQuality(listing, reviews) {
    let score = 50; // Base score
    
    // Rating impact
    if (listing.metrics?.averageRating) {
      score += (listing.metrics.averageRating - 3) * 15; // 3 is neutral
    }
    
    // Review volume impact
    const reviewCount = listing.metrics?.totalReviews || 0;
    if (reviewCount > 50) score += 10;
    else if (reviewCount > 20) score += 7;
    else if (reviewCount > 5) score += 5;
    
    // Completion rate
    if (listing.metrics?.completionRate) {
      score += (listing.metrics.completionRate - 0.9) * 50;
    }
    
    // Review sentiment (if detailed reviews available)
    if (reviews.length > 0) {
      const avgSentiment = reviews.reduce((acc, r) => 
        acc + (r.sentiment?.score || 0), 0) / reviews.length;
      score += avgSentiment * 10;
    }
    
    return Math.max(0, Math.min(100, score));
  }
  
  static scoreValue(listing, intent) {
    const budget = intent.parsed?.constraints?.budget;
    if (!budget || !listing.price) return 70; // Neutral if no budget specified
    
    let score = 50;
    
    // Under budget is good
    if (budget.max && listing.price <= budget.max) {
      const savings = (budget.max - listing.price) / budget.max;
      score += Math.min(30, savings * 50);
    } else if (budget.max && listing.price > budget.max) {
      const overage = (listing.price - budget.max) / budget.max;
      score -= Math.min(50, overage * 100);
    }
    
    // Quality-adjusted value
    const qualityPref = intent.parsed?.constraints?.quality;
    if (qualityPref === 'premium' && listing.price > (budget.max || 500)) {
      score += 10; // Premium preference accepts higher prices
    } else if (qualityPref === 'economy' && listing.price < 100) {
      score += 10; // Economy preference likes low prices
    }
    
    return Math.max(0, Math.min(100, score));
  }
  
  static scoreTrustworthy(seller, listing) {
    let score = 50;
    
    if (!seller) return score;
    
    // Verification
    if (seller.verified) score += 15;
    if (seller.verificationLevel === 'pro') score += 10;
    if (seller.verificationLevel === 'enterprise') score += 15;
    
    // Track record
    if (seller.metrics?.averageRating > 4.5) score += 10;
    if (seller.metrics?.totalSales > 100) score += 10;
    if (seller.metrics?.responseRate > 0.9) score += 5;
    if (seller.metrics?.repeatClientRate > 0.3) score += 10;
    
    return Math.min(100, score);
  }
  
  static calculateWeights(intent) {
    // Default weights
    const weights = {
      relevance: 0.4,
      quality: 0.25,
      value: 0.2,
      trustworthiness: 0.15,
    };
    
    const quality = intent.parsed?.constraints?.quality;
    const budget = intent.parsed?.constraints?.budget;
    
    // Adjust based on user preferences
    if (quality === 'premium') {
      weights.quality = 0.35;
      weights.value = 0.1;
    } else if (quality === 'economy') {
      weights.value = 0.35;
      weights.quality = 0.15;
    }
    
    if (budget?.descriptor === 'budget') {
      weights.value = 0.35;
    }
    
    return weights;
  }
  
  static findMatchedAttributes(listing, intent) {
    const matches = [];
    const parsed = intent.parsed;
    
    // Check category match
    if (parsed.categoryHints?.length > 0) {
      const matched = parsed.categoryHints.find(cat =>
        listing.category?.toLowerCase().includes(cat)
      );
      if (matched) {
        matches.push({
          attribute: 'category',
          userNeed: `Looking for ${matched}`,
          listingValue: listing.category,
          matchStrength: 'exact',
        });
      }
    }
    
    // Check price match
    if (parsed.constraints?.budget?.max && listing.price) {
      const withinBudget = listing.price <= parsed.constraints.budget.max;
      matches.push({
        attribute: 'price',
        userNeed: `Budget under $${parsed.constraints.budget.max}`,
        listingValue: `$${listing.price}`,
        matchStrength: withinBudget ? 'exact' : 'partial',
      });
    }
    
    // Check feature matches
    const needWords = parsed.primaryNeed?.toLowerCase().split(/\s+/) || [];
    if (listing.attributes?.features) {
      listing.attributes.features.forEach(feature => {
        if (needWords.some(word => feature.toLowerCase().includes(word))) {
          matches.push({
            attribute: 'feature',
            userNeed: parsed.primaryNeed,
            listingValue: feature,
            matchStrength: 'close',
          });
        }
      });
    }
    
    return matches;
  }
}

// ================================
// RECOMMENDATION GENERATOR
// ================================
export class RecommendationEngine {
  /**
   * Generate recommendations for a user query
   * @param {string} query - Natural language query
   * @param {Array} listings - All available listings
   * @param {Object} context - Additional context (sellers, reviews, etc.)
   * @returns {Object} Recommendations with explanations
   */
  static async recommend(query, listings, context = {}) {
    // 1. Parse the intent
    const intent = IntentParser.parse(query);
    
    // 2. Score all listings
    const scoredListings = listings.map(listing => {
      const seller = context.sellers?.find(s => s.id === listing.sellerId);
      const reviews = context.reviews?.filter(r => r.listingId === listing.id) || [];
      
      const scoring = ListingScorer.score(listing, intent, seller, reviews);
      
      return {
        listing,
        seller,
        ...scoring,
      };
    });
    
    // 3. Filter out irrelevant (score < 30)
    const relevant = scoredListings.filter(s => s.scores.overall >= 30);
    
    // 4. Sort by overall score
    relevant.sort((a, b) => b.scores.overall - a.scores.overall);
    
    // 5. Generate explanations for top results
    const recommendations = relevant.slice(0, 10).map((item, index) => ({
      id: `rec-${Date.now()}-${index}`,
      rank: index + 1,
      listing: item.listing,
      seller: item.seller,
      scores: item.scores,
      confidence: item.scores.overall / 100,
      explanation: this.generateExplanation(item, intent, index, relevant.length),
    }));
    
    // 6. Handle edge cases
    if (recommendations.length === 0) {
      return {
        intent,
        recommendations: [],
        fallback: {
          message: "We couldn't find exact matches for your request.",
          suggestions: this.generateSuggestions(intent, listings),
          clarifications: intent.ambiguities,
        },
      };
    }
    
    return {
      intent,
      recommendations,
      totalMatches: relevant.length,
      queryConfidence: intent.parseConfidence,
    };
  }
  
  static generateExplanation(scoredItem, intent, rank, totalMatches) {
    const { listing, scores, matchedAttributes } = scoredItem;
    const parsed = intent.parsed;
    
    // Generate summary
    let summary = '';
    if (scores.overall >= 80) {
      summary = `Excellent match for "${parsed.primaryNeed}"`;
    } else if (scores.overall >= 60) {
      summary = `Strong match with good alignment to your needs`;
    } else {
      summary = `Potential option worth considering`;
    }
    
    // Generate strengths (citing real attributes)
    const strengths = [];
    
    if (scores.relevance >= 70) {
      strengths.push(`Directly addresses your need for ${parsed.primaryNeed}`);
    }
    
    if (listing.metrics?.averageRating >= 4.5) {
      strengths.push(`Highly rated (${listing.metrics.averageRating.toFixed(1)}★) with ${listing.metrics.totalReviews} reviews`);
    }
    
    if (parsed.constraints?.budget?.max && listing.price <= parsed.constraints.budget.max) {
      const savings = parsed.constraints.budget.max - listing.price;
      if (savings > 0) {
        strengths.push(`Within budget ($${listing.price} - saves $${savings})`);
      }
    }
    
    if (listing.metrics?.completionRate > 0.95) {
      strengths.push(`${Math.round(listing.metrics.completionRate * 100)}% completion rate`);
    }
    
    // Generate considerations
    const considerations = [];
    
    if (parsed.constraints?.budget?.max && listing.price > parsed.constraints.budget.max * 0.9) {
      considerations.push('Near the top of your budget');
    }
    
    if (listing.metrics?.totalReviews < 10) {
      considerations.push('Relatively new listing with limited reviews');
    }
    
    if (listing.attributes?.deliveryTime && 
        parsed.constraints?.timeline === 'immediate') {
      considerations.push(`Delivery time: ${listing.attributes.deliveryTime}`);
    }
    
    // Position vs alternatives
    let comparedToAlternatives = '';
    if (rank === 1) {
      comparedToAlternatives = `Top recommendation out of ${totalMatches} matches`;
    } else if (rank <= 3) {
      comparedToAlternatives = `#${rank} of ${totalMatches} - strong alternative to top pick`;
    } else {
      comparedToAlternatives = `#${rank} of ${totalMatches} matches`;
    }
    
    return {
      summary,
      matchedAttributes,
      strengths,
      considerations,
      comparedToAlternatives,
    };
  }
  
  static generateSuggestions(intent, listings) {
    const suggestions = [];
    
    // Suggest broadening search
    suggestions.push('Try using more general terms');
    
    // Suggest popular in category
    if (intent.parsed?.categoryHints?.length > 0) {
      suggestions.push(`Browse popular ${intent.parsed.categoryHints[0]} listings`);
    }
    
    // Suggest adjusting budget
    if (intent.parsed?.constraints?.budget?.max) {
      suggestions.push('Consider increasing your budget for more options');
    }
    
    return suggestions;
  }
  
  /**
   * Generate AI comparison between listings
   */
  static generateComparison(listings, intent) {
    const dimensions = [
      { name: 'Price', key: 'price', weight: 0.25 },
      { name: 'Quality', key: 'quality', weight: 0.25 },
      { name: 'Speed', key: 'deliveryTime', weight: 0.2 },
      { name: 'Reliability', key: 'reliability', weight: 0.15 },
      { name: 'Value', key: 'value', weight: 0.15 },
    ];
    
    const comparison = {
      dimensions: dimensions.map(dim => {
        const values = {};
        let winner = null;
        let bestValue = null;
        
        listings.forEach(listing => {
          let value;
          switch (dim.key) {
            case 'price':
              value = listing.price;
              if (!bestValue || value < bestValue) {
                bestValue = value;
                winner = listing.id;
              }
              values[listing.id] = `$${value}`;
              break;
            case 'quality':
              value = listing.metrics?.averageRating || 0;
              if (!bestValue || value > bestValue) {
                bestValue = value;
                winner = listing.id;
              }
              values[listing.id] = `${value.toFixed(1)}★`;
              break;
            case 'deliveryTime':
              value = listing.attributes?.deliveryTime || 'Not specified';
              values[listing.id] = value;
              break;
            case 'reliability':
              value = listing.metrics?.completionRate || 0;
              if (!bestValue || value > bestValue) {
                bestValue = value;
                winner = listing.id;
              }
              values[listing.id] = `${Math.round(value * 100)}%`;
              break;
            case 'value':
              // Price per quality point
              const rating = listing.metrics?.averageRating || 3;
              value = listing.price / rating;
              if (!bestValue || value < bestValue) {
                bestValue = value;
                winner = listing.id;
              }
              values[listing.id] = value < 20 ? 'Excellent' : value < 40 ? 'Good' : 'Fair';
              break;
          }
        });
        
        return {
          name: dim.name,
          weight: dim.weight,
          values,
          winner,
        };
      }),
      
      perListing: {},
    };
    
    // Generate pros/cons per listing
    listings.forEach(listing => {
      const pros = [];
      const cons = [];
      
      // Price analysis
      const avgPrice = listings.reduce((sum, l) => sum + l.price, 0) / listings.length;
      if (listing.price < avgPrice * 0.8) pros.push('Most affordable option');
      else if (listing.price > avgPrice * 1.2) cons.push('Higher priced');
      
      // Quality analysis
      if (listing.metrics?.averageRating >= 4.8) pros.push('Exceptional ratings');
      else if (listing.metrics?.averageRating < 4.0) cons.push('Lower ratings');
      
      // Review volume
      if (listing.metrics?.totalReviews > 100) pros.push('Well-established');
      else if (listing.metrics?.totalReviews < 10) cons.push('Limited track record');
      
      // Best for
      let bestFor = 'General use';
      if (listing.price < avgPrice && listing.metrics?.averageRating >= 4.0) {
        bestFor = 'Budget-conscious buyers seeking quality';
      } else if (listing.metrics?.averageRating >= 4.7) {
        bestFor = 'Those prioritizing quality';
      }
      
      comparison.perListing[listing.id] = { pros, cons, bestFor };
    });
    
    // Determine overall winner
    const winCounts = {};
    comparison.dimensions.forEach(dim => {
      if (dim.winner) {
        winCounts[dim.winner] = (winCounts[dim.winner] || 0) + dim.weight;
      }
    });
    
    const overallWinner = Object.entries(winCounts)
      .sort((a, b) => b[1] - a[1])[0]?.[0];
    
    comparison.overallWinner = overallWinner;
    comparison.winnerRationale = overallWinner 
      ? `Wins in the most important dimensions based on your priorities`
      : 'No clear winner - choose based on your priorities';
    
    comparison.verdict = this.generateVerdict(listings, comparison, intent);
    
    return comparison;
  }
  
  static generateVerdict(listings, comparison, intent) {
    const winner = listings.find(l => l.id === comparison.overallWinner);
    if (!winner) return 'All options have their merits. Consider your priorities.';
    
    const parsed = intent?.parsed;
    const quality = parsed?.constraints?.quality;
    
    if (quality === 'premium') {
      return `For premium quality, ${winner.title} offers the best overall experience with top ratings and reliability.`;
    } else if (quality === 'economy') {
      return `For value-conscious buyers, ${winner.title} delivers the best balance of price and quality.`;
    }
    
    return `${winner.title} emerges as the top choice, offering the best combination of quality, value, and reliability for your needs.`;
  }
}

export default {
  IntentParser,
  ListingScorer,
  RecommendationEngine,
};

