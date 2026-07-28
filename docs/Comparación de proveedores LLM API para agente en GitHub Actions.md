## Resumen directo

Para un agente en GitHub Actions con `requests` de Python y auth simple por header, **DeepSeek** y **Qwen (Alibaba)** son los más baratos y sin fricción de acceso; **Moonshot/Kimi** es competitivo en precio pero tiene fricción de registro (requiere teléfono chino o pasa por reseller); y entre proveedores occidentales, **Gemini 2.5 Flash-Lite** y **GPT-5 Nano** son los más económicos, con acceso abierto sin restricción para Costa Rica. Todos exponen REST estándar compatible con `Authorization: Bearer <key>` en header, ideal para GitHub Secrets/.env.

## Tabla comparativa de precios (modelos económicos/rápidos)

| Proveedor | Modelo | Input $/1M tok | Output $/1M tok | Fecha del dato | Fuente |
|---|---|---|---|---|---|
| Moonshot (China) | Kimi K2.5 | $0.60 (cache-miss) / $0.10 (cache-hit) | $3.00 | 2026-05-14 | [^1] |
| Moonshot (China) | Kimi K2 0711 | $0.55 | $2.20 | 2026-07-03 | [^2] |
| DeepSeek (China) | DeepSeek V3.2 (chat) | $0.14 | $0.28 | 2026-04-22 | [^3] |
| Alibaba | Qwen3.5 Flash | $0.10 | $0.40 | 2026-07-24 | [^4] |
| Alibaba | Qwen-Turbo (legacy) | $0.30 | $0.60 | 2026-03-13 | [^5] |
| OpenAI | GPT-5 Nano | $0.05 | $0.40 | 2026-02-28 | [^6] |
| OpenAI | GPT-5 Mini | $0.25 | $2.00 | 2026-02-28 | [^6] |
| Google | Gemini 2.5 Flash-Lite | $0.10 | $0.40 | fecha de captura 2026-07 (página oficial, sin fecha de "última actualización" visible) | [^7] |
| Google | Gemini 3.1 Flash-Lite | $0.25 | $1.50 | 2026-03-02 | [^8] |
| Anthropic | Claude Haiku 4.5 | $1.00 | $5.00 | 2026-03-02 | [^9] |

Nota: no encontré con fuente fechada un precio de "Claude Haiku económico" por debajo de $1.00/$5.00 vigente en 2026; Claude 3.5 Haiku ($0.25/$1.25) aparece en algunas páginas  pero no pude confirmar si sigue disponible comercialmente en julio 2026 — lo marco como dato incierto, no lo uses sin verificar directamente en la consola de Anthropic.[^9]

## Disponibilidad de API pública y restricciones para Costa Rica

| Proveedor | ¿Cualquiera puede sacar key? | Restricción regional / Costa Rica | Fuente |
|---|---|---|---|
| Moonshot (Kimi) | Registro oficial requiere número de teléfono de China continental para verificación completa; el portal está en chino | Sin número chino, el flujo es incompleto o requiere pasar por reseller (ej. TokenMix, Global API) que sí acepta PayPal/email y sirve desde fuera de China | [^10][^11][^12] |
| DeepSeek | Guías indican que developers fuera de China enfrentan trabas (verificación, pago) y existen guías específicas "cómo acceder sin teléfono chino" | Existencia de esa guía sugiere fricción real para signup directo desde fuera de China, aunque no se documenta un bloqueo geográfico explícito por país | [^13] |
| Qwen (Alibaba Cloud) | Sí, vía Alibaba Cloud Model Studio "International mode", pensado para desarrolladores fuera de China | No se reportó bloqueo específico para Costa Rica | [^4] |
| OpenAI | Sí, self-service abierto globalmente vía platform.openai.com | Costa Rica no aparece en listas de países restringidos de OpenAI en las fuentes consultadas | [^14][^6] |
| Google Gemini API | Sí, self-service vía Google AI Studio | Sin restricción reportada para Costa Rica | [^7] |
| Anthropic Claude | Sí, self-service vía console.anthropic.com | Sin restricción reportada para Costa Rica en las fuentes consultadas | [^9] |

No encontré, con fuente fechada en 2026, una lista oficial de países bloqueados/permitidos específica para Costa Rica en ninguno de los seis proveedores. Lo que sí está documentado con fecha es la fricción práctica de Moonshot y DeepSeek para signup fuera de China.[^10][^11][^13]

