<!-- fineprint snapshot: groq/models | source: https://console.groq.com/docs/models -->

Login

Log In

# Supported Models

Explore all available models on GroqCloud.

### Groq Compound

Groq Compound is an AI system powered by openly available models that intelligently and selectively uses built-in tools to answer user queries, including web search and code execution.

Token Speed

~450 tps

Modalities

Capabilities

### OpenAI GPT-OSS 120B

GPT-OSS 120B is OpenAI's flagship open-weight language model with 120 billion parameters, built in browser search and code execution, and reasoning capabilities.

Token Speed

~500 tps

Modalities

Capabilities

Note: Production models are intended for use in your production environments. They meet or exceed our high standards for speed, quality, and reliability. Read more here.

| MODEL ID | SPEED (T/SEC) | PRICE PER 1M TOKENS | RATE LIMITS (DEVELOPER PLAN) | CONTEXT WINDOW (TOKENS) | MAX COMPLETION TOKENS | MAX FILE SIZE |
|---|---|---|---|---|---|---|
| GPT OSS 120Bopenai/gpt-oss-120b | 500 | $0.15 input$0.60 output | 250K TPM1K RPM | 131,072 | 65,536 | - |
| GPT OSS 20Bopenai/gpt-oss-20b | 1000 | $0.075 input$0.30 output | 250K TPM1K RPM | 131,072 | 65,536 | - |
| Whisperwhisper-large-v3 | - | $0.111 per hour | 200K ASH300 RPM | - | - | 100 MB |
| Whisper Large V3 Turbowhisper-large-v3-turbo | - | $0.04 per hour | 400K ASH400 RPM | - | - | - |

Systems are a collection of models and tools that work together to answer a user query.

| MODEL ID | SPEED (T/SEC) | PRICE PER 1M TOKENS | RATE LIMITS (DEVELOPER PLAN) | CONTEXT WINDOW (TOKENS) | MAX COMPLETION TOKENS | MAX FILE SIZE |
|---|---|---|---|---|---|---|
| Compoundgroq/compound | 450 | - | 200K TPM200 RPM | 131,072 | 8,192 | - |
| Compound Minigroq/compound-mini | 450 | - | 200K TPM200 RPM | 131,072 | 8,192 | - |

Learn More About Agentic Tooling

Discover how to build powerful applications with real-time web search and code execution

Note: Preview models are intended for evaluation purposes only and should not be used in production environments as they may be discontinued at short notice. Read more about deprecations here.

| MODEL ID | SPEED (T/SEC) | PRICE PER 1M TOKENS | RATE LIMITS (DEVELOPER PLAN) | CONTEXT WINDOW (TOKENS) | MAX COMPLETION TOKENS | MAX FILE SIZE |
|---|---|---|---|---|---|---|
| Canopy Labs Orpheus Arabic Saudicanopylabs/orpheus-arabic-saudi | - | $40.00 per 1M characters | 50K TPM250 RPM | 4,000 | 50,000 | - |
| Canopy Labs Orpheus V1 Englishcanopylabs/orpheus-v1-english | - | $22.00 per 1M characters | 50K TPM250 RPM | 4,000 | 50,000 | - |
| Llama Prompt Guard 2 22Mmeta-llama/llama-prompt-guard-2-22m | - | $0.03 input$0.03 output | 30K TPM100 RPM | 512 | 512 | - |
| Prompt Guard 2 86Mmeta-llama/llama-prompt-guard-2-86m | - | $0.04 input$0.04 output | 30K TPM100 RPM | 512 | 512 | - |
| MiniMax M2.7Enterpriseminimaxai/minimax-m2.7 | 260 | ContactSales | ContactSales | 196,608 | 131,072 | - |
| Safety GPT OSS 20Bopenai/gpt-oss-safeguard-20b | 1000 | $0.075 input$0.30 output | 150K TPM1K RPM | 131,072 | 65,536 | - |
| Qwen/Qwen3.6-27Bqwen/qwen3.6-27b | 500 | $0.60 input$3.00 output | 250K TPM1K RPM | 131,072 | 16,384 | 20 MB |

Deprecated models are models that are no longer supported or will no longer be supported in the future. See our deprecation guidelines and deprecated models here.

Hosted models are directly accessible through the GroqCloud Models API endpoint using the model IDs mentioned above. You can use the `https://api.groq.com/openai/v1/models` endpoint to return a JSON list of all active models:

```
curl -X GET "https://api.groq.com/openai/v1/models" \
     -H "Authorization: Bearer $GROQ_API_KEY" \
     -H "Content-Type: application/json"
```

```
import Groq from "groq-sdk";

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const getModels = async () => {
  return await groq.models.list();
};

getModels().then((models) => {
  // console.log(models);
});
```

```
import requests
import os

api_key = os.environ.get("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

print(response.json())
```
