# NexusMarket AI Agent — Abilities & Improvement Ideas

## Current Abilities

### 1. **Tool-based behavior**
- **`search_listings`** — Search by free-text `query`, optional `category`, optional `max_price`. Returns up to 5 results, scored by keyword match + rating.
- **`get_listing_details`** — Get one listing by ID plus its seller (no reviews in tool response).
- **`compare_listings`** — Compare 2+ listings; returns listings plus “cheapest” and “best_rated” analysis.
- **`get_recommendations`** — Personalized suggestions by `need` (text) and `budget` (low/medium/high). Returns up to 4 results.

### 2. **Conversation**
- **Session memory** — In-memory store per `session_id`; last 50 messages kept. Agent receives `previous_messages` so it can refer to “the first one”, “that designer”, etc.
- **Chat vs agent** — `/api/chat` uses a keyword heuristic (“need”, “looking”, “find”, “want”, “search”, “help”, “recommend”, “show”): if matched → full agent with tools; else → simple LLM reply (no tools).

### 3. **Routing**
- **`/api/agent`** — Always uses the agent (tools + history).
- **`/api/chat`** — Conditional: search-like intent → agent; else → plain chat.
- **`/api/recommend`** — Single-shot agent call for recommendations.
- **`/api/compare`** — Agent with a pre-built compare query + listing IDs.

### 4. **Data the agent can use (via tools)**
- Listings: title, category, description, price, metrics (rating, sales, delivery days, etc.), sellerId.
- Sellers: name, bio, expertise, aiProfile, metrics (per tool that returns seller).
- **Not** exposed to tools today: **reviews** (reviews exist in REST `/api/listings/{id}` and `/api/sellers/{id}` but are not in `tool_get_listing_details` or any agent tool).

### 5. **Observability**
- Netra tracing: agent span, tool spans (`tool.search_listings`, etc.), `tools_used` and tool names on spans.
- Session ID set per request for correlation.

---

## Gaps & Limitations

| Area | Limitation |
|------|------------|
| **Search** | Keyword-only scoring; no semantic/embedding search, no typo tolerance. |
| **Filters** | No min_price, sort options, or delivery-time filter in tools. |
| **Sellers** | No tool to search or browse sellers by skill/industry; agent can only see seller when attached to a listing. |
| **Reviews** | Agent never sees reviews; cannot say “highly reviewed” or quote feedback. |
| **Chat routing** | Keyword list is brittle; “I need a logo” might not trigger agent if phrasing differs. |
| **Recommendations** | Budget is low/medium/high only; no numeric range. Only 4 results. |
| **Compare** | Only cheapest vs best_rated; no delivery time, no “best value” score. |
| **Persistence** | Conversation store is in-memory; lost on restart; no user identity. |
| **Safety** | No content filters, PII handling, or guardrails beyond the model. |
| **Structured output** | Agent returns prose; no guaranteed JSON or slots for UI (e.g. “list of listing IDs”). |

---

## How to Improve Abilities

### Quick wins (minimal new surface)
1. **Include reviews in listing details**  
   In `tool_get_listing_details`, attach `reviews` for that listing (same as REST). Agent can then reference “reviews” or “what past clients said”.
2. **Add optional `min_price` and `sort` to search**  
   Extend `search_listings` with `min_price`, `sort` (e.g. `price_asc`, `rating`, `delivery`). Implement in `tool_search_listings`.
3. **Improve chat routing**  
   Replace or augment keyword list with a tiny classifier (e.g. one LLM call or small model): “Is this a search/recommendation/compare request?” → use agent; else → simple chat.
4. **Numeric budget in recommendations**  
   Add optional `max_price` (number) to `get_recommendations` and filter by it in `tool_get_recommendations`.

### New tools (more capable agent)
5. **`search_sellers`**  
   Params: e.g. `query`, `skills[]`, `industry`, `min_rating`. Return sellers (and optionally their listings count) so the agent can say “here are designers who do branding”.
6. **`get_seller_profile`**  
   By `seller_id`; return seller + their listings + reviews. Enables “tell me about this seller” and “what do people say about them?”.
