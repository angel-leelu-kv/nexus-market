"""Generate clusterable traces across intent categories for the NexusMarket AI agent.

Each trace is a multi-turn user<->agent conversation labeled with an intent.
Traces within the same intent use varied phrasing to produce
embedding-separable clusters for downstream insight analysis.

Usage examples:
    python generate_traces.py --samples 5
    python generate_traces.py --samples 3 --turns 4
    python generate_traces.py --profile buyer_journey --turns 3
    python generate_traces.py --profile seller_focus
    python generate_traces.py --intent search_services:10 compare_listings:8
    python generate_traces.py --profile balanced --intent search_services:15
    python generate_traces.py --list-intents
    python generate_traces.py --list-profiles
    python generate_traces.py --offline --samples 5   # save traces, no LLM/API calls
"""

import argparse
import asyncio
import json
import os
import random
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()
load_dotenv(Path(__file__).resolve().parent / ".env")

# ---------------------------------------------------------------------------
# Buyer Personas
# ---------------------------------------------------------------------------

BUYER_PERSONAS = {
    "startup_founder": {
        "name": "Ankit Verma",
        "profile": "Startup founder, needs logo + website + copy, budget-conscious ($2-5k total)",
        "budget_level": "medium",
        "interests": ["Development", "Design", "Writing"],
    },
    "marketing_manager": {
        "name": "Rachel Torres",
        "profile": "Marketing manager at mid-size SaaS, needs SEO, content, and video editing",
        "budget_level": "high",
        "interests": ["Marketing", "Writing", "Video"],
    },
    "solopreneur": {
        "name": "Deepak Iyer",
        "profile": "Solopreneur, tight budget (<$500), needs quick logo and basic WordPress site",
        "budget_level": "low",
        "interests": ["Design", "Development"],
    },
    "agency_owner": {
        "name": "Clara Nguyen",
        "profile": "Agency owner outsourcing ML/data work and motion graphics for clients",
        "budget_level": "high",
        "interests": ["Data & AI", "Video", "Development"],
    },
    "ecommerce_seller": {
        "name": "Priya Malhotra",
        "profile": "E-commerce seller needing product copy, email sequences, and SEO help",
        "budget_level": "medium",
        "interests": ["Writing", "Marketing"],
    },
}

# ---------------------------------------------------------------------------
# Intent Catalog (each intent = one cluster)
# ---------------------------------------------------------------------------

