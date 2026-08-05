<!-- fineprint snapshot: perplexity/rate-limits | source: https://docs.perplexity.ai/docs/admin/rate-limits-usage-tiers -->

## What are Usage Tiers?

Usage tiers determine your rate limits and access to beta features based on your cumulative API spending. As you spend more on API credits over time, you automatically advance to higher tiers with increased rate limits. Higher tiers unlock significantly more requests per minute, and once you reach a tier, you keep it permanently with no downgrade.

You can check your current usage tier on the Pricing page in the API Console.

## Tier Progression

| Tier | Total Credits Purchased | Status |
|---|---|---|
| Tier 0 | $0 | New accounts, limited access |
| Tier 1 | $50+ | Light usage, basic limits |
| Tier 2 | $250+ | Regular usage |
| Tier 3 | $500+ | Heavy usage |
| Tier 4 | $1,000+ | Production usage |
| Tier 5 | $5,000+ | Enterprise usage |

Tiers are based on cumulative purchases across your account lifetime, not current balance.

## Gateway API Rate Limits

Gateway API requests are rate limited. When a request is rate limited, or an upstream model is overloaded, the API returns a `429` with a `Retry-After` header — retry after the indicated interval.

Requests rejected with a `429` are not billed.

## Agent API Rate Limits

The Agent API uses tier-based rate limits that scale with your usage tier:

| Tier | QPS (Queries per Second) | Requests per Minute |
|---|---|---|
| Tier 0 | 1 QPS | 50/min |
| Tier 1 | 3 QPS | 150/min |
| Tier 2 | 8 QPS | 500/min |
| Tier 3 | 17 QPS | 1,000/min |
| Tier 4 | 33 QPS | 2,000/min |
| Tier 5 | 33 QPS | 2,000/min |

## Search API Rate Limits

The Search API has separate rate limits that apply to all usage tiers:

| Endpoint | Rate Limit | Burst Capacity |
|---|---|---|
| POST `/search` | 50 query units per second | 50 query units |

Search Rate Limiter Behavior:

- Single-query request: Consumes 1 query unit
- Multi-query request: Consumes 1 query unit for each query in the array
- Burst: Can consume 50 query units instantly
- Sustained: 50 query units per second on average

Billing and rate limiting use different units. A successful request containing five queries is one billable Search API request, but it consumes five rate-limit units. Search rate limits are independent of your usage tier and apply consistently across all accounts using the same leaky bucket algorithm. See Search API pricing for billing details.

## Sonar API Rate Limits

The Sonar API uses tier-based rate limits that scale with your usage tier:

- Tier 0
- Tier 1
- Tier 2
- Tier 3
- Tier 4
- Tier 5

| Model | Requests per minute (RPM) |
|---|---|
| `sonar-deep-research` | 5 |
| `sonar-reasoning-pro` | 50 |
| `sonar-pro` | 50 |
| `sonar` | 50 |
| POST `/v1/async/sonar` | 5 |
| GET `/v1/async/sonar` | 3000 |
| GET `/v1/async/sonar/{request_id}` | 6000 |

| Model | Requests per minute (RPM) |
|---|---|
| `sonar-deep-research` | 10 |
| `sonar-reasoning-pro` | 150 |
| `sonar-pro` | 150 |
| `sonar` | 150 |
| POST `/v1/async/sonar` | 10 |
| GET `/v1/async/sonar` | 3000 |
| GET `/v1/async/sonar/{request_id}` | 6000 |

| Model | Requests per minute (RPM) |
|---|---|
| `sonar-deep-research` | 20 |
| `sonar-reasoning-pro` | 500 |
| `sonar-pro` | 500 |
| `sonar` | 500 |
| POST `/v1/async/sonar` | 20 |
| GET `/v1/async/sonar` | 3000 |
| GET `/v1/async/sonar/{request_id}` | 6000 |

| Model | Requests per minute (RPM) |
|---|---|
| `sonar-deep-research` | 40 |
| `sonar-reasoning-pro` | 1,000 |
| `sonar-pro` | 1,000 |
| `sonar` | 1,000 |
| POST `/v1/async/sonar` | 40 |
| GET `/v1/async/sonar` | 3000 |
| GET `/v1/async/sonar/{request_id}` | 6000 |

| Model | Requests per minute (RPM) |
|---|---|
| `sonar-deep-research` | 60 |
| `sonar-reasoning-pro` | 4,000 |
| `sonar-pro` | 4,000 |
| `sonar` | 4,000 |
| POST `/v1/async/sonar` | 60 |
| GET `/v1/async/sonar` | 3000 |
| GET `/v1/async/sonar/{request_id}` | 6000 |