7. **`get_listing_reviews`** (or keep one “listing details” that includes reviews)  
   If you prefer a separate tool: input `listing_id`, output reviews + aggregate. Agent can summarize “past buyers say…”.
8. **`get_categories`**  
   Return categories and counts so the agent can answer “what categories do you have?” and suggest categories by intent.

### Better search & recommendations
9. **Semantic search**  
   Embed listing title/description (and maybe seller bio); embed user query; rank by similarity so “something for my startup’s brand” matches design/logo even without the word “logo”.
10. **Richer compare**  
    Add delivery time, “value” score (e.g. rating/price), or a short pros/cons summary so the agent can give a structured comparison.
11. **More and configurable results**  
    Allow `limit` (e.g. 5/10) in search and recommendations; consider pagination (e.g. “next 5”) via `offset` or cursor.

### Conversation & product behavior
12. **Structured replies**  
    Add an optional “response shape” (e.g. list of listing IDs, chosen category, comparison winner) so the frontend can show cards, comparison table, or “Add to compare” without re-parsing prose.
13. **Persistent memory**  
    Store conversation (and optionally user preferences) in DB or Redis keyed by user/session so history survives restarts and can be used for “last time you liked X”.
14. **Intent + slots**  
    First step: classify intent (search / recommend / compare / seller_info / general_chat) and extract slots (category, budget, listing IDs). Then call the right tool(s) with those slots; reduces hallucinated params and improves consistency.

### Safety & robustness
15. **Guardrails**  
    Validate tool args (e.g. listing_id exists, max_price &gt; 0); reject off-topic or harmful queries with a short policy message.
16. **Rate limiting & cost**  
    Per user/session limits on agent calls and tool calls to avoid abuse and control cost.
17. **Fallback and errors**  
    If a tool errors, return a clear “I couldn’t load that right now” and optionally suggest a retry or alternative (e.g. “try another listing”).

### UX and observability
18. **Streaming**  
    Stream agent reply token-by-token so the UI feels responsive on long answers.
19. **Tool call visibility**  
    In the UI, show “Searching listings…”, “Comparing…”, “Fetching details…” when tools run, so users know the agent is “doing something”.
20. **Feedback loop**  
    Thumbs up/down or “Was this helpful?”; store with session/run for tuning prompts and tools.

---

## Feature Summary Table

| Feature | Effort | Impact | Description |
|--------|--------|--------|-------------|
| Reviews in listing details | Low | High | Agent can cite reviews and “what others said”. |
| min_price + sort in search | Low | Medium | Finer control and “sort by price/rating”. |
| Smarter chat routing | Low–Medium | Medium | Fewer missed agent invocations. |
| search_sellers | Medium | High | “Find me designers who do X.” |
| get_seller_profile | Low | Medium | “Tell me about this seller” and reviews. |
| get_categories tool | Low | Low–Medium | “What do you offer?” and category suggestions. |
| Numeric budget (max_price) | Low | Medium | “Under $500” in recommendations. |
| Semantic search | High | High | Better match for vague or long queries. |
| Richer compare | Medium | Medium | Delivery, value score, pros/cons. |
| Persistent conversation | Medium | High | History across restarts and devices. |
| Structured response shape | Medium | High | Easier UI: cards, compare table, actions. |
| Streaming | Medium | Medium | Better perceived performance. |
| Guardrails & validation | Medium | High | Safety and consistent behavior. |

---

## Suggested order of work

1. **Reviews in `tool_get_listing_details`** and **min_price/sort in search** — small code changes, clear gain.
2. **`get_categories`** and **optional `max_price` in get_recommendations** — low effort, completes “what can you do?” and budget.
3. **`search_sellers`** and **`get_seller_profile`** (with reviews) — makes the agent fully “marketplace-aware”.
4. **Smarter chat routing** (or intent/slots) — so every search-like request uses the agent.
5. **Structured output** and **streaming** — then **persistent memory** and **semantic search** as you scale.

This document can live in the repo and be updated as you implement each item (e.g. “Reviews in listing details: done in PR #X”).
