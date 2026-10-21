<!-- fineprint snapshot: perplexity/rate-limits | source: https://docs.perplexity.ai/docs/admin/rate-limits-usage-tiers -->

## What are Usage Tiers?

Usage tiers determine your rate limits and access to beta features based on your cumulative API spending. As you spend more on API credits over time, you automatically advance to higher tiers with increased rate limits. Higher tiers unlock higher request and token limits, and once you reach a tier, you keep it permanently with no downgrade.

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

## Orchestrator API Rate Limits

Orchestrator API requests are rate limited. When a request is rate limited, or an upstream model is overloaded, the API returns a `429` with a `Retry-After` header — retry after the indicated interval.

Requests rejected with a `429` are not billed.

## Agent API Rate Limits

Two kinds of limits apply to Agent API requests, and a request must pass both:

- A request limit (queries per second, QPS) for each API organization, shared across all models.
- Token limits (tokens per minute, TPM, and tokens per hour, TPH) for each API organization and model.

Both are shared across every API key in the organization. Because token limits are separate from the request limit, you can receive a `429` while your request rate is well under your QPS limit, once usage already recorded in the rolling window has reached the model's token budget. The size of the rejected request itself does not matter; the check looks only at usage already recorded. Which limit did you hit? Read `error.type` in the `429` body:

| `error.type` | Meaning | What to do |
|---|---|---|
| `request_rate_limit_exceeded` | Request limit (QPS) | Wait `Retry-After` (normally 1 second), then retry |
| `token_rate_limit_exceeded` | Token limit; the message names the window (`TPM` or `TPH`) | Wait `Retry-After` seconds, then retry with backoff |
| `overloaded` | Not a rate limit. Upstream model capacity | Retry with backoff, or use the `models` fallback list |

A `429` response carries `Retry-After` but no `x-ratelimit-*` headers.

### Agent API Request Limits

Every Agent API call counts against one request limit shared across models and API keys in the organization: `POST /v1/agent`, `GET /v1/agent/{id}` polls, cancel, resume, and file downloads, on both the `/v1/agent` and `/v1/responses` paths. There is no separate per-model request limit. Polling is not free: at 1 QPS, polling once a second leaves no room for new requests. Poll with backoff or use streaming reconnect.

| Tier | QPS (Queries per Second) |
|---|---|
| Tier 0 | 1 QPS |
| Tier 1 | 3 QPS |
| Tier 2 | 8 QPS |
| Tier 3 | 17 QPS |
| Tier 4 | 33 QPS |
| Tier 5 | 33 QPS |

The limit uses a rolling one-second window. Each accepted request counts against the organization's shared Agent API request limit for one second, regardless of the model selected. Successful responses include `x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-used`, and `x-ratelimit-reset` (Unix seconds) headers for the request limit. A `429` carries `Retry-After` instead, and no response reports token budget.

### Agent API Token Rate Limits

Token limits apply per organization and per model. Each model has its own budget, so traffic on one model does not use another model's budget. Both windows are rolling: TPM covers roughly the last minute and TPH covers roughly the last hour, and neither resets at the top of a minute or hour.

| Tier | TPM (Tokens per Minute) | TPH (Tokens per Hour) |
|---|---|---|
| Tier 0 | 5,000,000 | 300,000,000 |
| Tier 1 | 6,000,000 | 360,000,000 |
| Tier 2 | 8,000,000 | 480,000,000 |
| Tier 3 | 10,000,000 | 600,000,000 |
| Tier 4 | 13,000,000 | 780,000,000 |
| Tier 5 | 16,000,000 | 960,000,000 |

Token usage includes all input tokens (uncached, cached, and cache write) and all output tokens, including reasoning tokens. A request can make several model calls while it uses tools, including helper models used inside tools such as `fetch_url` content extraction and `sandbox`. All of them count toward the limit for the model you requested. Which model's budget: if you set `models`, the budget is the first entry's; otherwise it is `model`'s. Tokens used by fallback models are charged to that budget. If you name only a preset, usage counts against a budget keyed on the preset name you send (an alias such as `pro-search` has a separate budget from `low`). If you name only a profile, the budget is the one for the profile's first model. Before a request starts: if you are over a token limit, the API returns `429` and does not start the request. The `Retry-After` header gives the number of seconds to wait, and the message says which limit you hit:

