# Kilo Code API Endpoints Research

Here's an evidence-backed breakdown of the current status of Kilo Code API endpoints, proxy configuration, and header requirements.

## Confirmed/Corrected

- **Primary Endpoint:**
  - *Confirmed, with clarification*: The main endpoint for Kilo Code model calls is `https://kilocode.ai/api/openrouter/`, using the OpenAI-compatible `/chat/completions` path. This endpoint is designed to work in direct replacement for OpenRouter's original API endpoint (i.e., swap `https://openrouter.ai/api/v1` with `https://kilocode.ai/api/openrouter`) and supports OpenAI-style payloads. This does function as a proxy to OpenRouter for most non-local models.[1]

- **Custom Headers:**
  - *Partially Confirmed/Not Fully Documented*: 
    - The required headers for normal model calls include `Content-Type: application/json` and `Authorization: <KiloCode API Key>`. There is **no explicit documentation** confirming strict requirements for `HTTP-Referer`, `X-Title`, `X-KiloCode-Version`, or `User-Agent` headers on standard usage in official guides or popular examples.[1]
    - Environmental variables for custom proxy behavior (such as OPENROUTER_REFERER, etc.) are referenced sporadically in setup discussions and potential advanced/proxy scenarios, but their strict enforcement for end-users is *not confirmed* in public-facing documentation.
    - There is no public evidence post-2025 that the headers must match exactly as specified for authentication by default; typically the `Authorization` header is sufficient.[1]

- **Provider Routing:**
  - *Partially Confirmed*: 
    - OpenAI and Gemini models are routed according to their standard APIs when configured directly.
    - For most other model calls, requests through the Kilo Code UI or extension to less-common models are proxied via the Kilo Code OpenRouter proxy endpoint. Custom/local (Ollama/vLLM) routing is supported via an environment variable such as `CUSTOM_API_URL`, but this is referenced more in the MCP server's codebase and advanced user setups.[2]
    - Documentation on the precise mechanics of how routing occurs in `providers/openrouter.py` and `server.py` is not public, but user and official blog reports confirm this overall structure.[2][1]

- **Configuration Source Files:**
  - *Partially Confirmed*: 
    - The routing, base URL, and some validation settings are handled in `providers/openrouter.py` and `server.py`. However, direct public access to these specific line numbers is unavailable at this time, and information is mostly referenced via user issues, environment variables, and setup advice.[2]
    - Header and route customization is affected by environment variables (like `CUSTOM_MODELS_CONFIG_PATH`), especially for custom model registries and advanced development cases.[2]

- **Recent Changes/Post-2025:**
  - *No major deprecations*: No public repo or official blog post mentions significant deprecations to the described API endpoint or basic routing practices since mid-2025. Current guides dated September 2025 confirm endpoint parity and comparable setup instructions.[3][4][1]

## Sources

- Kilo Code API usage and endpoint swapping: [How to use Kilocode LLM API Directly (AI Engineer Guide, July 2025)](https://aiengineerguide.com/blog/kilocode-api/).[1]
- Official Kilo Code Docs (configuration, model routing, no explicit strict custom header requirements): [Kilo Code Documentation](https://kilocode.ai/docs/) , [Provider integration](https://kilocode.ai/docs/providers/openrouter).[5][3]
- Environment variable and configuration file guidance (for advanced routing such as custom_models.json): [zen-mcp-server GitHub issues](https://github.com/BeehiveInnovations/zen-mcp-server/issues/185).[2]
- No explicit mention of strict custom header matching in user-facing docs or tutorials as of September 2025.[5][1]

## Recommendations

- **Basic Use:** For standard inference/API calls, use the endpoint `https://kilocode.ai/api/openrouter/chat/completions` and pass your API key in the `Authorization` header and content as JSON. This workflow closely mimics OpenRouter usage.[1]
- **Custom Routing or Local Models:** For advanced cases (e.g., custom/local providers), reference MCP server environmental variables such as `CUSTOM_API_URL` or `CUSTOM_MODELS_CONFIG_PATH` as needed. Refer to server code and environment for deep customization.[2]
- **Header Matching:** Unless developing advanced integrations or debugging authentication errors, do not worry about exact custom header values beyond `Content-Type` and `Authorization`. If encountering rejections, check server logs and MCP docs, and mirror the headers in your requests as closely as possible.
- **Version Changes:** Monitor the Kilo Code and Zen MCP server changelogs for updates if building critical infrastructure, as headers and routing logic can evolve.

If more granular or internal documentation is required, contacting the Kilo Code team or inspecting private repos may be necessary for confirmation on internal validation logic. If more detail is needed from private code, consider submitting a request or issue upstream.