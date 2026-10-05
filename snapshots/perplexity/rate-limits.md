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

## Router API Rate Limits

Router API requests are rate limited. When a request is rate limited, or an upstream model is overloaded, the API returns a `429` with a `Retry-After` header — retry after the indicated interval.

Requests rejected with a `429` are not billed.

## Agent API Rate Limits

The standard Agent API request-count limit applies per API organization. Requests to the Responses API share this limit across models and API keys in the organization. There is no separate per-model requests-per-minute limit.

| Tier | QPS (Queries per Second) |
|---|---|
| Tier 0 | 1 QPS |
| Tier 1 | 3 QPS |
| Tier 2 | 8 QPS |
| Tier 3 | 17 QPS |
| Tier 4 | 33 QPS |
| Tier 5 | 33 QPS |

The limit uses a rolling one-second window. Each accepted request counts against the organization's shared Responses limit for one second, regardless of the model selected.

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

## Embeddings API Rate Limits

The Embeddings API uses tier-based rate limits that scale with your usage tier. Limits are higher than other APIs because each request is a single forward pass on an elastic backend.

| Tier | QPS (Queries per Second) |
|---|---|
| Tier 0 | 85 QPS |
| Tiers 1–3 | 170 QPS |
| Tiers 4–5 | 335 QPS |

### Contextualized Embeddings

Contextualized embeddings have separate, higher limits (5× the standard embeddings tiers):

| Tier | Chunks per second |
|---|---|
| Tier 0 | 415 chunks/s |
| Tiers 1–3 | 835 chunks/s |
| Tiers 4–5 | 1,670 chunks/s |

Contextualized embeddings are rate limited by total chunks, not by request count. The 16,000-chunk request limit is a structural ceiling. With an otherwise empty rate-limit window, the effective maximum is the lower of 16,000 chunks and your organization's one-second chunk allowance. Earlier requests in the window reduce the number of chunks currently available.

## How Rate Limiting Works

Rate limiter behavior differs by API; one algorithm does not apply across the platform. Refer to each API section above for the applicable limits.

### Agent API Rolling Window

Agent API requests use a rolling one-second window rather than continuous token refill. When the window is empty, requests can arrive together up to your tier's QPS limit. Additional requests are rejected until earlier requests become more than one second old and leave the window. For example, an organization with a 33 QPS limit can make up to 33 Agent API requests in any rolling one-second period.

## What Happens When You Hit Rate Limits?

When you exceed your rate limits:

1. 429 Error - Your request gets rejected with "Too Many Requests"
2. Recovery Timing - Capacity returns according to the applicable API's limiter. For the Agent API, each accepted request leaves the rolling window after one second.

Best Practices:

- Monitor your usage to predict when you'll need higher tiers
- Consider upgrading your tier proactively for production applications
- Implement exponential backoff with jitter in your code
- Pace Agent API traffic to stay within your tier's rolling one-second limit

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
