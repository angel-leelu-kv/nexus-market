"""
Simplified script to generate spans via API - focuses on fast endpoints
"""

import os
import random
import time
from typing import List

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:3001/api"
_t = (os.environ.get("MARKETPLACE_API_BEARER_TOKEN") or "").strip()
API_AUTH_HEADERS = {"Authorization": f"Bearer {_t}"} if _t else {}

# Focus on fast endpoints that don't require OpenAI API calls
def make_listings_request() -> bool:
    """Fast endpoint - no AI calls"""
    try:
        params = {
            "category": random.choice(["Development", "Design", "Marketing", None]),
            "sort": random.choice(["price_asc", "price_desc", "rating", None]),
        }
        response = requests.get(
            f"{API_BASE}/listings",
            params=params,
            headers=API_AUTH_HEADERS,
            timeout=5,
        )
        return response.status_code == 200
    except:
        return False

def make_listing_detail_request(listing_id: str) -> bool:
    """Fast endpoint - no AI calls"""
    try:
        response = requests.get(
            f"{API_BASE}/listings/{listing_id}",
            headers=API_AUTH_HEADERS,
            timeout=5,
        )
        return response.status_code == 200
    except:
        return False

def make_sellers_request() -> bool:
    """Fast endpoint - no AI calls"""
    try:
        response = requests.get(
            f"{API_BASE}/sellers", headers=API_AUTH_HEADERS, timeout=5
        )
        return response.status_code == 200
    except:
        return False

def make_categories_request() -> bool:
    """Fast endpoint - no AI calls"""
    try:
        response = requests.get(
            f"{API_BASE}/categories", headers=API_AUTH_HEADERS, timeout=5
        )
        return response.status_code == 200
    except:
        return False

def make_home_recommendations_request() -> bool:
    """Fast endpoint - no AI calls"""
    try:
        response = requests.get(
            f"{API_BASE}/home-recommendations",
            headers=API_AUTH_HEADERS,
            timeout=5,
        )
        return response.status_code == 200
    except:
        return False

def make_seller_detail_request(seller_id: str) -> bool:
    """Fast endpoint - no AI calls"""
    try:
        response = requests.get(
            f"{API_BASE}/sellers/{seller_id}",
            headers=API_AUTH_HEADERS,
            timeout=5,
        )
        return response.status_code == 200
    except:
        return False

def make_health_request() -> bool:
    """Health check endpoint"""
    try:
        response = requests.get(
            f"{API_BASE}/health", headers=API_AUTH_HEADERS, timeout=2
        )
        return response.status_code == 200
    except:
        return False

def make_ai_status_request() -> bool:
    """AI status endpoint"""
    try:
        response = requests.get(
            f"{API_BASE}/ai-status", headers=API_AUTH_HEADERS, timeout=2
        )
        return response.status_code == 200
    except:
        return False

LISTING_IDS = [
    "listing-001", "listing-002", "listing-003", "listing-004", "listing-005",
    "listing-006", "listing-007", "listing-008", "listing-009", "listing-010",
    "listing-011", "listing-012", "listing-013", "listing-014", "listing-015",
]

SELLER_IDS = [
    "seller-001", "seller-002", "seller-003", "seller-004", "seller-005",
    "seller-006", "seller-007", "seller-008",
]

def make_get_request(request_num: int) -> bool:
    """Make a GET request to any available GET endpoint"""
    request_type = random.choice([
        "listings", "listings", "listings",  # 3x weight
        "listing_detail", "listing_detail",  # 2x weight
        "sellers",
        "seller_detail",
        "categories",
        "home_recommendations",
        "health",
        "ai_status"
    ])
    
    if request_type == "listings":
        return make_listings_request()
    elif request_type == "listing_detail":
        return make_listing_detail_request(random.choice(LISTING_IDS))
    elif request_type == "sellers":
        return make_sellers_request()
    elif request_type == "seller_detail":
        return make_seller_detail_request(random.choice(SELLER_IDS))
    elif request_type == "categories":
        return make_categories_request()
    elif request_type == "home_recommendations":
        return make_home_recommendations_request()
    elif request_type == "health":
        return make_health_request()
    elif request_type == "ai_status":
        return make_ai_status_request()
    return False


def generate_spans_simple(total_requests: int = 10000):
    """Generate spans using only GET endpoints (no POST calls)"""
    print(f"\n🚀 Generating {total_requests} requests (GET endpoints only - no POST calls)...")
    print("   GET endpoints: /api/health, /api/ai-status, /api/listings, /api/listings/{{id}},")
    print("                  /api/sellers, /api/sellers/{{id}}, /api/categories, /api/home-recommendations")
    
    # Check if backend is running
    try:
        response = requests.get(
            f"{API_BASE}/health", headers=API_AUTH_HEADERS, timeout=2
        )
        if response.status_code != 200:
            print("⚠️  Backend is not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend at {API_BASE}")
        print(f"   Error: {e}")
        print(f"\n   Please start your backend first: ./start.sh")
        return
    
    start_time = time.time()
    successful = 0
    failed = 0
    
    for i in range(1, total_requests + 1):
        if make_get_request(i):
            successful += 1
        else:
            failed += 1
        
        # Progress update every 100 requests
        if i % 100 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = total_requests - i
            eta = remaining / rate if rate > 0 else 0
            print(f"  ✅ {i}/{total_requests} requests ({rate:.1f} req/sec) | "
                  f"Success: {successful} | Failed: {failed} | ETA: {eta:.0f}s")
        
        # Small delay to prevent overwhelming
        if i % 10 == 0:
            time.sleep(0.01)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Completed!")
    print(f"   Total requests: {total_requests}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Time: {elapsed:.2f} seconds")
    print(f"   Rate: {total_requests/elapsed:.1f} requests/second")
    print(f"\n💡 Each request creates spans in Netra")
    print(f"   Estimated total spans: {successful * 2} - {successful * 5}")


if __name__ == "__main__":
    import sys
    
    total_requests = 10000
    
    if len(sys.argv) > 1:
        total_requests = int(sys.argv[1])
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║        📊 NETRA SPAN GENERATOR (GET ENDPOINTS ONLY)          ║
╠══════════════════════════════════════════════════════════════╣
║  Total Requests: {total_requests:<42} ║
║  Method: GET only (no POST calls)                            ║
║  API Base: {API_BASE:<46} ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    generate_spans_simple(total_requests)