## Manejo de la API key (env var / .env / secrets)

Todos los proveedores listados usan el mismo patrón REST estándar: header `Authorization: Bearer <API_KEY>`, sin OAuth ni firmas complejas, compatible con variables de entorno estándar (`.env` local o GitHub Actions Secrets):

- Moonshot/Kimi: API OpenAI-compatible, base URL `api.moonshot.ai/v1` (o `.cn/v1`), misma librería `openai` de Python con `api_key` desde variable de entorno.[^1][^10]
- DeepSeek: mismo esquema OpenAI-compatible, sin requerimiento especial más allá del header Bearer.[^3]
- Qwen (Alibaba Model Studio): también expone endpoint OpenAI-compatible con Bearer token.[^4]
- OpenAI, Google Gemini y Anthropic: todos usan header simple (`Authorization: Bearer` para OpenAI/Anthropic, `x-goog-api-key` o query param para Gemini), estándar en SDKs y perfectamente manejable con GitHub Secrets.[^14][^7][^9]

No encontré ningún proveedor de los evaluados que requiera algo distinto a una API key simple en header — no hay mTLS, firma HMAC ni tokens rotativos obligatorios en el uso básico de estas APIs REST.

## Benchmarks recientes de clasificación / juicio de texto corto

| Benchmark | Modelo líder relevante | Score | Fecha | Fuente |
|---|---|---|---|
| IFEval (instrucciones verificables, formato/longitud) | Qwen3.5-27B | 95% | 2026-07-07 | [^15] |
| IFEval | Kimi K2.5 | 93.9% | 2026-07-07 | [^15] |
| IFEval | DeepSeek V3 | 86.1% | 2026-07-07 | [^15] |
| IFEval | GPT-4.1 mini | 88.5% | 2026-07-07 | [^15] |
| MMLU (conocimiento general, clasificación multi-tema) | Qwen3.7 Max | 93.7% | 2026-07-27 | [^16] |
| MMLU | Kimi K2 0711 | 88.3% | 2026-07-27 (fuente actualizada, score de referencia previo) | [^16] |
| MMLU | DeepSeek V3 | 83.4% | 2026-07-27 | [^16] |
| MMLU | GLM 5 / GLM 5 Thinking | 91.7% | 2026-06-10 | [^16] |

IFEval es el benchmark más directamente relacionado con "juicio/clasificación de texto corto", ya que evalúa si el modelo sigue restricciones verificables (palabras clave, longitud, formato) sobre prompts cortos. No encontré, con fuente fechada de 2026, un benchmark específico llamado "short-text classification" estandarizado que cubra a los seis proveedores simultáneamente — los datos más comparables y fechados que hallé son IFEval y MMLU.[^15]

## Comparación consolidada: Kimi vs. chinos vs. occidentales económicos

| Dimensión | Kimi (Moonshot) | DeepSeek / Qwen (chinos) | GPT-5 Nano / Gemini Flash-Lite (occidentales) |
|---|---|---|---|
| Precio input/output más barato disponible | $0.60/$3.00 (K2.5, cache-miss) [^1] | DeepSeek $0.14/$0.28 [^3]; Qwen Flash $0.10/$0.40 [^4] | GPT-5 Nano $0.05/$0.40 [^6]; Gemini 2.5 Flash-Lite $0.10/$0.40 [^7] |
| Fricción de signup | Alta: requiere teléfono chino o reseller [^10][^11] | Fricción reportada para acceso directo fuera de China [^13]; Qwen ofrece modo internacional [^4] | Ninguna: signup self-service estándar [^14][^7] |
| Auth header simple | Sí, Bearer, OpenAI-compatible [^10] | Sí, Bearer [^3][^4] | Sí, Bearer/API-key header [^14][^7] |
| Benchmark IFEval (texto corto/instrucciones) | 93.9% (K2.5) [^15] | DeepSeek V3 86.1% [^15]; Qwen3.5-27B 95% [^15] | GPT-4.1 mini 88.5% [^15] (no hay dato fechado de GPT-5 Nano en IFEval en las fuentes revisadas) |

Para tu caso de uso (agente en GitHub Actions, requests simples, key en Secrets), la combinación más práctica dado el requisito de "sin restricciones especiales" sería DeepSeek o Qwen por precio, o Gemini Flash-Lite/GPT-5 Nano por cero fricción de acceso desde Costa Rica; Kimi queda en tercer lugar por la barrera de registro salvo que uses un reseller como TokenMix.[^11][^1]

