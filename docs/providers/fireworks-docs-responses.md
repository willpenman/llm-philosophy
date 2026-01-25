> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fireworks.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Responses API

Fireworks.ai offers a powerful Responses API that allows for more complex and stateful interactions with models. This guide will walk you through the key features and how to use them.

<Warning title="Data Retention Policy">
  The Responses API has a different data retention policy than the chat completions endpoint. See [Data Privacy & security](/guides/security_compliance/data_handling#response-api-data-retention).
</Warning>

## Overview

The Responses API is designed for building conversational applications and complex workflows. It allows you to:

* **Continue conversations**: Maintain context across multiple turns without resending the entire history.
* **Use external tools**: Integrate with external services and data sources through MCP/SSE tools (server-executed) or function tools (client-executed).
* **Stream responses**: Receive results as they are generated, enabling real-time applications.
* **Control tool usage**: Set limits on tool calls with `max_tool_calls` parameter.
* **Manage data retention**: Choose whether to store conversations (default) or opt-out with `store=false`.

## Basic Usage

You can interact with the Response API using the Fireworks Python SDK or by making direct HTTP requests.

### Creating a Response

To start a new conversation, you use the `client.responses.create` method. For a complete example, see the [getting started notebook](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/fireworks_mcp_examples.ipynb).

```python OpenAI SDK theme={null}
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_API_KEY", "YOUR_FIREWORKS_API_KEY_HERE")
)

response = client.responses.create(
    model="accounts/fireworks/models/qwen3-235b-a22b",
    input="What is reward-kit and what are its 2 main features? Keep it short Please analyze the fw-ai-external/reward-kit repository.",
    tools=[{"type": "sse", "server_url": "https://gitmcp.io/docs"}]
)

print(response.output[-1].content[0].text.split("</think>")[-1])
```

### Using Function Tools

Function tools follow the OpenAI-compatible format and are returned to the client for execution.

```python OpenAI SDK theme={null}
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_API_KEY", "YOUR_FIREWORKS_API_KEY_HERE")
)

response = client.responses.create(
    model="accounts/fireworks/models/qwen3-235b-a22b",
    input="What is the weather like in San Francisco?",
    tools=[{
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA"
                }
            },
            "required": ["location"]
        }
    }],
    tool_choice="auto"
)

# Check if the model wants to call a function
for item in response.output:
    if hasattr(item, 'type') and item.type == "tool_call":
        print(f"Function: {item.function.name}")
        print(f"Arguments: {item.function.arguments}")
```

### Continuing a Conversation with `previous_response_id`

To continue a conversation, you can use the `previous_response_id` parameter. This tells the API to use the context from a previous response, so you don't have to send the entire conversation history again. For a complete example, see the [previous response ID notebook](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/fireworks_previous_response_cookbook.ipynb).

```python OpenAI SDK theme={null}
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_API_KEY", "YOUR_FIREWORKS_API_KEY_HERE")
)

# First, create an initial response
initial_response = client.responses.create(
    model="accounts/fireworks/models/qwen3-235b-a22b",
    input="What are the key features of reward-kit?",
    tools=[{"type": "sse", "server_url": "https://gitmcp.io/docs"}]
)
initial_response_id = initial_response.id

# Now, continue the conversation
continuation_response = client.responses.create(
    model="accounts/fireworks/models/qwen3-235b-a22b",
    input="How do I install it?",
    previous_response_id=initial_response_id,
    tools=[{"type": "sse", "server_url": "https://gitmcp.io/docs"}]
)

print(continuation_response.output[-1].content[0].text.split("</think>")[-1])
```

## Streaming Responses

For real-time applications, you can stream the response as it's being generated. For a complete example, see the [streaming example notebook](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/fireworks_streaming_example.ipynb).

```python OpenAI SDK theme={null}
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_API_KEY", "YOUR_FIREWORKS_API_KEY_HERE")
)

stream = client.responses.create(
    model="accounts/fireworks/models/qwen3-235b-a22b",
    input="give me 5 interesting facts on modelcontextprotocol/python-sdk -- keep it short!",
    stream=True,
    tools=[{"type": "mcp", "server_url": "https://mcp.deepwiki.com/mcp"}]
)

for chunk in stream:
    print(chunk)
```

## Cookbook Examples

For more in-depth examples, check out the following notebooks:

* [General MCP Examples](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/fireworks_mcp_examples.ipynb)
* [Using `previous_response_id`](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/fireworks_previous_response_cookbook.ipynb)
* [Streaming Responses](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/fireworks_streaming_example.ipynb)
* [Using `store=False`](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/mcp_server_with_store_false_argument.ipynb)
* [MCP with Streaming](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/fireworks_mcp_with_streaming.ipynb)

## Storing Responses

By default, responses are stored and can be referenced by their ID. You can disable this by setting `store=False`. If you do this, you will not be able to use the `previous_response_id` to continue the conversation. For a complete example, see the [store=False notebook](https://github.com/fw-ai/cookbook/blob/main/learn/response-api/mcp_server_with_store_false_argument.ipynb).

```python OpenAI SDK theme={null}
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=os.getenv("FIREWORKS_API_KEY", "YOUR_FIREWORKS_API_KEY_HERE")
)

response = client.responses.create(
    model="accounts/fireworks/models/qwen3-235b-a22b",
    input="give me 5 interesting facts on modelcontextprotocol/python-sdk -- keep it short!",
    store=False,
    tools=[{"type": "mcp", "server_url": "https://mcp.deepwiki.com/mcp"}]
)

# This will fail because the previous response was not stored
try:
    continuation_response = client.responses.create(
        model="accounts/fireworks/models/qwen3-235b-a22b",
        input="Explain the second fact in more detail.",
        previous_response_id=response.id
    )
except Exception as e:
    print(e)
```

## Deleting Stored Responses

When responses are stored (the default behavior with `store=True`), you can immediately delete them from storage using the DELETE endpoint. This permanently removes the conversation data.

<CodeGroup>
  ```python Python (OpenAI SDK) theme={null}
  import os
  from openai import OpenAI
  import requests

  client = OpenAI(
      base_url="https://api.fireworks.ai/inference/v1",
      api_key=os.getenv("FIREWORKS_API_KEY", "YOUR_FIREWORKS_API_KEY_HERE")
  )

  # Create a response
  response = client.responses.create(
      model="accounts/fireworks/models/qwen3-235b-a22b",
      input="What is the capital of France?",
      store=True  # This is the default
  )

  response_id = response.id
  print(f"Created response with ID: {response_id}")

  # Delete the response immediately
  headers = {
      "Authorization": f"Bearer {os.getenv('FIREWORKS_API_KEY')}",
      "x-fireworks-account-id": "your-account-id"
  }
  delete_response = requests.delete(
      f"https://api.fireworks.ai/inference/v1/responses/{response_id}",
      headers=headers
  )

  if delete_response.status_code == 200:
      print("Response deleted successfully")
  else:
      print(f"Failed to delete response: {delete_response.status_code}")
  ```

  ```bash cURL theme={null}
  # First create a response and capture the ID
  RESPONSE=$(curl -X POST https://api.fireworks.ai/inference/v1/responses \
    -H "Authorization: Bearer $FIREWORKS_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
      "model": "accounts/fireworks/models/qwen3-235b-a22b",
      "input": "What is the capital of France?",
      "store": true
    }')

  # Extract the response ID (using jq or similar JSON parser)
  RESPONSE_ID=$(echo $RESPONSE | jq -r '.id')

  # Delete the response
  curl -X DELETE "https://api.fireworks.ai/inference/v1/responses/$RESPONSE_ID" \
    -H "Authorization: Bearer $FIREWORKS_API_KEY" \
    -H "x-fireworks-account-id: your-account-id"
  ```
</CodeGroup>

<Warning>
  Once a response is deleted, it cannot be recovered.
</Warning>

## Response Structure

All response objects include the following fields:

* `id`: Unique identifier for the response (e.g., `resp_abc123...`)
* `created_at`: Unix timestamp when the response was created
* `status`: Status of the response (typically `"completed"`)
* `model`: The model used to generate the response
* `output`: Array of message objects, tool calls, and tool outputs
* `usage`: Token usage information:
  * `prompt_tokens`: Number of tokens in the prompt
  * `completion_tokens`: Number of tokens in the completion
  * `total_tokens`: Total tokens used
* `previous_response_id`: ID of the previous response in the conversation (if any)
* `store`: Whether the response was stored (boolean)
* `max_tool_calls`: Maximum number of tool calls allowed (if set)

### Example Response

```json  theme={null}
{
  "id": "resp_abc123...",
  "created_at": 1735000000,
  "status": "completed",
  "model": "accounts/fireworks/models/qwen3-235b-a22b",
  "output": [
    {
      "id": "msg_xyz789...",
      "role": "user",
      "content": [{"type": "input_text", "text": "What is 2+2?"}],
      "status": "completed"
    },
    {
      "id": "msg_def456...",
      "role": "assistant",
      "content": [{"type": "output_text", "text": "2 + 2 equals 4."}],
      "status": "completed"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 8,
    "total_tokens": 23
  },
  "previous_response_id": null,
  "store": true,
  "max_tool_calls": null
}
```
