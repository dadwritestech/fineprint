<!-- fineprint snapshot: xai/models-pricing | source: https://docs.x.ai/developers/models -->

#### Key Information

# Models

View as Markdown

Create API keyMeet grok-4.5

### Grok 4.5

New

grok-4.5

Our flagship model for code and everything else: agentic tool calling, minimal hallucinations, configurable reasoning.

View modelTry in playground

Context500k tokens

Input$2.00 / 1M tokens

Output$6.00 / 1M tokens

ReasoningConfigurable

### Voice API

Real-time conversations, speech-to-text, and text-to-speech.

AgentStarting at $0.05 / min

TTS$15.00 / 1M chars

STT (Batch)$0.10 / hour

STT (Streaming)$0.20 / hour

Read docsTry in playground

### Imagine API

Turn ideas into reality with image and video generation.

ModesGeneration & editing

SpeedIndustry-leading

Image · 1K / 2KStarting at $0.02 / image

Video · 480p / 720p / 1080pStarting at $0.05 / sec

Read docsTry in playground

## Which model should I choose?

Your choice depends on your use case. We have dedicated models and APIs for audio, image, and video capabilities. For everything else, including code, use Grok 4.5. It is the most intelligent and fastest model we've built.

Use case

Model

Code

Grok 4.5

Chat

Grok 4.5

Images

Grok Imagine API

Videos

Grok Imagine API

Voice

Grok Voice API

## Additional Information Regarding Models

- No access to realtime events without search tools enabled
  - Grok has no knowledge of current events or data beyond what was present in its training data.
  - To incorporate realtime data with your request, enable server-side search tools (Web Search / X Search). See Web Search and X Search.
- Chat models
  - No role order limitation: You can mix `system`, `user`, or `assistant` roles in any sequence for your conversation context.
  - `logprobs` and `top_logprobs` are not supported by models `grok-4.20` and newer. These fields will be silently ignored if set.
- Image input models
  - Maximum image size: `20MiB`
  - Maximum number of images: No limit
  - Supported image file types: `jpg/jpeg` or `png`.
  - Any image/text input order is accepted (e.g. text prompt can precede image prompt)

The knowledge cut-off date of Grok 4.5 is February 1, 2026.

## Model Aliases

Some models have aliases to help users automatically migrate to the next version of the same model. In general:

- `<modelname>` is aliased to the latest stable version.
- `<modelname>-latest` is aliased to the latest version. This is suitable for users who want to access the latest features.
- `<modelname>-<date>` refers directly to a specific model release. This will not be updated and is for workflows that demand consistency.

For most users, the aliased `<modelname>` or `<modelname>-latest` are recommended, as you would receive the latest features automatically.

Last updated: July 9, 2026
