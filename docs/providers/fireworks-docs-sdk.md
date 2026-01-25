> ## Documentation Index
> Fetch the complete documentation index at: https://docs.fireworks.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Python SDK

The official Python SDK for the Fireworks AI API is available on [GitHub](https://github.com/fw-ai-external/python-sdk) and [PyPI](https://pypi.org/project/fireworks-ai/).

## Fireworks vs. OpenAI SDK

Fireworks is [OpenAI-compatible](/tools-sdks/openai-compatibility), so you can use the OpenAI SDK with Fireworks. The Fireworks SDK offers additional benefits:

* **Better concurrency defaults** — Optimized connection pooling for high-throughput workloads
* **Fireworks-exclusive features** — Access parameters and response fields not available in the OpenAI API
* **Platform automation** — Manage datasets, evals, fine-tuning, and deployments programmatically

## Installation

Requires Python 3.9+ and an API key. See [Getting your API key](/api-reference/introduction#getting-your-api-key) for instructions.

<Note>
  The SDK is currently in alpha. Use the `--pre` flag when installing to get the latest version.
</Note>

<CodeGroup>
  ```bash pip theme={null}
  pip install --pre fireworks-ai
  ```

  ```bash poetry theme={null}
  poetry add --pre fireworks-ai
  ```

  ```bash uv theme={null}
  uv add --pre fireworks-ai
  ```
</CodeGroup>

For detailed usage instructions, see the
[README.md](https://github.com/fw-ai-external/python-sdk#readme). To quickly get
started with serverless, see our [Serverless
Quickstart](/getting-started/quickstart).