INTENT_CATALOG = {
    "search_services": {
        "description": "Customer searches for a specific type of service or skill",
        "guidance": "Search for a service by naming the skill, technology, or deliverable you need.",
        "expected_tools": ["search_listings"],
        "sample_queries": [
            "I need someone to build a React web app",
            "Find me logo design under $500",
            "Looking for SEO help for my e-commerce site",
            "Search for machine learning or data science projects",
            "Find WordPress developers",
        ],
    },
    "browse_category": {
        "description": "Customer wants to explore a category of services",
        "guidance": "Ask what's available in a category or ask about categories in general.",
        "expected_tools": ["search_listings"],
        "sample_queries": [
            "What's available in the Writing category?",
            "What categories do you have?",
            "Show me what's in Data & AI",
            "What do you have in Video?",
            "Top rated in Development",
        ],
    },
    "get_listing_details": {
        "description": "Customer asks for details about a specific listing",
        "guidance": "Ask about a specific listing by ID or by name from previous results.",
        "expected_tools": ["get_listing_details"],
        "sample_queries": [
            "Show me listing-001 details",
            "Tell me more about listing-005",
            "What are the reviews for the React web application listing?",
            "What's the delivery time for listing-011?",
            "More details on the brand identity package",
        ],
    },
    "compare_listings": {
        "description": "Customer wants to compare two or more services side by side",
        "guidance": "Ask to compare specific listings by ID or by description.",
        "expected_tools": ["compare_listings"],
        "sample_queries": [
            "Compare listing-001, listing-002, and listing-003",
            "Compare the two logo design listings",
            "Compare listing-006 and listing-012",
            "I want to compare React Native app development options",
            "Which is better: listing-001 or listing-004?",
        ],
    },
    "get_recommendations": {
        "description": "Customer asks for personalized service recommendations",
        "guidance": "Describe your needs and optionally a budget level for tailored recommendations.",
        "expected_tools": ["get_recommendations"],
        "sample_queries": [
            "Recommend something for a startup that needs a logo and website copy",
            "Show me the best rated video editing services",
            "Recommend 3 options for a startup logo under $500",
            "What would you suggest for email marketing on a medium budget?",
            "I need a data dashboard and analysis — what do you recommend?",
        ],
    },
    "shortlist_add": {
        "description": "Customer wants to save a listing to their shortlist",
        "guidance": "Ask to add a specific listing to your shortlist or save it for later.",
        "expected_tools": ["add_to_shortlist"],
        "sample_queries": [
            "Add listing-001 to my shortlist",
            "Save the React Native one to my shortlist",
            "Add the first result to my shortlist",
            "Bookmark that logo design listing",
            "Save this one for later",
        ],
    },
    "shortlist_view": {
        "description": "Customer wants to see their saved shortlist",
        "guidance": "Ask to see your saved or shortlisted items.",
        "expected_tools": ["get_my_shortlist"],
        "sample_queries": [
            "What's on my shortlist?",
            "Show my saved listings",
            "What have I bookmarked so far?",
            "Let me see my shortlist",
            "Show me the listings I saved",
        ],
    },
    "shortlist_remove": {
        "description": "Customer wants to remove a listing from their shortlist",
        "guidance": "Ask to remove a specific item from your shortlist.",
        "expected_tools": ["remove_from_shortlist"],
        "sample_queries": [
            "Remove listing-001 from my shortlist",
            "Take the logo design off my shortlist",
            "Remove everything from my shortlist",
            "Delete the WordPress one from my saved items",
            "Clear my shortlist",
        ],
    },
    "ask_help_general": {
        "description": "Customer asks how the platform works in general",
        "guidance": "Ask a general question about how NexusMarket works or what it can do.",
        "expected_tools": ["get_help"],
        "sample_queries": [
            "How does NexusMarket work?",
            "What can you do?",
            "How do I get started as a buyer?",
            "Tell me about sellers on the platform",
            "Are sellers verified?",
        ],
    },
    "ask_help_payment": {
        "description": "Customer asks about payments, refunds, or pricing policies",
        "guidance": "Ask about payment process, refund policy, or how money works on the platform.",
        "expected_tools": ["get_help"],
        "sample_queries": [
            "How do payments work?",
            "What's your refund policy?",
            "Explain the refund process",
            "Is payment secure here?",
            "When do I pay the seller?",
        ],
    },
    "ask_help_hiring": {
        "description": "Customer asks about the hiring/engagement process",
        "guidance": "Ask how to hire a seller or what happens after sending an inquiry.",
        "expected_tools": ["get_help"],
        "sample_queries": [
            "How do I hire a seller?",
            "What happens after I send an inquiry?",
            "How to get started as a buyer?",
            "What's the process for starting a project?",
            "How do I engage a freelancer?",
        ],
    },
    "submit_review": {
        "description": "Customer wants to leave a review for a service they used",
        "guidance": "Express desire to review a listing with a rating and comment.",
        "expected_tools": ["submit_review"],
        "sample_queries": [
            "I want to leave a review for listing-009",
            "I'd like to review the copywriting service I used — 5 stars, great work",
            "Submit a review for listing-003 — 4 stars, good delivery",
            "Leave a 5-star review for listing-004 — Fast and professional",
            "Rate listing-001 five stars, amazing quality",
        ],
    },
    "create_inquiry": {
        "description": "Customer wants to contact a seller to hire them",
        "guidance": "Express intent to hire and provide listing ID, requirements, timeline, or budget.",
        "expected_tools": ["create_inquiry"],
        "sample_queries": [
            "I want to hire the person behind listing-005 for my landing page",
            "Create an inquiry for listing-001 — I need a dashboard in 3 weeks, budget around 3000",
            "Send a message to the React Native developer about my app idea",
            "I'm interested in listing-007, need it in 2 weeks",
            "Create inquiry for listing-010 — need 7-email welcome sequence, budget $700",
        ],
    },
    "budget_planning": {
        "description": "Customer wants help splitting budget across multiple goals",
        "guidance": "State a total budget and list the things you need (e.g. logo, website, copy).",
        "expected_tools": ["suggest_budget_split"],
        "sample_queries": [
            "I have $2000 total for logo, website, and social kit — how should I split it?",
            "Suggest budget split for $5000 across logo, web dev, and copywriting",
            "How should I allocate $3000 between SEO and content writing?",
            "I have $1500 for branding and video — what split makes sense?",
            "Budget of $4000 for app development and marketing — suggest a split",
        ],
    },
    "seller_insights": {
        "description": "Seller wants marketplace insights, demand info, or tips",
        "guidance": "Ask as a seller about what categories have demand, pricing, or how to grow.",
        "expected_tools": ["get_marketplace_insights"],
        "sample_queries": [
            "I'm a seller — what categories have the most demand?",
            "How do I get more buyers as a seller?",
            "What's in demand in Design?",
            "Marketplace insights for Marketing category",
            "What should I price my services at?",
        ],
    },
    "alert_create": {
        "description": "Customer wants to be notified about new listings matching criteria",
        "guidance": "Ask to be alerted when new listings appear in a category, under a price, or from a seller.",
        "expected_tools": ["create_alert"],
        "sample_queries": [
            "Create an alert for new Design listings under $800",
            "Notify me when there are new SEO listings",
            "Alert me when seller-002 posts new listings",
            "Alert for new listings in Development under $2000",
            "Let me know when there's something new in Video",
        ],
    },
    "alert_view": {
        "description": "Customer wants to check their active alerts",
        "guidance": "Ask to see or check your current alerts.",
        "expected_tools": ["get_my_alerts"],
        "sample_queries": [
            "What alerts do I have?",
            "Show my alerts",
            "What am I subscribed to?",
            "List my active notifications",
            "Do I have any alerts set up?",
        ],
    },
    "alert_delete": {
        "description": "Customer wants to remove an alert",
        "guidance": "Ask to delete or remove a specific alert.",
        "expected_tools": ["delete_alert"],
        "sample_queries": [
            "Delete my alert for Design",
            "Remove the SEO alert",
            "Cancel my notification for new listings",
            "Stop alerting me about Development",
            "Delete all my alerts",
        ],
    },
    "support_create": {
        "description": "Customer has an issue and wants to create a support ticket",
        "guidance": "Describe an order issue, payment problem, or desire to report a seller.",
        "expected_tools": ["create_support_ticket"],
        "sample_queries": [
            "I have an issue with my order",
            "Create a support ticket — payment issue, order ID 12345",
            "I want to report a seller",
            "I was charged incorrectly for my last order",
            "The seller didn't deliver on time, I need help",
        ],
    },
    "support_status": {
        "description": "Customer wants to check the status of their support tickets",
        "guidance": "Ask about the status of open support tickets.",
        "expected_tools": ["get_support_status"],
        "sample_queries": [
            "What's the status of my support tickets?",
            "Check my support ticket status",
            "Any update on my ticket?",
            "Is my issue resolved yet?",
            "Show me my open tickets",
        ],
    },
    "referral_info": {
        "description": "Customer asks about the referral program",
        "guidance": "Ask about the referral or invite program and how it works.",
        "expected_tools": ["get_referral_info"],
        "sample_queries": [
            "Tell me about the referral program",
            "How do I invite friends?",
            "What do I get for referring someone?",
            "Give me the referral program details",
            "How does your invite system work?",
        ],
    },
    "referral_create": {
        "description": "Customer wants to create their personal referral link",
        "guidance": "Ask for your referral link to share with others.",
        "expected_tools": ["create_referral_link"],
        "sample_queries": [
            "I want a referral link",
            "Create my referral link",
            "Give me a link to share with friends",
            "Generate my invite link",
            "I'd like my personal referral URL",
        ],
    },
    "price_filter": {
        "description": "Customer searches with a specific budget or price constraint",
        "guidance": "Search for services mentioning a specific price limit or budget bracket.",
        "expected_tools": ["search_listings", "get_recommendations"],
        "sample_queries": [
            "Anything under $1000 for a quick logo?",
            "Show me cheap WordPress options",
            "Best value in Video editing?",
            "Budget under $400 for a logo",
            "What can I get for $500 in Development?",
        ],
    },
    "contextual_reference": {
        "description": "Customer refers to items from earlier in the conversation",
        "guidance": "Reference something shown earlier like 'that one', 'the first option', 'add both'.",
        "expected_tools": ["add_to_shortlist", "get_listing_details", "compare_listings"],
        "sample_queries": [
            "Add the second one you showed me to my shortlist",
            "Compare that one with listing-002",
            "Tell me more about the first one",
            "Add both to my shortlist",
            "What was the price on that last listing?",
        ],
    },
    "greeting_chitchat": {
        "description": "Customer sends a greeting or general chitchat message",
        "guidance": "Send a casual greeting, ask what the bot can do, or say thanks.",
        "expected_tools": [],
        "sample_queries": [
            "Hi",
            "What can you do?",
            "Help",
            "Thanks, that's all",
            "Hello, I'm new here",
        ],
    },
}

# ---------------------------------------------------------------------------
# Intent Discriminators — wording constraints so intents stay separable
# ---------------------------------------------------------------------------

