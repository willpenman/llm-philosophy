Guides
Streaming Response
Streaming outputs is supported by all models with text output capability (Chat, Image Understanding, etc.). It is not supported by models with image output capability (Image Generation).

Streaming outputs uses Server-Sent Events (SSE) that let the server send back the delta of content in event streams.

Streaming responses are beneficial for providing real-time feedback, enhancing user interaction by allowing text to be displayed as it's generated.

To enable streaming, you must set 
"stream": true
 in your request.

When using streaming output with reasoning models, you might want to manually override request timeout to avoid prematurely closing connection.

Python

import os
from xai_sdk import Client
from xai_sdk.chat import user, system
client = Client(
    api_key=os.getenv('XAI_API_KEY'),
    timeout=3600, # Override default timeout with longer timeout for reasoning models
)
chat = client.chat.create(model="grok-4")
chat.append(
    system("You are Grok, a chatbot inspired by the Hitchhiker's Guide to the Galaxy."),
)
chat.append(
    user("What is the meaning of life, the universe, and everything?")
)
for response, chunk in chat.stream():
    print(chunk.content, end="", flush=True) # Each chunk's content
    print(response.content, end="", flush=True) # The response object auto-accumulates the chunks
print(response.content) # The full response
You'll get the event streams like these:

Bash

data: {
    "id":"<completion_id>","object":"chat.completion.chunk","created":<creation_time>,
    "model":"grok-4",
    "choices":[{"index":0,"delta":{"content":"Ah","role":"assistant"}}],
    "usage":{"prompt_tokens":41,"completion_tokens":1,"total_tokens":42,
    "prompt_tokens_details":{"text_tokens":41,"audio_tokens":0,"image_tokens":0,"cached_tokens":0}},
    "system_fingerprint":"fp_xxxxxxxxxx"
}
data: {
    "id":"<completion_id>","object":"chat.completion.chunk","created":<creation_time>,
    "model":"grok-4",
    "choices":[{"index":0,"delta":{"content":",","role":"assistant"}}],
    "usage":{"prompt_tokens":41,"completion_tokens":2,"total_tokens":43,
    "prompt_tokens_details":{"text_tokens":41,"audio_tokens":0,"image_tokens":0,"cached_tokens":0}},
    "system_fingerprint":"fp_xxxxxxxxxx"
}
data: [DONE]
It is recommended that you use a client SDK to parse the event stream.

Example streaming responses in Python/Javascript:

Text

Ah, the ultimate question! According to Douglas Adams, the answer is **42**. However, the trick lies in figuring out what the actual question is. If you're looking for a bit more context or a different perspective:
- **Philosophically**: The meaning of life might be to seek purpose, happiness, or to fulfill one's potential.
- **Biologically**: It could be about survival, reproduction, and passing on genes.
- **Existentially**: You create your own meaning through your experiences and choices.
But let's not forget, the journey to find this meaning might just be as important as the answer itself! Keep exploring, questioning, and enjoying the ride through the universe. And remember, don't panic!