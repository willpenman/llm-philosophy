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
| Anthropic | Claude 3 Haiku (`claude-3-haiku-20240307`) | 2024-03-13 | yes | https://www.anthropic.com/news/claude-3-haiku | Announcement + API availability. |
| OpenAI | GPT-5.2 (`gpt-5.2-2025-12-11`) | 2025-12-11 | yes | https://openai.com/index/introducing-gpt-5-2/ | Announcement + API availability. |
| OpenAI | GPT-5.2 Pro (`gpt-5.2-pro`) | 2025-12-11 | yes | https://openai.com/index/introducing-gpt-5-2/ | Pro availability listed in announcement. |
| OpenAI | GPT-5.2-Codex (`gpt-5.2-codex`) | 2025-12-18 | yes (Codex) | https://openai.com/index/introducing-gpt-5-2-codex/ | Codex-only release. |
| OpenAI | GPT-5.1 (`gpt-5.1`) | 2025-11-13 | yes | https://openai.com/index/gpt-5-1-for-developers/ | API release. |
| OpenAI | GPT-5.1-Codex-Max (`gpt-5.1-codex-max`) | 2025-11-19 | yes (Codex) | https://help.openai.com/en/articles/9624314-model-release-notes | Codex-only release. |
| OpenAI | GPT-5 (`gpt-5`) | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5/ | Announcement. |
| OpenAI | GPT-5 Pro | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5/ | Pro availability listed in announcement. |
| OpenAI | GPT-5 mini (`gpt-5-mini`) | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5-for-developers/ | API release (mini/nano). |
| OpenAI | GPT-5 nano (`gpt-5-nano`) | 2025-08-07 | yes | https://openai.com/index/introducing-gpt-5-for-developers/ | API release (mini/nano). |
| OpenAI (open weights) | gpt-oss-120b | 2025-08-05 | yes | https://help.openai.com/en/articles/9624314-model-release-notes | Open-weight release. |
| OpenAI (open weights) | gpt-oss-20b | 2025-08-05 | yes | https://help.openai.com/en/articles/9624314-model-release-notes | Open-weight release. |
| OpenAI | GPT-5-Codex (`gpt-5-codex`) | 2025-09-15 | yes (Codex) | https://help.openai.com/en/articles/9624314-model-release-notes | Codex-only release. |
| OpenAI | GPT-5-Codex-Mini (`gpt-5-codex-mini`) | 2025-11-19 | yes (Codex) | https://help.openai.com/en/articles/9624314-model-release-notes | Listed without a date; included in Nov 19 release notes. |
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
| OpenAI | GPT-4 Turbo (`gpt-4-turbo`) | 2023-11-06 | yes | https://openai.com/blog/new-models-and-developer-products-announced-at-devday | DevDay launch. |
| OpenAI | GPT-4 (`gpt-4`) | 2023-03-14 | yes | https://help.openai.com/en/articles/6825453-chatgpt-release-notes | Announced in ChatGPT release notes. |
| OpenAI | GPT-3.5 Turbo (`gpt-3.5-turbo`) | 2023-03-01 | yes | https://www.wired.com/story/chatgpt-api-ai-gold-rush | ChatGPT API launch. |
| Google | Gemini 3 Pro Preview (`gemini-3-pro-preview`) | 2025-11-18 | preview | https://ai.google.dev/gemini-api/docs/changelog | Changelog launch note. |
| Google | Gemini 2.0 Flash Lite (`gemini-2.0-flash-lite-001`) | 2025-02-25 | yes (scheduled shutdown 2026-02-25) | https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-0-flash-lite | Release + discontinuation dates. |
| xAI | Grok 4.1 (`grok-4-1-fast-reasoning`) | 2025-11-17 | yes | https://x.ai/news/grok-4-1/ | Release of Grok 4.1 family; fast-reasoning variant date not separately announced. |
| xAI | Grok 3 (`grok-3`) | 2025-02-19 | yes | https://x.ai/blog/grok-3 | Grok 3 Beta announcement. |
| DeepSeek | DeepSeek V3.2 (`deepseek-v3p2`) | 2025-12-01 | yes | https://api-docs.deepseek.com/news/news251201 | Open-source release announcement. |
| Meta (open weights) | Llama 3 | 2024-04-18 | yes | https://about.fb.com/news/2024/04/meta-ai-assistant-built-with-llama-3/ | Meta AI update built on Llama 3. |
| Meta (open weights) | Llama 3.1 | 2024-07-23 | yes | https://about.fb.com/br/news/2024/07/apresentando-o-llama-3-1-nossos-modelos-mais-capazes-ate-o-momento/ | Newsroom announcement (Portuguese). |
| Meta (open weights) | Llama 3.2 | 2024-09-25 | yes | https://about.fb.com/ltam/news/2024/09/llama-3-2-revolucionando-la-ia-y-la-vision-de-vanguardia-con-modelos-abiertos-y-personalizables/ | Newsroom announcement (Spanish). |
| Mistral (open weights) | Mistral 7B | 2023-09-27 | no (retired 2025-03-30) | https://legal.mistral.ai/ai-governance/models/mistral-7-b | Model lifecycle table. |
| Mistral (open weights) | Mixtral 8x7B | 2023-12-11 | no (retired 2025-03-30) | https://legal.mistral.ai/ai-governance/models/mixtral-8-7b | Model lifecycle table. |
| Mistral (open weights) | Mixtral 8x22B | 2024-04-17 | yes | https://mistral.ai/news/mixtral-8x22b | Announcement. |
| Google (open weights) | Gemma 2 | 2024-06-27 | yes | https://blog.google/technology/developers/google-gemma-2/ | Announcement. |
| Qwen (open weights) | Qwen2 | 2024-06-07 | yes | https://qwenlm.github.io/blog/qwen2/ | Announcement. |
| Qwen (open weights) | Qwen2.5 | 2024-09-19 | yes | https://qwenlm.github.io/blog/qwen2.5/ | Announcement. |