INTENT_DISCRIMINATORS: dict[str, str] = {
    "search_services": (
        "Name a specific skill, technology, or deliverable you need. "
        "Do not ask about categories in the abstract or request a recommendation."
    ),
    "browse_category": (
        "Ask about what exists in a category or ask to list categories. "
        "Do not mention a specific skill or technology — keep it category-level."
    ),
    "get_listing_details": (
        "Ask about a specific listing by ID or name. "
        "Do not ask for a search, comparison, or general recommendation."
    ),
    "compare_listings": (
        "Explicitly ask to compare two or more listings side by side. "
        "Use words like compare, versus, which is better, or side by side."
    ),
    "get_recommendations": (
        "Ask for suggestions, recommendations, or 'what would you suggest'. "
        "Do not ask for raw search results or a category listing."
    ),
    "shortlist_add": (
        "Ask to save, add, or bookmark a listing to your shortlist. "
        "Do not ask to view or remove from the shortlist."
    ),
    "shortlist_view": (
        "Ask to view, show, or see your saved/shortlisted items. "
        "Do not ask to add or remove anything."
    ),
    "shortlist_remove": (
        "Ask to remove, delete, or clear items from your shortlist. "
        "Do not ask to add or view items."
    ),
    "ask_help_general": (
        "Ask how the platform works, what it does, or how to get started. "
        "Do not ask specifically about payments, refunds, or hiring process."
    ),
    "ask_help_payment": (
        "Ask specifically about payment, refund, charges, or money-related policy. "
        "Do not ask generic how-it-works or hiring questions."
    ),
    "ask_help_hiring": (
        "Ask about the process of hiring, engaging, or starting work with a seller. "
        "Do not ask about refunds/payments or generic platform overview."
    ),
    "submit_review": (
        "Express intent to leave a rating or review for a listing you used. "
        "Include a star rating or feedback. Do not ask to search or browse."
    ),
    "create_inquiry": (
        "Express intent to hire, contact, or message a seller about a project. "
        "Mention requirements, timeline, or budget. Do not just browse or compare."
    ),
    "budget_planning": (
        "State a total dollar budget and multiple goals to split it across. "
        "Do not just search for a single service or ask for recommendations."
    ),
    "seller_insights": (
        "Speak as a seller asking about marketplace demand, tips, or pricing guidance. "
        "Do not sound like a buyer searching for services."
    ),
    "alert_create": (
        "Ask to create a notification or alert for future listings matching criteria. "
        "Do not ask to view or delete existing alerts."
    ),
    "alert_view": (
        "Ask to view, check, or list your current alerts. "
        "Do not ask to create or delete alerts."
    ),
    "alert_delete": (
        "Ask to delete, remove, or cancel an existing alert. "
        "Do not ask to view or create alerts."
    ),
    "support_create": (
        "Describe a problem or issue and ask to create a ticket or report something. "
        "Do not ask about ticket status."
    ),
    "support_status": (
        "Ask about the status or progress of an existing support ticket. "
        "Do not describe a new issue or ask to create a ticket."
    ),
    "referral_info": (
        "Ask about how the referral/invite program works or what rewards exist. "
        "Do not ask to generate your actual link."
    ),
    "referral_create": (
        "Ask for your personal referral link to share. "
        "Do not just ask about how the program works."
    ),
    "price_filter": (
        "Include an explicit dollar amount, price cap, or budget bracket in a search. "
        "The price constraint must be the central element of the message."
    ),
    "contextual_reference": (
        "Reference something from earlier in conversation using 'that one', 'the first', "
        "'both', or similar. Do not name a listing ID directly."
    ),
    "greeting_chitchat": (
        "Send a greeting, thanks, or general non-task message. "
        "Do not include any service search, listing reference, or action request."
    ),
}

# ---------------------------------------------------------------------------
# Intent Tool Plans — per-turn guidance to drive multi-turn conversations
# ---------------------------------------------------------------------------

INTENT_TOOL_PLANS: dict[str, dict[str, Any]] = {
    "search_services": {
        "expected_tools": ["search_listings"],
        "turn_guidance": {
            1: "Search for a specific service you need (e.g. React developer, logo design, SEO).",
            2: "Ask for details about one of the results the agent showed.",
            3: "Ask to save your favorite result to your shortlist or ask a follow-up.",
        },
    },
    "browse_category": {
        "expected_tools": ["search_listings"],
        "turn_guidance": {
            1: "Ask what's available in a specific category (Development, Design, Marketing, Writing, Video, Data & AI).",
            2: "Ask about a specific listing from the results.",
            3: "Ask a follow-up or thank the agent.",
        },
    },
    "get_listing_details": {
        "expected_tools": ["get_listing_details"],
        "turn_guidance": {
            1: "Ask about a specific listing (use listing-001 through listing-015).",
            2: "Ask a follow-up about the listing (reviews, delivery time, seller info).",
            3: "Decide whether to save it or ask to compare with another.",
        },
    },
    "compare_listings": {
        "expected_tools": ["compare_listings"],
        "turn_guidance": {
            1: "Ask to compare two or more listings (use listing IDs like listing-001, listing-002).",
            2: "Ask which one is better for your specific situation.",
            3: "Make a decision or ask to save one to your shortlist.",
        },
    },
    "get_recommendations": {
        "expected_tools": ["get_recommendations"],
        "turn_guidance": {
            1: "Describe what you need and ask for recommendations.",
            2: "Ask for more details about one of the recommendations.",
            3: "Ask a follow-up or decide to move forward with one.",
        },
    },
    "shortlist_add": {
        "expected_tools": ["search_listings", "add_to_shortlist"],
        "turn_guidance": {
            1: "Search for a service you're interested in.",
            2: "Ask to add one of the results to your shortlist.",
            3: "Confirm or ask about what's on your shortlist now.",
        },
    },
    "shortlist_view": {
        "expected_tools": ["get_my_shortlist"],
        "turn_guidance": {
            1: "Ask to see your saved shortlist.",
            2: "Ask about details of one item on your shortlist.",
            3: "Thank the agent or ask to compare shortlisted items.",
        },
    },
    "shortlist_remove": {
        "expected_tools": ["get_my_shortlist", "remove_from_shortlist"],
        "turn_guidance": {
            1: "Ask to see your shortlist first.",
            2: "Ask to remove a specific item from the shortlist.",
            3: "Confirm the removal or ask about what remains.",
        },
    },
    "ask_help_general": {
        "expected_tools": ["get_help"],
        "turn_guidance": {
            1: "Ask a general question about how NexusMarket works.",
            2: "Ask a follow-up about a specific aspect mentioned in the answer.",
            3: "Thank the agent or ask to start searching.",
        },
    },
    "ask_help_payment": {
        "expected_tools": ["get_help"],
        "turn_guidance": {
            1: "Ask about payments, refunds, or pricing on the platform.",
            2: "Ask a specific follow-up about the payment/refund process.",
            3: "Thank the agent or transition to browsing services.",
        },
    },
    "ask_help_hiring": {
        "expected_tools": ["get_help"],
        "turn_guidance": {
            1: "Ask how to hire a seller or start a project.",
            2: "Ask what happens after you send an inquiry.",
            3: "Thank the agent or ask to search for services.",
        },
    },
    "submit_review": {
        "expected_tools": ["submit_review"],
        "turn_guidance": {
            1: "Say you want to leave a review. Mention the listing ID, star rating, and comment.",
            2: "React to the confirmation. Ask if you can review another listing.",
            3: "Thank the agent.",
        },
    },
    "create_inquiry": {
        "expected_tools": ["search_listings", "create_inquiry"],
        "turn_guidance": {
            1: "Search for the type of service you want to hire for.",
            2: "Say you want to hire one of the results. Provide requirements, timeline, and budget.",
            3: "React to the confirmation or ask about next steps.",
        },
    },
    "budget_planning": {
        "expected_tools": ["suggest_budget_split"],
        "turn_guidance": {
            1: "State your total budget and the goals you need (e.g. logo, website, copy).",
            2: "Ask for recommendations for one of the goals based on the suggested split.",
            3: "React to the suggestions or adjust the split.",
        },
    },
    "seller_insights": {
        "expected_tools": ["get_marketplace_insights"],
        "turn_guidance": {
            1: "As a seller, ask about demand, pricing, or tips for a category.",
            2: "Ask a follow-up about how to stand out or get more buyers.",
            3: "Thank the agent or ask about another category.",
        },
    },
    "alert_create": {
        "expected_tools": ["create_alert"],
        "turn_guidance": {
            1: "Ask to create an alert for new listings in a category, under a price, or from a seller.",
            2: "Confirm the alert was created or ask to see your alerts.",
            3: "Thank the agent or ask about another category.",
        },
    },
    "alert_view": {
        "expected_tools": ["get_my_alerts"],
        "turn_guidance": {
            1: "Ask to see your current alerts.",
            2: "Ask about one specific alert or ask to modify it.",
            3: "Thank the agent.",
        },
    },
    "alert_delete": {
        "expected_tools": ["get_my_alerts", "delete_alert"],
        "turn_guidance": {
            1: "Ask to see your alerts first.",
            2: "Ask to delete a specific alert.",
            3: "Confirm or check remaining alerts.",
        },
    },
    "support_create": {
        "expected_tools": ["create_support_ticket"],
        "turn_guidance": {
            1: "Describe an issue you're having (order problem, payment issue, seller complaint).",
            2: "Provide more details if the agent asks, or confirm ticket creation.",
            3: "Ask about next steps or resolution timeline.",
        },
    },
    "support_status": {
        "expected_tools": ["get_support_status"],
        "turn_guidance": {
            1: "Ask about the status of your support tickets.",
            2: "Ask when you can expect a resolution.",
            3: "Thank the agent or express urgency.",
        },
    },
    "referral_info": {
        "expected_tools": ["get_referral_info"],
        "turn_guidance": {
            1: "Ask about the referral program and how it works.",
            2: "Ask about the rewards or limits.",
            3: "Ask to get your referral link or thank the agent.",
        },
    },
    "referral_create": {
        "expected_tools": ["get_referral_info", "create_referral_link"],
        "turn_guidance": {
            1: "Ask about the referral program briefly, then ask for your link.",
            2: "React to the link. Ask how to share it or about the rewards.",
            3: "Thank the agent.",
        },
    },
    "price_filter": {
        "expected_tools": ["search_listings", "get_recommendations"],
        "turn_guidance": {
            1: "Search for services with a specific budget constraint (mention a dollar amount).",
            2: "Ask for details about the cheapest or best-value option.",
            3: "Ask to save it or compare options.",
        },
    },
    "contextual_reference": {
        "expected_tools": ["search_listings", "add_to_shortlist"],
        "turn_guidance": {
            1: "Search for some services first.",
            2: "Refer to the results using 'the first one', 'that one', 'both', etc.",
            3: "Do another action with a contextual reference.",
        },
    },
    "greeting_chitchat": {
        "expected_tools": [],
        "turn_guidance": {
            1: "Send a greeting or ask what the assistant can do.",
            2: "React to the answer with a brief follow-up or ask to get started.",
            3: "Thank the agent or transition to an actual task.",
        },
    },
}