| Model | Requests per minute (RPM) |
|---|---|
| `sonar-deep-research` | 100 |
| `sonar-reasoning-pro` | 4,000 |
| `sonar-pro` | 4,000 |
| `sonar` | 4,000 |
| POST `/v1/async/sonar` | 100 |
| GET `/v1/async/sonar` | 3000 |
| GET `/v1/async/sonar/{request_id}` | 6000 |

## Embeddings API Rate Limits

The Embeddings API uses tier-based rate limits that scale with your usage tier. Limits are higher than other APIs because each request is a single forward pass on an elastic backend.

| Tier | QPS (Queries per Second) |
|---|---|
| Tier 0 | 85 QPS |
| Tiers 1–3 | 170 QPS |
| Tiers 4–5 | 335 QPS |

### Contextualized Embeddings

Contextualized embeddings have separate, higher limits (5× the standard embeddings tiers):

| Tier | QPS (Queries per Second) |
|---|---|
| Tier 0 | 415 QPS |
| Tiers 1–3 | 835 QPS |
| Tiers 4–5 | 1,670 QPS |

Contextualized embeddings are rate limited by total chunks, not by request count.

## How Rate Limiting Works

Our rate limiting system uses a leaky bucket algorithm that allows for burst traffic while maintaining strict long-term rate control.

### Technical Implementation

Leaky Bucket Algorithm Explained

The leaky bucket algorithm works like a bucket with a small hole in the bottom:

- Bucket Capacity: Maximum number of requests you can make instantly (burst capacity)
- Leak Rate: How quickly tokens leak out of the bucket (your rate limit)
- Token Refill: Tokens refill continuously at regular intervals based on your rate limit

This design allows legitimate burst traffic when you need it, prevents sustained abuse, and ensures predictable and fair rate enforcement across all users.

Rate Limiter Behavior Example

Let's examine how 50 requests per second works in practice. With a capacity of 50 tokens and a leak rate of 50 tokens per second, one token refills every 20ms.Scenario 1: Burst Traffic

```
Time 0.0s: Bucket full (50 tokens)
→ Send 50 requests instantly → ALL ALLOWED
→ Send 51st request → REJECTED (bucket empty)

Time 0.020s: 1 token refilled
→ Send 1 request → ALLOWED
→ Send 2nd request → REJECTED

Time 0.040s: 1 more token refilled
→ Send 1 request → ALLOWED
```

Scenario 2: Steady 50 QPS

```
Request every 20ms:
Time 0.0s: Request → ALLOWED (50→49 tokens)
Time 0.020s: Request → ALLOWED (49+1-1=49 tokens)
Time 0.040s: Request → ALLOWED (49+1-1=49 tokens)
... maintains 49-50 tokens, all requests pass
```

Scenario 3: Slightly Over 50 QPS

```
Request every 19ms (≈52.6 QPS):
→ Eventually tokens deplete faster than refill
→ Some requests start getting rejected
→ Achieves exactly 50 QPS on average
```

Real-World Implications

The leaky bucket design means you can handle your full rate limit instantly, making it perfect for batch operations or sudden traffic spikes. There's no need to artificially spread requests when you have available burst capacity.The system enforces strict average rate limits over time while allowing quick recovery after burst usage. This provides consistent performance across different usage patterns and prevents sustained over-limit usage while maintaining fair resource allocation.When building your application, take advantage of burst capacity for batch operations, monitor your usage patterns to optimize request timing, and implement proper error handling for 429 responses.

## What Happens When You Hit Rate Limits?

When you exceed your rate limits:

1. 429 Error - Your request gets rejected with "Too Many Requests"
2. Continuous Refill - Tokens refill continuously based on your rate limit
3. Immediate Recovery - New requests become available as soon as tokens refill

Example Recovery Times:

- 50 QPS limit: 1 token refills every 20ms
- 500 QPS limit: 1 token refills every 2ms
- 1,000 QPS limit: 1 token refills every 1ms

Best Practices:

- Monitor your usage to predict when you'll need higher tiers
- Consider upgrading your tier proactively for production applications
- Implement exponential backoff with jitter in your code
- Take advantage of burst capacity for batch operations
- Don't artificially spread requests if you have available burst capacity

## Upgrading Your Tier

1

Check Current Tier

Open Usage tiers in the API Console to see your current tier and the purchase threshold for each tier.

2

Purchase More Credits

Add credits to your account through the billing section. Your tier will automatically upgrade once you reach the spending threshold.

3

Verify Upgrade

Your new rate limits take effect immediately after the tier upgrade. Check your settings page to confirm.

4

Need Even Higher Limits?

If you require custom rate limits beyond Tier 5, fill out our rate limit increase request form and we'll review your use case to accommodate your needs.

Higher tiers significantly improve your API experience with increased rate limits, especially important for production applications.

## Need Higher Rate Limits?

Need custom rate limits beyond your current tier? Fill out our rate limit increase request form and we'll review your use case to accommodate your needs.

⌘I
