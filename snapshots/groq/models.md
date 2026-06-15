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

No models found for the specified criteria.

Systems are a collection of models and tools that work together to answer a user query.

No models found for the specified criteria.

Learn More About Agentic Tooling

Discover how to build powerful applications with real-time web search and code execution

Note: Preview models are intended for evaluation purposes only and should not be used in production environments as they may be discontinued at short notice. Read more about deprecations here.

No models found for the specified criteria.

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