def _get_turn_guidance(intent: str, turn_number: int) -> str:
    plan = INTENT_TOOL_PLANS.get(intent)
    if not plan:
        return ""
    guidance = plan["turn_guidance"].get(turn_number, "")
    if not guidance:
        max_defined = max(plan["turn_guidance"].keys())
        guidance = plan["turn_guidance"].get(max_defined, "")
    return guidance


# ---------------------------------------------------------------------------
# Diversity Axes — varied per trace for distinct phrasings within a cluster
# ---------------------------------------------------------------------------

VOICE_STYLES = [
    "Sound like a first-time user exploring the marketplace.",
    "Sound like a busy professional who wants quick answers.",
    "Use a warm, conversational tone like chatting with a friend.",
    "Use a more formal, business-like tone.",
    "Sound slightly impatient — you've been looking for a while.",
    "Sound excited about starting a new project.",
    "Sound cautious and budget-conscious.",
    "Sound like a repeat user who knows how the platform works.",
    "Sound like someone comparing NexusMarket to other freelance platforms.",
    "Sound cooperative but slightly confused about how things work.",
    "Sound confident and direct — you know exactly what you want.",
    "Sound like you're in a rush and need something done fast.",
]

SHAPE_HINTS = [
    "Use exactly one short sentence.",
    "Use at most two short sentences.",
    "Lead with a question, then one brief clause if needed.",
    "Lead with a short statement, then one follow-up question.",
    "Skip greetings; jump straight to the request.",
    "Use a minimal greeting (Hi/Hello) then the request.",
    "Include one specific detail about your project or needs.",
    "Keep it very brief; abbreviations OK if natural.",
]

PHRASING_AXES = [
    "Neutral natural phrasing.",
    "More formal register than typical chat.",
    "More colloquial than typical chat.",
    "Put the core ask in the first half of the message.",
    "Put the core ask at the end after brief context.",
    "Mention a mild time constraint or urgency.",
    "Sound like you already browsed the site but need help with this step.",
    "Use a different opening word than you would in a template.",
]

# ---------------------------------------------------------------------------
# Cluster Profiles — preset intent->count configurations
# ---------------------------------------------------------------------------

CLUSTER_PROFILES: dict[str, dict[str, int]] = {
    "small": {intent: 3 for intent in INTENT_CATALOG},
    "balanced": {intent: 5 for intent in INTENT_CATALOG},
    "large": {intent: 10 for intent in INTENT_CATALOG},
    "buyer_journey": {
        "search_services": 10,
        "get_listing_details": 8,
        "compare_listings": 8,
        "get_recommendations": 8,
        "shortlist_add": 6,
        "create_inquiry": 6,
        "price_filter": 6,
    },
    "shortlist_flow": {
        "shortlist_add": 10,
        "shortlist_view": 8,
        "shortlist_remove": 6,
        "search_services": 6,
        "contextual_reference": 5,
    },
    "help_and_support": {
        "ask_help_general": 8,
        "ask_help_payment": 8,
        "ask_help_hiring": 8,
        "support_create": 6,
        "support_status": 6,
        "greeting_chitchat": 4,
    },
    "seller_focus": {
        "seller_insights": 10,
        "browse_category": 5,
        "price_filter": 5,
    },
    "alerts_and_referrals": {
        "alert_create": 8,
        "alert_view": 6,
        "alert_delete": 5,
        "referral_info": 6,
        "referral_create": 5,
    },
    "full": {intent: 5 for intent in INTENT_CATALOG},
}


# ---------------------------------------------------------------------------
# LLM for user-message generation (uses Google GenAI matching the agent)
# ---------------------------------------------------------------------------

def _get_genai_client():
    try:
        from google import genai
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set in .env")
        return genai.Client(api_key=api_key)
    except ImportError:
        raise ImportError("google-genai package required. Install with: pip install google-genai")


_genai_client = None


def _get_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = _get_genai_client()
    return _genai_client


GENERATOR_MODEL = os.getenv("TRACE_GEN_MODEL", "gemini-2.0-flash")