```
{"error":{"message":"Token rate limit exceeded (TPM). Retry after the Retry-After interval.","type":"token_rate_limit_exceeded","code":429}}
```

Request limit errors use `request_rate_limit_exceeded` instead:

```
{"error":{"message":"Request rate limit exceeded, please try again later.","type":"request_rate_limit_exceeded","code":429}}
```

For token limits, `Retry-After` is the time until enough usage leaves the window, plus up to 10 seconds of random delay so that clients rejected together do not all retry at once. It is not a reservation: other requests in your organization can use the budget before your retry arrives. A request rejected for token budget still counts one request against the QPS limit, so tight retry loops on token `429`s can also trip the request limit. While a request runs: tokens are not reserved when a request starts, so other requests in your organization can use up the limit. When that happens, the request pauses before its next turn and resumes automatically when tokens are available. A pause is not an error. Do not resubmit a paused request.

- Streaming: set `stream_options.include_token_pause_events: true` to receive `response.paused` and `response.resumed` events. These events do not end the stream, and keepalive comments are sent every 15 seconds while paused. They are off by default because some OpenAI SDKs treat unknown events as regular chunks. When you reconnect with `GET /v1/agent/{id}?stream=true`, add `include_token_pause_events=true` to get them.
- Background: `GET /v1/agent/{id}` returns `status: "in_progress"` with a `paused` object. The object is removed when the request resumes or finishes.
- Non-streaming: the request cannot report a pause, so a pause appears only as added latency. The API holds the connection for at most 30 minutes, and a request your client abandons (timeout or disconnect) is cancelled server-side, even while it is paused. Use `background: true` for work that must survive a client timeout.

```
event: response.paused
data: {"type":"response.paused","reason":"token_rate_limit","window":"TPM","estimated_resume_in_seconds":12,"message":"Task paused: organization TPM budget exhausted. It will resume automatically; do not resubmit."}

event: response.resumed
data: {"type":"response.resumed"}
```

```
{"status":"in_progress","paused":{"reason":"token_rate_limit","window":"TPM","estimated_resume_at":1791302400}}
```

`window` is `TPM` or `TPH`. `estimated_resume_in_seconds` and `estimated_resume_at` (Unix time in seconds) are estimates, and `estimated_resume_at` can briefly be in the past while the request waits to resume. If `paused` is missing from a polled response, keep polling; that alone does not mean the request has resumed. Pause events have no `sequence_number`, so do not use them as `starting_after` values.

Handling token limits:

- Set client timeouts long enough to allow for pauses.
- On a `429`, wait at least `Retry-After` seconds, then retry with exponential backoff and jitter.
- Limit concurrent retries so they do not use up the limit again.
- A foreground request that times out or disconnects is cancelled, not resumed, and the tokens it used still count. If a run must outlive client timeouts, submit it with `background: true` and poll.

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

Agent API requests use a rolling one-second window rather than continuous token refill. When the window is empty, requests can arrive together up to your tier's QPS limit. Additional requests are rejected until earlier requests become more than one second old and leave the window. For example, an organization with a 33 QPS limit can make up to 33 Agent API requests in any rolling one-second period. Agent API token limits also use rolling windows, so capacity returns gradually as older usage leaves the window instead of all at once on a clock boundary.

## What Happens When You Hit Rate Limits?

When you exceed your rate limits:

1. 429 Error - Your request gets rejected with "Too Many Requests"
2. Recovery Timing - Capacity returns according to the applicable API's limiter. For the Agent API request limit, each accepted request leaves the rolling window after one second. For Agent API token limits, wait at least the `Retry-After` interval.
3. Token Limits - Agent API token limit errors use the type `token_rate_limit_exceeded` and include a `Retry-After` header. See Agent API Token Rate Limits.

Best Practices:

- Monitor your usage to predict when you'll need higher tiers
- Consider upgrading your tier proactively for production applications
- Implement exponential backoff with jitter in your code
- Pace Agent API traffic to stay within your tier's rolling one-second request limit and per-model token limits

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