---

## References

1. [Kimi API Pricing 2026: K2.6 $0.95, K2.5 $0.60, K2 Family ...](https://tokenmix.ai/blog/kimi-k2-api-pricing) - Kimi K2.6 ships April 2026: $0.16/$0.95 input, $4.00 output per MTok. K2.5: $0.10/$0.60/$3.00. K2 de...

2. [Kimi K2 0711 API Pricing 2026 - Costs, Performance & Providers](https://pricepertoken.com/pricing-page/model/moonshotai-kimi-k2) - Kimi K2 0711 pricing: $0.55/M input, $2.20/M output. Compare with 10 similar models, see benchmarks,...

3. [DeepSeek API Pricing (July 2026): V4 Flash $0.14/M ... - TLDL](https://www.tldl.io/resources/deepseek-api-pricing) - DeepSeek API pricing (July 2026): DeepSeek V4 Flash $0.14/M input, $0.28/M output. Compare cache, co...

4. [Qwen API Pricing (July 2026): Qwen3.5 Plus & Flash Rates](https://benchlm.ai/alibaba/api-pricing) - Current Qwen API prices per 1M tokens: Qwen3.5 397B $0.60/$3.60, Plus $0.40/$2.40, Flash $0.10/$0.40...

5. [Qwen API Pricing 2026: Complete Guide to Alibaba's LLM Costs](https://aiapi-pro.com/blog/blog-qwen-api-pricing-2026) - Complete Qwen API pricing guide for 2026. Compare Qwen-Turbo, Qwen-Plus, Qwen-Max costs. Free tier i...

6. [OpenAI API $ per 1M tokens (May 2026) | Nicola Lazzari](https://nicolalazzari.ai/articles/openai-api-pricing-explained-2026) - OpenAI API $/million-token rates for GPT-5.4, GPT-5, Mini & Nano—tables, workload math, Batch 50% sa...

7. [Gemini Developer API pricing | Gemini API | Google AI for Developers](https://ai.google.dev/gemini-api/docs/pricing) - Gemini Developer API Pricing

8. [Gemini 3.1 Flash-Lite: Built for intelligence at scale](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-lite/) - Gemini 3.1 Flash-Lite is our fastest and most cost-efficient Gemini 3 series model yet.

9. [Anthropic API Pricing (July 2026): Claude Fable 5 $10.00/M ...](https://www.tldl.io/resources/anthropic-api-pricing) - Anthropic API pricing (July 2026): Claude Haiku 4.5 $1/M input, $5/M output. Compare cache, context,...

10. [Moonshot AI — Pricing, Products & Review](https://china-llm.com/provider/moonshot) - Kimi — long-context chat models optimized for research and analysis

11. [Kimi API Guide 2026: How to Access Moonshot AI from Anywhere](https://global-apis.com/cs/blog/kimi-api-guide-2026) - Step-by-step guide to using Kimi K2.5/K2.6 API. Pricing, code examples, international payment soluti...

12. [Moonshot API Key 注册教程 - OneClaw](https://oneclaw.cn/docs/tutorials/moonshot-api-key.html) - 手把手教你注册 Moonshot AI 开放平台，获取 API Key，3 分钟搞定。

13. [How to Access DeepSeek API from Outside China (2026 Guide)](https://dev.to/zhouxia_qian_768284ca068e/how-to-access-deepseek-api-from-outside-china-2026-guide-5748) - A practical guide for overseas developers trying to use DeepSeek V4, DeepSeek-Coder, and other DeepS...

14. [Pricing | OpenAI API](https://developers.openai.com/api/docs/pricing) - Pricing information for the OpenAI platform.

15. [IFEval Leaderboard (July 2026): Qwen3.5-27B Leads at 95%](https://benchlm.ai/benchmarks/ifeval) - Instruction-Following Eval (IFEval) leaderboard across 24 AI models. Qwen3.5-27B leads with 95%. A b...

16. [MMLU Leaderboard 2026 - Compare AI Model Scores](https://pricepertoken.com/leaderboards/benchmark/mmlu) - Compare AI model performance on MMLU benchmark. As of July 27, 2026, the top-scoring model on MMLU i...