# Concurrency limit for GenAI calls to avoid 429 rate-limit errors.
# Gemini free tier allows ~15 RPM; set higher for paid tiers.
_MAX_CONCURRENT_GENAI = int(os.getenv("TRACE_GEN_CONCURRENCY", "3"))
_genai_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _genai_semaphore
    if _genai_semaphore is None:
        _genai_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_GENAI)
    return _genai_semaphore


async def _genai_generate_with_retry(prompt: str, max_retries: int = 6) -> str:
    """Call GenAI with semaphore-based concurrency control and exponential backoff on 429."""
    from google.genai import types as genai_types
    from google.genai.errors import ClientError

    client = _get_client()
    sem = _get_semaphore()

    for attempt in range(max_retries + 1):
        async with sem:
            try:
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=GENERATOR_MODEL,
                    contents=[genai_types.Content(
                        role="user",
                        parts=[genai_types.Part.from_text(text=prompt)],
                    )],
                    config=genai_types.GenerateContentConfig(
                        temperature=0.8,
                        max_output_tokens=256,
                    ),
                )
                # Small delay after success to stay under RPM limits
                await asyncio.sleep(float(os.getenv("TRACE_GEN_DELAY", "2.0")))
                return response.text or ""
            except ClientError as e:
                if e.code == 429 and attempt < max_retries:
                    # Exponential backoff: 4s, 8s, 16s, 32s, 64s, 128s
                    wait = (4 * (2 ** attempt)) + random.uniform(1, 3)
                    print(f"    [rate-limit] 429 from GenAI, retrying in {wait:.0f}s (attempt {attempt + 1}/{max_retries})...")
                    await asyncio.sleep(wait)
                    continue
                if e.code == 429:
                    print(f"    [rate-limit] Exhausted retries. Using fallback message.")
                    return ""
                raise

    return ""


# ---------------------------------------------------------------------------
# Trace Configuration
# ---------------------------------------------------------------------------

@dataclass
class TraceConfig:
    base_url: str
    timeout: int
    intent_counts: dict[str, int]
    thread_prefix: str
    seed: int | None = None
    sequential: bool = False
    prompt: str | None = None
    profile_name: str | None = None
    max_turns: int = 3
    template_mode: bool = False
    offline_mode: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json_payload(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    code_block_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        try:
            payload = json.loads(code_block_match.group(1))
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r"\{[^{}]*\"message\"[^{}]*\}", text)
    if brace_match:
        try:
            payload = json.loads(brace_match.group(0))
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------------------------
# User-message generation via LLM
# ---------------------------------------------------------------------------

def _build_generation_prompt(
    intent: str,
    persona_key: str,
    sample_index: int,
    total_samples: int,
    *,
    voice_style: str = "",
    shape_hint: str = "",
    phrasing_axis: str = "",
    extra_guidance: str | None = None,
    multi_turn: bool = False,
) -> str:
    intent_info = INTENT_CATALOG[intent]
    persona = BUYER_PERSONAS[persona_key]
    sample_queries = intent_info.get("sample_queries", [])

    sample_queries_block = ""
    if sample_queries:
        bullets = "\n".join(f"  - {q}" for q in sample_queries)
        anchor = sample_queries[sample_index % len(sample_queries)]
        sample_queries_block = f"""
Reference sample queries (same meaning, fresh wording — do NOT copy verbatim):
{bullets}
For this trace (sample {sample_index + 1} of {total_samples}), lean toward the theme of:
  «{anchor}»
"""

    discriminator = INTENT_DISCRIMINATORS.get(intent, "Keep the message clearly about this intent.")

    diversity_block = ""
    if voice_style and shape_hint and phrasing_axis:
        diversity_block = f"""
Variety constraints (make this trace clearly different from other traces of the same intent):
  Voice: {voice_style}
  Shape: {shape_hint}
  Phrasing: {phrasing_axis}
  This is sample {sample_index + 1} of {total_samples} — vary openings, vocabulary, and structure."""

    turn_plan_block = ""
    if multi_turn:
        turn1_guidance = _get_turn_guidance(intent, 1)
        expected_tools = intent_info.get("expected_tools", [])
        tools_str = ", ".join(expected_tools) if expected_tools else "none (chitchat)"
        turn_plan_block = f"""
This is turn 1 of a multi-turn conversation.
Your goal for turn 1: {turn1_guidance}
Tools expected during this conversation: {tools_str}
Don't cram everything into one message — handle turn 1's objective only."""

    return f"""You are simulating a customer on NexusMarket, a freelance services marketplace.

You are playing the role of:
- Name: {persona["name"]}
- Profile: {persona["profile"]}
- Budget: {persona["budget_level"]}
- Interests: {", ".join(persona["interests"])}

Current intent: {intent}
Intent description: {intent_info["description"]}
Guidance: {intent_info["guidance"]}
{sample_queries_block}
Wording separation (required so intents stay distinct in clustering):
{discriminator}

Rules:
- Produce ONE realistic customer message for this intent.
- Stay in character as the buyer described above.
- Keep the message concise (1-2 lines), natural, and conversational.
- When referencing listings, use valid IDs (listing-001 through listing-015).
- Valid categories: Development, Design, Marketing, Writing, Video, Data & AI.
{turn_plan_block}
{diversity_block}

Additional guidance:
{extra_guidance or "None"}

Respond as strict JSON only:
{{"message": "<user message>"}}""".strip()


async def _generate_user_message(
    intent: str,
    persona_key: str,
    sample_index: int,
    total_samples: int,
    *,
    voice_style: str = "",
    shape_hint: str = "",
    phrasing_axis: str = "",
    extra_guidance: str | None = None,
    multi_turn: bool = False,
) -> str:
    generation_prompt = _build_generation_prompt(
        intent=intent,
        persona_key=persona_key,
        sample_index=sample_index,
        total_samples=total_samples,
        voice_style=voice_style,
        shape_hint=shape_hint,
        phrasing_axis=phrasing_axis,
        extra_guidance=extra_guidance,
        multi_turn=multi_turn,
    )

    raw_content = await _genai_generate_with_retry(generation_prompt)
    payload = _extract_json_payload(raw_content)
    if payload and isinstance(payload.get("message"), str) and payload["message"].strip():
        return payload["message"].strip()

    return "Hi, I'm looking for help with a project. Can you show me what's available?"


# ---------------------------------------------------------------------------
# Follow-up message generation (multi-turn)
# ---------------------------------------------------------------------------

def _build_followup_prompt(
    intent: str,
    persona_key: str,
    conversation_history: list[dict[str, str]],
    turn_number: int,
    max_turns: int,
) -> str:
    intent_info = INTENT_CATALOG[intent]
    persona = BUYER_PERSONAS[persona_key]

    history_lines = []
    for msg in conversation_history:
        role = msg["role"].upper()
        content = msg["content"][:300]
        history_lines.append(f"  {role}: {content}")
    history_block = "\n".join(history_lines)

    turn_guidance = _get_turn_guidance(intent, turn_number)
    is_final_turn = turn_number >= max_turns

    if is_final_turn:
        progression_hint = (
            "This is the FINAL turn. Wrap up naturally — confirm, thank, "
            "or ask one brief closing question."
        )
    else:
        progression_hint = (
            "Move the conversation forward naturally. "
            "React to what the agent said and make a logical next request."
        )

    return f"""You are simulating a customer on NexusMarket, a freelance services marketplace.

You are playing:
- Name: {persona["name"]}
- Profile: {persona["profile"]}
- Budget: {persona["budget_level"]}
- Interests: {", ".join(persona["interests"])}

Overall intent: {intent}
Intent description: {intent_info["description"]}

This is turn {turn_number} of {max_turns}.

YOUR OBJECTIVE FOR THIS TURN:
{turn_guidance}

Conversation so far:
{history_block}

Rules:
- Produce ONE realistic follow-up customer message.
- Stay in character. Keep it concise (1-2 lines).
- React naturally to what the agent just said.
- {progression_hint}
- When referencing listings use valid IDs (listing-001 through listing-015).

Respond as strict JSON only:
{{"message": "<user message>"}}""".strip()


