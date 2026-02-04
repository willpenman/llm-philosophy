# Model Release Registry

Source of truth for release timing, availability, and references.

Columns:
- provider: company or ecosystem
- model: model family or snapshot
- release_date: YYYY-MM-DD (approximate when only a public announcement date is available)
- available: yes/no/preview (note upcoming shutdowns)
- source: reference URL for the release timing
- notes: optional context (e.g., deprecations)

| provider | model | release_date | available | source | notes |
| --- | --- | --- | --- | --- | --- |
| Anthropic | Claude Opus 4.5 (`claude-opus-4-5-20251101`) | 2025-11-24 | yes | https://www.anthropic.com/news/claude-opus-4-5 | Announcement + API availability. |
| Anthropic | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | 2025-10-15 | no | https://www.anthropic.com/news/claude-haiku-4-5 | Not supported. |
| Anthropic | Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) | 2025-09-29 | no | https://www.anthropic.com/news/claude-sonnet-4-5 | Not supported. |
| Anthropic | Claude Opus 4.1 (`claude-opus-4-1-20250805`) | 2025-08-05 | no | https://www.anthropic.com/news/claude-opus-4-1 | Not supported. |
| Anthropic | Claude Opus 4 (`claude-opus-4-20250514`) | 2025-05-22 | no (retired 2026-01-05) | https://www.anthropic.com/news/claude-4 | Retired January 5, 2026. |
| Anthropic | Claude Sonnet 4 (`claude-sonnet-4-20250514`) | 2025-05-22 | no | https://www.anthropic.com/news/claude-4 | Not supported. |
| Anthropic | Claude 3.7 Sonnet (`claude-3-7-sonnet-20250219`) | 2025-02-24 | deprecated (retiring 2026-02-19) | https://www.anthropic.com/news/claude-3-7-sonnet | Deprecated October 28, 2025. |
| Anthropic | Claude 3.5 Haiku (`claude-3-5-haiku-20241022`) | 2024-10-22 | deprecated (retiring 2026-02-19) | https://www.anthropic.com/news/3-5-models-and-computer-use | Deprecated December 19, 2025. |
| Anthropic | Claude 3.5 Sonnet v2 (`claude-3-5-sonnet-20241022`) | 2024-10-22 | no (retired 2025-10-28) | https://www.anthropic.com/news/3-5-models-and-computer-use | Retired October 28, 2025. |
| Anthropic | Claude 3.5 Sonnet (`claude-3-5-sonnet-20240620`) | 2024-06-20 | no (retired 2025-10-28) | https://www.anthropic.com/news/claude-3-5-sonnet | First 3.5 model. Retired October 28, 2025. |
| Anthropic | Claude 3 Opus (`claude-3-opus-20240229`) | 2024-03-04 | no (retired 2026-01-05) | https://www.anthropic.com/news/claude-3-family | Claude 3 family launch. Retired January 5, 2026. |
| Anthropic | Claude 3 Sonnet (`claude-3-sonnet-20240229`) | 2024-03-04 | no (retired 2025-07-21) | https://www.anthropic.com/news/claude-3-family | Claude 3 family launch. Retired July 21, 2025. |
| Anthropic | Claude 3 Haiku (`claude-3-haiku-20240307`) | 2024-03-13 | yes | https://www.anthropic.com/news/claude-3-haiku | Announcement + API availability. |
| OpenAI | GPT-5.2 (`gpt-5.2-2025-12-11`) | 2025-12-11 | yes | https://openai.com/index/introducing-gpt-5-2/ | Announcement + API availability. |
| OpenAI | GPT-5.2 Pro (`gpt-5.2-pro-2025-12-11`) | 2025-12-11 | yes | https://openai.com/index/introducing-gpt-5-2/ | Pro availability listed in announcement. |
| OpenAI | GPT-5.2-Codex (`gpt-5.2-codex`) | 2025-12-18 | yes (Codex) | https://developers.openai.com/codex/changelog | Codex-only release. |
| OpenAI | GPT-5.1 (`gpt-5.1`) | 2025-11-13 | yes | https://openai.com/index/gpt-5-1-for-developers/ | API release. |
| OpenAI | GPT-5.1-Codex (`gpt-5.1-codex`) | 2025-11-13 | yes (Codex) | https://developers.openai.com/codex/changelog | Codex release note. |
| OpenAI | GPT-5.1-Codex-Mini (`gpt-5.1-codex-mini`) | 2025-11-13 | yes (Codex) | https://developers.openai.com/codex/changelog | Codex release note. |
| OpenAI | GPT-5.1-Codex-Max (`gpt-5.1-codex-max`) | 2025-11-13 | yes (Codex) | https://developers.openai.com/codex/changelog | Codex release note. |
| OpenAI | GPT-5 (`gpt-5`) | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5/ | Announcement. |
| OpenAI | GPT-5 Pro | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5/ | Pro availability listed in announcement. |
| OpenAI | GPT-5 mini (`gpt-5-mini`) | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5-for-developers/ | API release (mini/nano). |
| OpenAI | GPT-5 nano (`gpt-5-nano`) | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5-for-developers/ | API release (mini/nano). |
| OpenAI (open weights) | gpt-oss-120b | 2025-08-05 | yes | https://help.openai.com/en/articles/9624314-model-release-notes | Open-weight release. |
| OpenAI (open weights) | gpt-oss-20b | 2025-08-05 | yes | https://help.openai.com/en/articles/9624314-model-release-notes | Open-weight release. |
| OpenAI | GPT-5-Codex (`gpt-5-codex`) | 2025-09-15 | yes (Codex) | https://developers.openai.com/codex/changelog | Codex-only release. |
| OpenAI | GPT-5-Codex-Mini (`gpt-5-codex-mini`) | 2025-11-06 | yes (Codex) | https://developers.openai.com/codex/changelog | Codex-only release. |
| OpenAI | GPT-4.5 Preview (`gpt-4.5-preview`) | 2025-02-27 | deprecated | https://openai.com/index/introducing-gpt-4-5/ | Research preview; later deprecated. |
| OpenAI | GPT-4.1 (`gpt-4.1`) | 2025-04-14 | yes | https://openai.com/index/gpt-4-1/ | API release (4.1, 4.1 mini, 4.1 nano). |
| OpenAI | GPT-4.1 mini (`gpt-4.1-mini`) | 2025-04-14 | yes | https://openai.com/index/gpt-4-1/ | API release (4.1, 4.1 mini, 4.1 nano). |
| OpenAI | GPT-4.1 nano (`gpt-4.1-nano`) | 2025-04-14 | yes | https://openai.com/index/gpt-4-1/ | API release (4.1, 4.1 mini, 4.1 nano). |
| OpenAI | OpenAI o3 (`o3`) | 2025-04-16 | yes | https://openai.com/index/introducing-o3-and-o4-mini/ | API release. |
| OpenAI | OpenAI o4-mini (`o4-mini`) | 2025-04-16 | yes | https://openai.com/index/introducing-o3-and-o4-mini/ | API release. |
| OpenAI | OpenAI o3-pro (`o3-pro`) | 2025-06-10 | yes | https://help.openai.com/en/articles/9624314-model-release-notes | Pro release note. |
| OpenAI | OpenAI o3-mini (`o3-mini`) | 2025-01-31 | yes | https://openai.com/index/openai-o3-mini/ | Announcement. |
| OpenAI | GPT-4o (`gpt-4o-2024-05-13`) | 2024-05-13 | yes | https://openai.com/index/gpt-4o-and-more-tools-to-chatgpt-free/ | Announcement. |
| OpenAI | GPT-4o mini (`gpt-4o-mini`) | 2024-07-18 | yes | https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/ | Announcement. |
| OpenAI | OpenAI o1-preview (`o1-preview`) | 2024-09-12 | deprecated | https://openai.com/index/introducing-openai-o1-preview/ | Preview release. |
| OpenAI | OpenAI o1-mini (`o1-mini`) | 2024-09-12 | deprecated | https://openai.com/index/openai-o1-mini-advancing-cost-efficient-reasoning/ | Preview release. |
| OpenAI | OpenAI o1 (`o1-2024-12-17`) | 2024-12-17 | yes | https://openai.com/index/o1-and-new-tools-for-developers/ | Snapshot date in announcement. |
| OpenAI | OpenAI o1-pro (`o1-pro`) | 2024-12-05 | yes | https://openai.com/index/introducing-chatgpt-pro/ | Pro mode announced with ChatGPT Pro. |
| OpenAI | GPT-4 Turbo (`gpt-4-turbo`) | 2023-11-06 | yes | https://openai.com/blog/new-models-and-developer-products-announced-at-devday | DevDay launch. |
| OpenAI | GPT-4 (`gpt-4`) | 2023-03-14 | yes | https://help.openai.com/en/articles/6825453-chatgpt-release-notes | 0314 checkpoint launch; 0613 checkpoint upgrade later in 2023. |
| OpenAI | GPT-3.5 Turbo (`gpt-3.5-turbo`) | 2023-03-01 | yes | https://openai.com/blog/introducing-chatgpt-and-whisper-apis | ChatGPT API launch with initial 0301 checkpoint, (early 2023, shut down Sept 2024 - note that the updated date of 2024 in the blog post is misleading). Later upgrades: 0613 (mid-2023, shut down Sept 2024), 1106 (late 2023) and 0125 (early 2024). |
| OpenAI | babbage-002 (`babbage-002`) | 2023-08-22 | deprecated | https://platform.openai.com/docs/models/babbage-002 | Release date supplied by maintainer. |
| OpenAI | ChatGPT (GPT-3.5) | 2022-11-30 | no | https://openai.com/hu-HU/index/chatgpt/ | Research preview launch. Not an API model. |
| Google | Gemini 3 Deep Think | 2025-12-04 | no | https://blog.google/products/gemini/gemini-3-deep-think/ | AI Ultra subscribers only. Not supported. |
| Google | Gemini 3 Pro Preview (`gemini-3-pro-preview`) | 2025-11-18 | preview | https://ai.google.dev/gemini-api/docs/changelog | Changelog launch note. |
| Google | Gemini 2.5 Flash-Lite (`gemini-2.5-flash-lite`) | 2025-07-22 | no | https://cloud.google.com/blog/products/ai-machine-learning/gemini-2-5-flash-lite-flash-pro-ga-vertex-ai | Stable version release. Not supported. |
| Google | Gemini 2.5 Pro (`gemini-2.5-pro`) | 2025-06-17 | no | https://cloud.google.com/blog/products/ai-machine-learning/gemini-2-5-flash-lite-flash-pro-ga-vertex-ai | GA release. Not supported. |
| Google | Gemini 2.5 Flash (`gemini-2.5-flash`) | 2025-06-17 | no | https://cloud.google.com/blog/products/ai-machine-learning/gemini-2-5-flash-lite-flash-pro-ga-vertex-ai | GA release. Not supported. |
| Google | Gemini 2.0 Flash Lite (`gemini-2.0-flash-lite-001`) | 2025-02-25 | yes (scheduled shutdown 2026-02-25) | https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-0-flash-lite | Release + discontinuation dates. |
| Google | Gemini 2.0 Pro (`gemini-2.0-pro`) | 2025-02-05 | no | https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-model-updates-february-2025/ | GA release. Not supported. |
| Google | Gemini 2.0 Flash (`gemini-2.0-flash`) | 2025-02-05 | no | https://blog.google/innovation-and-ai/models-and-research/google-deepmind/gemini-model-updates-february-2025/ | GA release. Not supported. |
| Google | Gemini 2.0 Flash Experimental | 2024-12-11 | no (deprecated) | https://blog.google/technology/google-deepmind/google-gemini-ai-update-december-2024/ | Experimental preview. Superseded by GA. |
| Google | Gemini 1.5 Pro v2 (`gemini-1.5-pro-002`) | 2024-09-24 | no | https://developers.googleblog.com/en/updated-production-ready-gemini-models-reduced-15-pro-pricing-increased-rate-limits-and-more/ | Updated production model. Not supported. |
| Google | Gemini 1.5 Flash v2 (`gemini-1.5-flash-002`) | 2024-09-24 | no | https://developers.googleblog.com/en/updated-production-ready-gemini-models-reduced-15-pro-pricing-increased-rate-limits-and-more/ | Updated production model. Not supported. |
| Google | Gemini 1.5 Pro (`gemini-1.5-pro-001`) | 2024-05-24 | no (deprecated) | https://ai.google.dev/gemini-api/docs/changelog#09-29-2025 | Deprecation announced 2025-09-29. |
| Google | Gemini 1.5 Flash (`gemini-1.5-flash-001`) | 2024-05-24 | no (deprecated) | https://developers.googleblog.com/en/gemini-15-pro-and-15-flash-now-available/ | GA release. Superseded by v2. |
| Google | Gemini 1.0 Pro (`gemini-1.0-pro`) | 2023-12-06 | no (deprecated) | https://blog.google/technology/ai/google-gemini-ai/ | Original Gemini launch. |
| xAI | Grok 4.1 (`grok-4-1-fast-reasoning`) | 2025-11-17 | yes | https://x.ai/news/grok-4-1/ | Release of Grok 4.1 family; fast-reasoning variant date not separately announced. |
| xAI | Grok 4 Fast (`grok-4-fast`) | 2025-09-19 | no | https://docs.x.ai/docs/release-notes | Efficiency-focused variant. Not supported. |
| xAI | Grok 2.5 | 2025-08 | no | https://en.wikipedia.org/wiki/Grok_(chatbot) | Source-available release. Not supported. |
| xAI | Grok 4 (`grok-4`) | 2025-07-09 | no | https://x.ai/news/grok-4 | Flagship release with tool use. Not supported. |
| xAI | Grok 4 Code (`grok-4-code`) | 2025-07-09 | no | https://x.ai/news/grok-4 | Code-focused variant. Not supported. |
| xAI | Grok 3 (`grok-3`) | 2025-02-19 | yes | https://x.ai/blog/grok-3 | Grok 3 Beta announcement. |
| xAI | Grok 2 Vision (`grok-2-vision-1212`) | 2024-12-12 | yes (date unverified) | https://docs.x.ai/docs/release-notes | Date inferred from model suffix; confirm source. |
| xAI | Grok 2 (`grok-2`) | 2024-08 | no (deprecated) | https://console.x.ai | Deprecated in xAI console (user-verified). |
| xAI | Grok 2 mini (`grok-2-mini`) | 2024-08 | no (deprecated) | https://console.x.ai | Deprecated in xAI console (user-verified). |
| xAI | Grok 1.5 Vision | 2024-04-12 | no (deprecated) | https://console.x.ai | Deprecated in xAI console (user-verified). |
| xAI | Grok 1.5 | 2024-03-29 | no (deprecated) | https://console.x.ai | Deprecated in xAI console (user-verified). |
| xAI | Grok 1 | 2023-11-04 | no (deprecated) | https://console.x.ai | Deprecated in xAI console (user-verified). |
| DeepSeek | DeepSeek V3.2 (`deepseek-v3p2`) | 2025-12-01 | yes | https://api-docs.deepseek.com/news/news251201 | Open-source release announcement. |
| DeepSeek | DeepSeek V3.2-Speciale | 2025-12-01 | no | https://api-docs.deepseek.com/news/news251201 | Advanced reasoning variant. Not supported. |
| DeepSeek | DeepSeek V3.2-Exp | 2025-09-29 | no (deprecated) | https://api-docs.deepseek.com/news/news250929 | Experimental. Superseded by V3.2. |
| DeepSeek | DeepSeek V3.1 | 2025-08 | no | https://en.wikipedia.org/wiki/DeepSeek | Hybrid V3+R1 model. Not supported. |
| DeepSeek | DeepSeek R1-0528 (`deepseek-reasoner`) | 2025-05-28 | no | https://api-docs.deepseek.com/updates/ | Updated R1 with function calling. Not supported. |
| DeepSeek | DeepSeek V3-0324 (`deepseek-v3-0324`) | 2025-03-24 | yes | https://api-docs.deepseek.com/updates/ | MIT License release. Supported via Fireworks serverless. |
| DeepSeek | DeepSeek R1 | 2025-01-20 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| DeepSeek | DeepSeek V3 | 2024-12-26 | no (deprecated) | https://en.wikipedia.org/wiki/DeepSeek | 671B MoE model. Superseded by V3.2. |
| DeepSeek | DeepSeek V2.5 | 2024-09 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| DeepSeek | DeepSeek Coder V2 | 2024-07 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| DeepSeek | DeepSeek V2 | 2024-05 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| DeepSeek | DeepSeek LLM | 2023-12 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| DeepSeek | DeepSeek Coder | 2023-11 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Moonshot AI | Kimi K2.5 | 2026-01-27 | yes | https://techcrunch.com/2026/01/27/chinas-moonshot-releases-a-new-open-source-model-kimi-k2-5-and-a-coding-agent/ | Open-source K2.5 release. Not supported. |
| Moonshot AI | Kimi K2 Thinking (`kimi-k2-thinking`) | 2025-11-06 | yes | https://platform.moonshot.ai/blog/posts/changelog | K2 Think release on Kimi Open Platform. Not supported. |
| Moonshot AI | Kimi K2 (`kimi-k2-0711-preview`) | 2025-07-11 | preview | https://platform.moonshot.ai/blog/posts/changelog | K2 preview release on Kimi Open Platform. Not supported. |
| Moonshot AI | Kimi K1.5 | 2025-01-20 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Moonshot AI | Kimi (chatbot) | 2023-10 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Meta (open weights) | Llama 4 Scout | 2025-04-05 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Meta (open weights) | Llama 4 Maverick | 2025-04-05 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Meta (open weights) | Llama 3.3 70B | 2024-12-06 | yes | https://techcommunity.microsoft.com/blog/machinelearningblog/microsoft-azure-ai-foundry-welcomes-meta-llama-3-3-70b-model/4355199 | Not supported. |
| Meta (open weights) | Llama 3.2 | 2024-09-25 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Meta (open weights) | Llama 3.1 | 2024-07-23 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Meta (open weights) | Llama 3 | 2024-04-18 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Meta (open weights) | Llama 2 | 2023-07-18 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Meta (open weights) | Llama 1 (LLaMA) | 2023-02-27 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Mistral (open weights) | Mistral Small 3.1 | 2025-03-17 | yes | https://mistral.ai/news/mistral-small-3-1 | Not supported. |
| Mistral (open weights) | Mistral Small 3 | 2025-01-30 | yes | https://mistral.ai/en/news/mistral-small-3 | Not supported. |
| Mistral (open weights) | Mistral Large 2 | 2024-07-24 | yes | https://mistral.ai/en/news/mistral-large-2407 | Research license release. Not supported. |
| Mistral (open weights) | Mixtral 8x22B | 2024-04-17 | yes | https://mistral.ai/news/mixtral-8x22b | Announcement. |
| Mistral (open weights) | Mixtral 8x7B | 2023-12-11 | no (retired 2025-03-30) | https://legal.mistral.ai/ai-governance/models/mixtral-8-7b | Model lifecycle table. |
| Mistral (open weights) | Mistral 7B | 2023-09-27 | no (retired 2025-03-30) | https://legal.mistral.ai/ai-governance/models/mistral-7-b | Model lifecycle table. |
| Qwen (open weights) | Qwen3 | 2025-04-29 | yes | https://www.alibabagroup.com/document-1853940226976645120 | Not supported. |
| Qwen (open weights) | Qwen2.5-VL | 2025-01-26 | yes | https://qwenlm.github.io/blog/qwen2.5-vl/ | Not supported. |
| Qwen (open weights) | Qwen2.5-Coder | 2024-10-21 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Qwen (open weights) | Qwen2.5 | 2024-09-19 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Qwen (open weights) | Qwen2 | 2024-06-07 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Qwen (open weights) | Qwen1.5 | 2024-02-04 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Qwen (open weights) | Qwen-1.8B | 2023-11-30 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Qwen (open weights) | Qwen-72B | 2023-11-30 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Qwen (open weights) | Qwen-14B | 2023-09-25 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
| Qwen (open weights) | Qwen-7B | 2023-08-03 | no (deprecated) | https://fireworks.ai/models | Deprecated in Fireworks serverless (user-verified). |
