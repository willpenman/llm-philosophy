#### Guides

Grok 4 Information for Grok 3 Users
When moving from 
grok-3 / grok-3-mini to grok-4, please note the following differences:
• Grok 4 is a reasoning model. There is no non-reasoning mode when using Grok 4.
• presencePenalty, frequencyPenalty, and stop parameters are not supported by reasoning models. Adding them in the request would result in an error.
• Grok 4 does not have a reasoning_effort parameter. If a reasoning_effort is provided, the request will return an error.

# Reasoning

`presencePenalty`, `frequencyPenalty` and `stop` parameters are not supported by reasoning models.
Adding them in the request would result in an error.

## Key Features

* **Think Before Responding**: Thinks through problems step-by-step before delivering an answer.
* **Math & Quantitative Strength**: Excels at numerical challenges and logic puzzles.
* **Reasoning Trace**: Usage metrics expose `reasoning_tokens`. Some models can also return encrypted reasoning via `include: ["reasoning.encrypted_content"]` (see below).

In Chat Completions, only `grok-3-mini` returns `message.reasoning_content`.

`grok-3`, `grok-4` and `grok-4-fast-reasoning` do not return `reasoning_content`. If supported, you can request [encrypted reasoning content](#encrypted-reasoning-content) via `include: ["reasoning.encrypted_content"]` in the Responses API instead.

### Encrypted Reasoning Content

For `grok-4`, the reasoning content is encrypted by us and can be returned if you pass `include: ["reasoning.encrypted_content"]` to the Responses API. You can send the encrypted content back to provide more context to a previous conversation. See [Adding encrypted thinking content](chat#adding-encrypted-thinking-content) for more details on how to use the content.

## Control how hard the model thinks

`reasoning_effort` is not supported by `grok-3`, `grok-4` and `grok-4-fast-reasoning`. Specifying `reasoning_effort` parameter will get
an error response. Only `grok-3-mini` supports `reasoning_effort`.

The `reasoning_effort` parameter controls how much time the model spends thinking before responding. It must be set to one of these values:

* **`low`**: Minimal thinking time, using fewer tokens for quick responses.
* **`high`**: Maximum thinking time, leveraging more tokens for complex problems.

Choosing the right level depends on your task: use `low` for simple queries that should complete quickly, and `high` for harder problems where response latency is less important.

## Usage Example

Here’s a simple example using `grok-3-mini` to multiply 101 by 3.

```pythonXAI
import os

from xai_sdk import Client
from xai_sdk.chat import system, user

client = Client(
    api_key=os.getenv("XAI_API_KEY"),
    timeout=3600, # Override default timeout with longer timeout for reasoning models
)

chat = client.chat.create(
    model="grok-3-mini",
    reasoning_effort="high",
    messages=[system("You are a highly intelligent AI assistant.")],
)
chat.append(user("What is 101\*3?"))

response = chat.sample()

print("Final Response:")
print(response.content)

print("Number of completion tokens:")
print(response.usage.completion_tokens)

print("Number of reasoning tokens:")
print(response.usage.reasoning_tokens)
```

```pythonOpenAISDK
import os
import httpx
from openai import OpenAI

client = OpenAI(
    base_url="https://api.x.ai/v1",
    api_key=os.getenv("XAI_API_KEY"),
    timeout=httpx.Timeout(3600.0), # Override default timeout with longer timeout for reasoning models
)

response = client.responses.create(
    model="grok-3-mini",
    reasoning={"effort": "high"},
    input=[
        {"role": "system", "content": "You are a highly intelligent AI assistant."},
        {"role": "user", "content": "What is 101*3?"},
    ],
)

message = next(item for item in response.output if item.type == "message")
text = next(c.text for c in message.content if c.type == "output_text")

print("Final Response:")
print(text)

print("Number of output tokens:")
print(response.usage.output_tokens)

print("Number of reasoning tokens:")
print(response.usage.output_tokens_details.reasoning_tokens)
```

```javascriptOpenAISDK
import OpenAI from "openai";

const client = new OpenAI({
    apiKey: "<api key>",
    baseURL: "https://api.x.ai/v1",
    timeout: 360000, // Override default timeout with longer timeout for reasoning models
});

const response = await client.responses.create({
    model: "grok-3-mini",
    reasoning: { effort: "high" },
    input: [
        {
            "role": "system",
            "content": "You are a highly intelligent AI assistant.",
        },
        {
            "role": "user",
            "content": "What is 101*3?",
        },
    ],
});

// Find the message in the output array
const message = response.output.find((item) => item.type === "message");
const textContent = message?.content?.find((c) => c.type === "output_text");

console.log("\\nFinal Response:", textContent?.text);

console.log("\\nNumber of output tokens:", response.usage.output_tokens);

console.log("\\nNumber of reasoning tokens:", response.usage.output_tokens_details.reasoning_tokens);
```

```javascriptAISDK
import { xai } from '@ai-sdk/xai';
import { generateText } from 'ai';

const result = await generateText({
  model: xai.responses('grok-3-mini'),
  system: 'You are a highly intelligent AI assistant.',
  prompt: 'What is 101*3?',
});

console.log('Final Response:', result.text);
console.log('Number of completion tokens:', result.totalUsage.completionTokens);
console.log('Number of reasoning tokens:', result.totalUsage.reasoningTokens);
```

```bash
curl https://api.x.ai/v1/responses \\
-H "Content-Type: application/json" \\
-H "Authorization: Bearer $XAI_API_KEY" \\
-m 3600 \\
-d '{
    "input": [
        {
            "role": "system",
            "content": "You are a highly intelligent AI assistant."
        },
        {
            "role": "user",
            "content": "What is 101*3?"
        }
    ],
    "model": "grok-3-mini",
    "reasoning": { "effort": "high" },
    "stream": false
}'
```

### Sample Output

```output

Final Response:
The result of 101 multiplied by 3 is 303.

Number of completion tokens:
14

Number of reasoning tokens:
310
```

## Notes on Consumption

When you use a reasoning model, the reasoning tokens are also added to your final consumption amount. The reasoning token consumption will likely increase when you use a higher `reasoning_effort` setting.