async def _generate_followup_message(
    intent: str,
    persona_key: str,
    conversation_history: list[dict[str, str]],
    turn_number: int,
    max_turns: int,
) -> str:
    followup_prompt = _build_followup_prompt(
        intent=intent,
        persona_key=persona_key,
        conversation_history=conversation_history,
        turn_number=turn_number,
        max_turns=max_turns,
    )

    raw_content = await _genai_generate_with_retry(followup_prompt)
    payload = _extract_json_payload(raw_content)
    if payload and isinstance(payload.get("message"), str) and payload["message"].strip():
        return payload["message"].strip()

    return "Can you tell me more about that?"


# ---------------------------------------------------------------------------
# Template-based message generation (zero LLM cost)
# ---------------------------------------------------------------------------

_TEMPLATE_PREFIXES = [
    "Hi, ",
    "Hey, ",
    "Hello — ",
    "",
    "Quick question: ",
    "Hi there, ",
]

_TEMPLATE_FOLLOWUPS_BY_TURN: dict[int, list[str]] = {
    2: [
        "Can you tell me more about the first option?",
        "What's the delivery time on that?",
        "Interesting — how much does that cost?",
        "Which one has the best reviews?",
        "Can you give me more details on that?",
        "What about the pricing and timeline?",
        "That sounds good. What are the next steps?",
        "Is there anything cheaper available?",
        "Can I see the seller's profile for that one?",
        "Add the best one to my shortlist.",
    ],
    3: [
        "Thanks, that helps! One more question — what's the refund policy?",
        "Great. Can you save that to my shortlist?",
        "Perfect, I'll go with that. How do I hire them?",
        "Thanks for the info. That's all I needed.",
        "Cool. Can you compare those two for me?",
        "Nice — I'll think about it. Thanks!",
        "Is there a way to get notified about new options?",
        "Can I send an inquiry to that seller?",
        "What if I need it done faster?",
        "Alright, thanks for the help!",
    ],
}


def _template_user_message(
    intent: str,
    persona_key: str,
    sample_index: int,
    rng: random.Random,
) -> str:
    """Pick a sample query and optionally add a persona-flavored prefix."""
    intent_info = INTENT_CATALOG[intent]
    sample_queries = intent_info.get("sample_queries", [])
    if not sample_queries:
        return "Hi, can you help me with something?"

    query = sample_queries[sample_index % len(sample_queries)]
    prefix = rng.choice(_TEMPLATE_PREFIXES)

    if prefix and query[0].isupper():
        query = query[0].lower() + query[1:]

    return f"{prefix}{query}"


def _template_followup_message(
    turn_number: int,
    rng: random.Random,
) -> str:
    """Pick a pre-written follow-up for the given turn number."""
    pool = _TEMPLATE_FOLLOWUPS_BY_TURN.get(turn_number)
    if not pool:
        pool = _TEMPLATE_FOLLOWUPS_BY_TURN[max(_TEMPLATE_FOLLOWUPS_BY_TURN.keys())]
    return rng.choice(pool)


# ---------------------------------------------------------------------------
# Offline / mock agent replies (zero LLM and no backend)
# ---------------------------------------------------------------------------

_MOCK_AGENT_TURN1 = [
    "I found several listings that may fit. Highlights: listing-001, listing-002, and listing-003. "
    "Tell me which ID you want details on, or I can compare them.",
    "Here are some options from the marketplace — listing-004 and listing-005 look like strong matches. "
    "Want me to open one or add any to your shortlist?",
    "I pulled a few relevant services (listing-006, listing-007). I can share pricing, reviews, or next steps.",
]

_MOCK_AGENT_FOLLOWUP = [
    "listing-001 is $2,500 with strong reviews; delivery is about two weeks. "
    "I can compare it with listing-002 or add it to your shortlist.",
    "Sure — I can get more details, compare two listings, or help you send an inquiry to the seller.",
    "Got it. Let me know if you want pricing, timeline, or help hiring from your shortlist.",
]


def _mock_agent_response(turn_number: int, rng: random.Random) -> str:
    pool = _MOCK_AGENT_TURN1 if turn_number <= 1 else _MOCK_AGENT_FOLLOWUP
    return rng.choice(pool)


# ---------------------------------------------------------------------------
# Backend communication
# ---------------------------------------------------------------------------

def _marketplace_auth_headers() -> dict[str, str]:
    t = (os.environ.get("MARKETPLACE_API_BEARER_TOKEN") or "").strip()
    if not t:
        return {}
    return {"Authorization": f"Bearer {t}"}


async def _send_to_agent(
    client: httpx.AsyncClient,
    base_url: str,
    timeout: int,
    session_id: str,
    message: str,
) -> tuple[bool, str, str]:
    endpoint = f"{base_url.rstrip('/')}/api/chat"
    payload: dict[str, Any] = {
        "message": message,
        "session_id": session_id,
    }

    try:
        response = await client.post(
            endpoint, json=payload, timeout=timeout, headers=_marketplace_auth_headers()
        )
    except httpx.RequestError as exc:
        return False, session_id, f"Connection error: {exc}"

    if response.status_code >= 400:
        return False, session_id, f"HTTP {response.status_code}: {response.text}"

    try:
        body = response.json()
    except ValueError:
        return False, session_id, "Non-JSON response from backend"

    next_session_id = str(body.get("session_id") or session_id)
    assistant_text = body.get("response") or body.get("error") or "No response returned"
    return True, next_session_id, str(assistant_text)


# ---------------------------------------------------------------------------
# Single trace execution
# ---------------------------------------------------------------------------

