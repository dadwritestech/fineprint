<!-- fineprint snapshot: deepseek/rate-limit | source: https://api-docs.deepseek.com/quick_start/rate_limit -->

# Rate Limit

DeepSeek API dynamically limits user concurrency based on server load. When you reach the concurrency limit, you will immediately receive an HTTP 429 response.

After your request is sent, it may take some time to receive a response from the server. During this period, your HTTP request will remain connected, and you may continuously receive contents in the following formats:

- Non-streaming requests: Continuously return empty lines
- Streaming requests: Continuously return SSE keep-alive comments (`: keep-alive`)

These contents do not affect the parsing of the JSON body of the response. If you are parsing the HTTP responses yourself, please ensure to handle these empty lines or comments appropriately.

If the request has not started inference after 10 minutes, the server will close the connection.
