#### Key Information

# Consumption and Rate Limits

The cost of using our API is based on token consumptions. We charge different prices based on token category: - **Prompt text, audio and image tokens** - Charged at prompt token price - **Cached prompt tokens** - Charged at cached prompt token price - **Completion tokens** - Charged at completion token price - **Reasoning tokens** - Charged at completion token price

Visit [Models and Pricing](../models) for general pricing, or [xAI Console](https://console.x.ai) for pricing applicable to your team.

Each `grok` model has different rate limits. To check your team's rate limits, you can visit [xAI Console Models Page](https://console.x.ai/team/default/models).

## Basic unit to calculate consumption — Tokens

Token is the base unit of prompt size for model inference and pricing purposes. It consists of one or more character(s)/symbol(s).

When a Grok model handles your request, an input prompt will be decomposed into a list of tokens through a tokenizer.
The model will then make inference based on the prompt tokens, and generate completion tokens.
After the inference is completed, the completion tokens will be aggregated into a completion response sent back to you.

Our system will add additional formatting tokens to the input/output token, and if you selected a reasoning model, additional reasoning tokens will be added into the total token consumption as well.
Your actual consumption would be reflected either in the `usage` object returned in the API response, or in Usage Explorer on the [xAI Console](https://console.x.ai).

You can use [Tokenizer](https://console.x.ai/team/default/tokenizer) on xAI Console to visualize tokens a given text prompt, or use [Tokenize text](../api-reference#tokenize-text) endpoint on the API.

### Text tokens

Tokens can be either of a whole word, or smaller chunks of character combinations. The more common a word is, the more likely it would be a whole token.

For example, Flint is broken down into two tokens, while Michigan is a whole token.

In another example, most words are tokens by themselves, but "drafter" is broken down into "dra" and "fter", and "postmaster" is broken down into "post" and "master".

For a given text/image/etc. prompt or completion sequence, different tokenizers may break it down into different lengths of lists.

Different Grok models may also share or use different tokenizers. Therefore, **the same prompt/completion sequence may not have the same amount of tokens across different models.**

The token count in a prompt/completion sequence should be approximately linear to the sequence length.

### Image prompt tokens

Each image prompt will take between 256 to 1792 tokens, depending on the size of the image. The image + text token count must be less than the overall context window of the model.

### Estimating consumption with tokenizer on xAI Console or through API

The tokenizer page or API might display less token count than the actual token consumption. The
inference endpoints would automatically add pre-defined tokens to help our system process the
request.

On xAI Console, you can use the [tokenizer page](https://console.x.ai/team/default/tokenizer) to estimate how many tokens your text prompt will consume. For example, the following message would consume 5 tokens (the actual consumption may vary because of additional special tokens added by the system).

Message body:

```json
[
  {
    "role": "user",
    "content": "How is the weather today?"
  }
]
```

Tokenize result on Tokenizer page:

You can also utilize the [Tokenize Text](../api-reference#tokenize-text) API endpoint to tokenize the text, and count the output token array length.

### Cached prompt tokens

When you send the same prompt multiple times, we may cache your prompt tokens. This would result in reduced cost for these tokens at the cached token rate, and a quicker response.

The prompt is cached using prefix matching, using cache for the exact prefix matches in the subsequent requests. However, the cache size might be limited and distributed across different clusters.

You can also specify `x-grok-conv-id: <A constant uuid4 ID>` in the HTTP request header, to increase the likelihood of cache hit in the subsequent requests using the same header.

### Reasoning tokens

The model may use reasoning to process your request. The reasoning content is returned in the response's `reasoning_content` field. The reasoning token consumption will be counted separately from `completion_tokens`, but will be counted in the `total_tokens`.

The reasoning tokens will be charged at the same price as `completion_tokens`.

`grok-4` does not return `reasoning_content`

## Hitting rate limits

To request a higher rate limit, please email support@x.ai with your anticipated volume.

For each tier, there is a maximum amount of requests per minute and tokens per minute. This is to ensure fair usage by all users of the system.

Once your request frequency has reached the rate limit, you will receive error code `429` in response.

You can either:

* Upgrade your team to higher tiers
* Change your consumption pattern to send fewer requests

## Checking token consumption

In each completion response, there is a `usage` object detailing your prompt and completion token count. You might find it helpful to keep track of it, in order to avoid hitting rate limits or having cost surprises.

```json
"usage": {
    "prompt_tokens":37,
    "completion_tokens":530,
    "total_tokens":800,
    "prompt_tokens_details": {
        "text_tokens":37,
        "audio_tokens":0,
        "image_tokens":0,
        "cached_tokens":8
    },
    "completion_tokens_details": {
        "reasoning_tokens":233,
        "audio_tokens":0,
        "accepted_prediction_tokens":0,
        "rejected_prediction_tokens":0
    },
    "num_sources_used":0
}
```

You can also check with the xAI or OpenAI SDKs (Anthropic SDK is deprecated).

```pythonXAI
import os

from xai_sdk import Client
from xai_sdk.chat import system, user

client = Client(api_key=os.getenv("XAI_API_KEY"))

chat = client.chat.create(
model="grok-4",
messages=[system("You are Grok, a chatbot inspired by the Hitchhiker's Guide to the Galaxy.")]
)
chat.append(user("What is the meaning of life, the universe, and everything?"))

response = chat.sample()
print(response.usage)
```

```pythonOpenAISDK
import os
from openai import OpenAI

XAI_API_KEY = os.getenv("XAI_API_KEY")
client = OpenAI(base_url="https://api.x.ai/v1", api_key=XAI_API_KEY)

completion = client.chat.completions.create(
model="grok-4",
messages=[
{
"role": "system",
"content": "You are Grok, a chatbot inspired by the Hitchhiker's Guide to the Galaxy.",
},
{
"role": "user",
"content": "What is the meaning of life, the universe, and everything?",
},
],
)

if completion.usage:
print(completion.usage.to_json())
```

```javascriptOpenAISDK
import OpenAI from "openai";
const openai = new OpenAI({
apiKey: "<api key>",
baseURL: "https://api.x.ai/v1",
});

const completion = await openai.chat.completions.create({
model: "grok-4",
messages: [
{
role: "system",
content:
"You are Grok, a chatbot inspired by the Hitchhiker's Guide to the Galaxy.",
},
{
role: "user",
content:
"What is the meaning of life, the universe, and everything?",
},
],
});

console.log(completion.usage);
```