async def _run_single_trace(
    client: httpx.AsyncClient | None,
    config: TraceConfig,
    intent: str,
    persona_key: str,
    sample_index: int,
    total_samples: int,
    rng: random.Random,
) -> dict[str, Any]:
    trace_id = f"{config.thread_prefix}-{intent}-{sample_index}"
    session_id = trace_id
    tag = f"[{intent}:{sample_index}]"
    max_turns = config.max_turns
    multi_turn = max_turns > 1

    voice_style = rng.choice(VOICE_STYLES)
    shape_hint = rng.choice(SHAPE_HINTS)
    phrasing_axis = PHRASING_AXES[sample_index % len(PHRASING_AXES)]

    # -- Turn 1: initial user message --
    if config.offline_mode:
        mode_label = "offline"
    else:
        mode_label = "template" if config.template_mode else "llm"
    print(f"  {tag} Turn 1/{max_turns} — generating message ({mode_label}, persona={persona_key})...")

    if config.offline_mode or config.template_mode:
        user_message = _template_user_message(intent, persona_key, sample_index, rng)
    else:
        user_message = await _generate_user_message(
            intent=intent,
            persona_key=persona_key,
            sample_index=sample_index,
            total_samples=total_samples,
            voice_style=voice_style,
            shape_hint=shape_hint,
            phrasing_axis=phrasing_axis,
            extra_guidance=config.prompt,
            multi_turn=multi_turn,
        )
    print(f"  {tag} User: {user_message}")

    if config.offline_mode:
        ok = True
        agent_response = _mock_agent_response(1, rng)
    else:
        ok, session_id, agent_response = await _send_to_agent(
            client=client,
            base_url=config.base_url,
            timeout=config.timeout,
            session_id=session_id,
            message=user_message,
        )

    preview = agent_response[:120] + ("..." if len(agent_response) > 120 else "")
    agent_label = "Mock" if config.offline_mode else "Agent"
    print(f"  {tag} {agent_label}: {preview}")

    turns: list[dict[str, str]] = [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": agent_response},
    ]

    if not ok:
        print(f"  {tag} [FAILED] {agent_response}")
        return {
            "trace_id": trace_id,
            "intent": intent,
            "persona": persona_key,
            "session_id": session_id,
            "turns": turns,
            "num_turns": 1,
            "success": False,
        }

    # -- Subsequent turns --
    for turn_num in range(2, max_turns + 1):
        print(f"  {tag} Turn {turn_num}/{max_turns} — generating follow-up ({mode_label})...")

        if config.offline_mode or config.template_mode:
            followup = _template_followup_message(turn_num, rng)
        else:
            followup = await _generate_followup_message(
                intent=intent,
                persona_key=persona_key,
                conversation_history=turns,
                turn_number=turn_num,
                max_turns=max_turns,
            )
        print(f"  {tag} User: {followup}")

        if config.offline_mode:
            ok = True
            agent_response = _mock_agent_response(turn_num, rng)
        else:
            ok, session_id, agent_response = await _send_to_agent(
                client=client,
                base_url=config.base_url,
                timeout=config.timeout,
                session_id=session_id,
                message=followup,
            )

        preview = agent_response[:120] + ("..." if len(agent_response) > 120 else "")
        print(f"  {tag} {agent_label}: {preview}")

        turns.append({"role": "user", "content": followup})
        turns.append({"role": "assistant", "content": agent_response})

        if not ok:
            print(f"  {tag} [FAILED at turn {turn_num}] {agent_response}")
            break

    return {
        "trace_id": trace_id,
        "intent": intent,
        "persona": persona_key,
        "session_id": session_id,
        "turns": turns,
        "num_turns": len(turns) // 2,
        "success": ok,
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def _build_work_items(
    config: TraceConfig,
    rng: random.Random,
) -> list[tuple[str, str, int, int]]:
    personas = list(BUYER_PERSONAS.keys())
    work: list[tuple[str, str, int, int]] = []

    for intent, count in config.intent_counts.items():
        for sample_index in range(count):
            persona_key = personas[sample_index % len(personas)]
            work.append((intent, persona_key, sample_index, count))

    rng.shuffle(work)
    return work


async def run_traces(config: TraceConfig) -> dict[str, Any]:
    seed = config.seed if config.seed is not None else random.randrange(1, 2**31 - 1)
    rng = random.Random(seed)

    work_items = _build_work_items(config, rng)
    total = len(work_items)

    print(f"\nGenerating {total} traces across {len(config.intent_counts)} intents...\n")

    traces: list[dict[str, Any]] = []

    async def _run_all(client: httpx.AsyncClient | None) -> list[dict[str, Any]]:
        if config.sequential:
            out: list[dict[str, Any]] = []
            for i, (intent, persona, sample_idx, total_samples) in enumerate(work_items):
                print(f"\n[{i + 1}/{total}] Intent: {intent}")
                out.append(
                    await _run_single_trace(
                        client, config, intent, persona, sample_idx, total_samples, rng,
                    )
                )
            return out
        tasks = [
            _run_single_trace(
                client, config, intent, persona, sample_idx, total_samples, rng,
            )
            for intent, persona, sample_idx, total_samples in work_items
        ]
        return list(await asyncio.gather(*tasks))

    if config.offline_mode:
        traces = await _run_all(None)
    else:
        async with httpx.AsyncClient() as client:
            traces = await _run_all(client)

    result = {
        "metadata": {
            "generated_at": datetime.now(UTC).isoformat(),
            "profile": config.profile_name,
            "seed": seed,
            "intent_counts": dict(sorted(config.intent_counts.items())),
            "total_traces": total,
            "base_url": config.base_url,
            "thread_prefix": config.thread_prefix,
            "max_turns": config.max_turns,
            "offline": config.offline_mode,
            "template": config.template_mode or config.offline_mode,
        },
        "traces": traces,
    }

    log_path = _save_traces(result, config.thread_prefix)
    result["metadata"]["log_file"] = log_path
    return result


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _save_traces(payload: dict[str, Any], thread_prefix: str) -> str:
    logs_dir = Path(__file__).resolve().parent / "trace_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    file_name = f"traces_{thread_prefix}_{timestamp}.json"
    log_path = logs_dir / file_name

    with log_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return str(log_path)


def _print_summary(result: dict[str, Any]) -> None:
    meta = result["metadata"]
    traces = result["traces"]
    total = len(traces)
    success = sum(1 for t in traces if t["success"])

    intent_breakdown: dict[str, dict[str, int]] = {}
    for t in traces:
        intent = t["intent"]
        if intent not in intent_breakdown:
            intent_breakdown[intent] = {"total": 0, "success": 0}
        intent_breakdown[intent]["total"] += 1
        if t["success"]:
            intent_breakdown[intent]["success"] += 1

    print(f"\n{'=' * 60}")
    print("Trace Generation Complete")
    print(f"{'=' * 60}")
    print(f"  Profile:          {meta.get('profile') or 'custom'}")
    total_turns = sum(t.get("num_turns", 1) for t in traces)
    print(f"  Total traces:     {total}")
    print(f"  Successful:       {success}/{total}")
    print(f"  Max turns/trace:  {meta.get('max_turns', 1)}")
    print(f"  Total turns:      {total_turns}")
    print(f"  Intent clusters:  {len(intent_breakdown)}")
    print(f"  Seed:             {meta['seed']}")
    print(f"  Log file:         {meta.get('log_file', 'N/A')}")

    print(f"\n  {'Intent':<28s} {'Traces':>7s} {'OK':>5s}")
    print(f"  {'-' * 28} {'-' * 7} {'-' * 5}")
    for intent in sorted(intent_breakdown):
        info = intent_breakdown[intent]
        print(f"  {intent:<28s} {info['total']:>7d} {info['success']:>5d}")
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_intent_count(value: str) -> tuple[str, int]:
    raw = value.strip()
    if ":" not in raw:
        raise argparse.ArgumentTypeError(f"Expected INTENT:COUNT, got {value!r}")
    intent_part, _, count_str = raw.rpartition(":")
    intent = intent_part.strip()
    if not intent:
        raise argparse.ArgumentTypeError(f"Expected INTENT:COUNT, got {value!r}")
    try:
        count = int(count_str.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Count must be integer in {value!r}") from exc
    if count < 1:
        raise argparse.ArgumentTypeError(f"Count must be >= 1 in {value!r}")
    return intent, count


def _resolve_intent_counts(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> tuple[dict[str, int], str | None]:
    profile_name: str | None = None

    if args.samples is not None:
        if args.profile is not None:
            parser.error("--samples and --profile are mutually exclusive.")
        counts = {intent: args.samples for intent in INTENT_CATALOG}
        if args.intent:
            for intent, n in args.intent:
                if intent not in INTENT_CATALOG:
                    parser.error(f"Unknown intent: {intent}. Use --list-intents.")
                counts[intent] = n
        return counts, profile_name

    if args.profile is not None:
        if args.profile not in CLUSTER_PROFILES:
            parser.error(
                f"Unknown profile: {args.profile!r}. "
                f"Available: {', '.join(CLUSTER_PROFILES)}. Use --list-profiles."
            )
        profile_name = args.profile
        counts = dict(CLUSTER_PROFILES[args.profile])
        if args.intent:
            for intent, n in args.intent:
                if intent not in INTENT_CATALOG:
                    parser.error(f"Unknown intent: {intent}. Use --list-intents.")
                counts[intent] = n
        return counts, profile_name

    if args.intent:
        counts: dict[str, int] = {}
        for intent, n in args.intent:
            if intent not in INTENT_CATALOG:
                parser.error(f"Unknown intent: {intent}. Use --list-intents.")
            counts[intent] = n
        return counts, profile_name

    profile_name = "balanced"
    return dict(CLUSTER_PROFILES["balanced"]), profile_name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate clusterable traces for the NexusMarket AI agent.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  %(prog)s --samples 5                             # 5 traces per intent (all intents)
  %(prog)s --samples 3 --turns 4                   # 4-turn convos
  %(prog)s --profile buyer_journey --turns 3       # multi-turn buyer journey
  %(prog)s --profile balanced --intent search_services:15
  %(prog)s --intent search_services:10 compare_listings:8
  %(prog)s --list-intents                          # show available intents
  %(prog)s --list-profiles                         # show available profiles
  %(prog)s --offline --samples 5                    # save JSON only, no LLM/API
""",
    )

    gen_group = parser.add_argument_group("generation")
    gen_group.add_argument(
        "--samples", type=int, default=None, metavar="N",
        help="Generate N traces for every intent (mutually exclusive with --profile)",
    )
    gen_group.add_argument(
        "--profile", default=None, metavar="NAME",
        help=f"Use a preset cluster profile ({', '.join(CLUSTER_PROFILES)})",
    )
    gen_group.add_argument(
        "--intent", nargs="+", type=_parse_intent_count, metavar="INTENT:COUNT",
        help="Specify per-intent trace counts. Combine with --profile to override specific intents.",
    )

    exec_group = parser.add_argument_group("execution")
    exec_group.add_argument(
        "--base-url", default="http://localhost:3001",
        help="NexusMarket backend URL (default: http://localhost:3001)",
    )
    exec_group.add_argument(
        "--timeout", type=int, default=60,
        help="Request timeout in seconds (default: 60)",
    )
    exec_group.add_argument(
        "--sequential", action="store_true",
        help="Run traces sequentially (clearer logs; default is parallel)",
    )
    exec_group.add_argument(
        "--seed", type=int, default=None, metavar="N",
        help="RNG seed for reproducible runs",
    )
    exec_group.add_argument(
        "--thread-prefix", default=f"trace-{uuid.uuid4().hex[:8]}",
        help="Prefix for generated session/trace IDs",
    )
    exec_group.add_argument(
        "--prompt", default=None,
        help="Extra scenario guidance passed to the message generator LLM",
    )
    exec_group.add_argument(
        "--turns", type=int, default=3, metavar="N",
        help="Max user-agent turns per trace (default: 3)",
    )
    exec_group.add_argument(
        "--template", action="store_true",
        help="Use pre-written templates instead of LLM for user messages (zero generation cost)",
    )
    exec_group.add_argument(
        "--offline", action="store_true",
        help="Save traces locally with template user messages and mock agent replies; "
        "no Gemini calls and no backend required",
    )

    info_group = parser.add_argument_group("info")
    info_group.add_argument(
        "--list-intents", action="store_true",
        help="List all available intents and exit",
    )
    info_group.add_argument(
        "--list-profiles", action="store_true",
        help="List all available cluster profiles and exit",
    )

    args = parser.parse_args()

    if args.list_intents:
        print(f"\nAvailable intents ({len(INTENT_CATALOG)}):\n")
        print(f"  {'Intent':<28s} {'Tools':>5s}  Description")
        print(f"  {'-' * 28} {'-' * 5}  {'-' * 45}")
        for name, info in INTENT_CATALOG.items():
            nt = len(info.get("expected_tools", []))
            print(f"  {name:<28s} {nt:5d}  {info['description']}")
        return

    if args.list_profiles:
        print(f"\nAvailable cluster profiles ({len(CLUSTER_PROFILES)}):\n")
        for pname, counts in CLUSTER_PROFILES.items():
            total = sum(counts.values())
            intents_summary = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
            print(f"  {pname}")
            print(f"    {len(counts)} intents, {total} total traces")
            print(f"    {intents_summary}")
            print()
        return

    intent_counts, profile_name = _resolve_intent_counts(args, parser)

    if not intent_counts:
        parser.error("No intents to generate. Use --profile, --samples, or --intent.")

    offline = args.offline
    template_mode = args.template or offline

    config = TraceConfig(
        base_url=args.base_url,
        timeout=args.timeout,
        intent_counts=intent_counts,
        thread_prefix=args.thread_prefix,
        seed=args.seed,
        sequential=args.sequential,
        prompt=args.prompt,
        profile_name=profile_name,
        max_turns=max(1, args.turns),
        template_mode=template_mode,
        offline_mode=offline,
    )

    total_traces = sum(intent_counts.values())
    print("NexusMarket Trace Generator")
    if config.offline_mode:
        print("  Backend:      (skipped — offline mode)")
    else:
        print(f"  Backend:      {config.base_url}")
    print(f"  Profile:      {profile_name or 'custom'}")
    print(f"  Intents:      {len(intent_counts)}")
    print(f"  Total traces: {total_traces}")
    print(f"  Turns/trace:  {config.max_turns}")
    if config.offline_mode:
        mode = "offline (no LLM, no API)"
    elif config.template_mode:
        mode = "template (no trace-gen LLM)"
    else:
        mode = "llm-generated"
    print(f"  Mode:         {mode}")
    print(f"  Seed:         {config.seed or 'random'}")
    print(f"  Parallel:     {not config.sequential}")
    print(f"  Prefix:       {config.thread_prefix}")

    counts_display = ", ".join(f"{k}:{v}" for k, v in sorted(intent_counts.items()))
    print(f"  Counts:       {counts_display}")

    result = asyncio.run(run_traces(config))
    _print_summary(result)


if __name__ == "__main__":
    main()
