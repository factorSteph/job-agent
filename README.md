# Job Alert Agent

🇪🇸 [Versión en español más abajo](#job-alert-agent-versión-en-español)

**Job Alert Agent** is a personal job-hunting agent that fetches remote listings from six boards, runs them through simple (and cost-efficient) rules, and uses an LLM as final judge, emailing me only what's worth my time. Built from scratch, in public, while learning Python, by someone who spent a decade running HR operations and decided the best way to learn to code was to automate her own job search.

## How it works

The agent is a pipeline of four layers. Layers are **stages, not sources**: adding a new job board doesn't create a new layer, it just widens Layer 1. Each board gets a small translator function that normalizes its data into one standard format, so the filter, the judge, and the email are written only once.

| Layer | What it does | Status |
|---|---|---|
| 1 - Fetch | Pulls listings from 6 boards (RSS + JSON APIs) | ✅ Done |
| 2 - Filter | Rule-based cascade + per-board translators | ✅ Done |
| 3 - Judge | An LLM reads each surviving listing and decides SEND or SKIP | ✅ Done |
| 4 - Notify | Daily email with approved listings only, scheduled via GitHub Actions | ✅ Done |

Boards connected: We Work Remotely, Himalayas, Remotive, Arbeitnow, Jobicy, RemoteOK.

## Stack

- **Python** - `feedparser` (RSS boards), `requests` (JSON APIs + LLM calls), `python-dotenv` (secrets), `tiktoken` (token measurement)
- **LLM judge:** GPT-5 Nano via REST API
- **Scheduler:** GitHub Actions (free tier), API key stored in GitHub Secrets
- **Version control:** Git + GitHub

### Why GPT-5 Nano

Model choice wasn't a default. It came from independent research (via Perplexity) comparing real input prices across providers, because this workload is heavily input-dominated: ~1,760 tokens per listing read, a one-line verdict out.

| Provider | Input price |
|---|---|
| **GPT-5 Nano** | $0.05/M ✅ |
| Gemini 2.5 Flash-Lite | $0.10/M |
| DeepSeek V3.2 | $0.14/M |

At this scale every option is cheap: a full run over ~400 listings costs about 10 cents (yes, I did the math 😜). The deciding factor wasn't price but API access friction from Costa Rica. Prompt caching was evaluated and deliberately skipped: at ~$3/month running daily, the optimization isn't worth the complexity.

## Design decisions

### 1. The filter fails toward letting things through

The cost of error is asymmetric. A false rejection (a good job silently discarded) is an opportunity lost forever: I never even know it existed. A false pass (a bad listing reaching my inbox) costs three seconds to delete. When errors are this unbalanced, the system should lean toward letting things through. The judge's standing rule: **when in doubt, let it pass.**

### 2. No filter rejects anything without saying why

A filter that discards silently is the worst class of bug: nothing breaks, and you never find out what you lost. Every rejection in this pipeline prints its reason (`→ dropped by: us based`). It's the same failure mode ATS systems inflict on candidates every day; I just refused to build one that does it to me.

### 3. Features get killed when the data stops justifying them

Early on I built a parser to extract each company's headquarters, as a proxy for "does this US company actually hire globally?" Then a board arrived with the direct data (explicit location restrictions), and the proxy became dead weight. I killed the feature, even though it was already built and had taught me string parsing. Sunk cost applies to code too. The HQ field didn't beat the LLM in any case where both could act, so it went.

Two more that shaped the pipeline: **look at raw data before filtering it** (the "region" field on one board says "Anywhere in the World" 82% of the time; a field that can't distinguish anything isn't a filter, it's decoration), and **guard against silent API failures** (a malformed response gets caught and named, never swallowed; an agent that crashes on the first weird input isn't an agent, it's a demo).

## Running it

```bash
git clone https://github.com/factorSteph/job-agent.git
cd job-agent
pip install -r requirements.txt
```

Create a `.env` file in the project root with your own API key:

```
OPENAI_API_KEY=your-key-here
```

The `.env` file is gitignored and never leaves your machine. For the scheduled run, the same key lives in GitHub Secrets under the same name.

Then:

```bash
python buscar_empleos.py
```

The judge's criteria (target roles, hard NOs, screening rules) are written for my profile. To use this for your own search, edit the system prompt in `buscar_empleos.py`. A configurable version is on the roadmap.

## Status & roadmap

The agent runs end to end: fetch, filter, judge, notify. Working and in daily use.

Next up, in no particular order:

- Configurable profiles (same engine, two configs: the second user has a cybersecurity background, which is what forced the normalization design from day one)
- Automatic retry on network failure (a DNS hiccup shouldn't kill a scheduled run)
- Region filter recovery (discard listings from explicitly named locations before they reach the judge)

The full build journal lives in a private Notion log, session by session. A narrative version of the journey (in Spanish) is coming to Substack; link will land here when it exists.

---

# Job Alert Agent (versión en español)

**Job Alert Agent** es un agente personal de búsqueda de empleo que trae vacantes remotas de seis boards, las pasa por reglas simples (y baratas de correr 😜), y usa un LLM como juez final, enviándome por correo solo lo que vale mi tiempo. Construido desde cero, en público, mientras aprendo Python, por alguien que pasó una década dirigiendo operaciones de RRHH y decidió que la mejor forma de aprender a programar era automatizar su propia búsqueda de trabajo.

## Cómo funciona

El agente es un pipeline de cuatro capas. Las capas son **etapas, no fuentes**: agregar un board nuevo no crea una capa nueva, solo ensancha la Capa 1. Cada board tiene una función traductora chica que normaliza sus datos a un formato estándar único, así el filtro, el juez y el correo se escriben una sola vez.

| Capa | Qué hace | Estado |
|---|---|---|
| 1 - Traer | Trae vacantes de 6 boards (RSS + APIs JSON) | ✅ Lista |
| 2 - Filtrar | Cascada de reglas + traductores por board | ✅ Lista |
| 3 - Decidir | Un LLM lee cada aviso sobreviviente y decide SEND o SKIP | ✅ Lista |
| 4 - Avisar | Correo diario solo con los aprobados, agendado vía GitHub Actions | ✅ Lista |

Boards conectados: We Work Remotely, Himalayas, Remotive, Arbeitnow, Jobicy, RemoteOK.

## Stack

- **Python** - `feedparser` (boards RSS), `requests` (APIs JSON + llamadas al LLM), `python-dotenv` (secretos), `tiktoken` (medición de tokens)
- **Juez LLM:** GPT-5 Nano vía API REST
- **Agendador:** GitHub Actions (capa gratuita), API key guardada en GitHub Secrets
- **Control de versiones:** Git + GitHub

### Por qué GPT-5 Nano

La elección del modelo no fue un default. Salió de investigación independiente (vía Perplexity) comparando precios reales de input entre proveedores, porque este proceso es dominado por input: ~1,760 tokens leídos por aviso, un veredicto de una línea de salida.

| Proveedor | Precio input |
|---|---|
| **GPT-5 Nano** | $0.05/M ✅ |
| Gemini 2.5 Flash-Lite | $0.10/M |
| DeepSeek V3.2 | $0.14/M |

A esta escala todas las opciones son baratas: una corrida completa sobre ~400 avisos cuesta unos 10 centavos (sí, hice la cuenta 😜). El factor decisivo no fue el precio sino la fricción de acceso a la API desde Costa Rica. El prompt caching se evaluó y se descartó deliberadamente: a ~$3/mes corriendo diario, la optimización no vale la complejidad.

## Decisiones de diseño

### 1. El filtro falla hacia dejar pasar

El costo del error es asimétrico. Un rechazo falso (un buen trabajo descartado en silencio) es una oportunidad perdida para siempre: nunca me entero de que existió. Un pase falso (un mal aviso llegando a mi bandeja) cuesta tres segundos de borrar. Cuando los errores están así de desbalanceados, el sistema debe inclinarse a dejar pasar. La regla permanente del juez: **ante la duda, dejar pasar.**

### 2. Ningún filtro rechaza nada sin decir por qué

Un filtro que descarta en silencio es la peor clase de bug: nada se rompe, y nunca te enterás de lo que perdiste. Cada rechazo en este pipeline imprime su motivo (`→ cayó por: us based`). Es el mismo modo de fallo que los ATS le infligen a los candidatos todos los días; simplemente me negué a construir uno que me lo hiciera a mí.

### 3. Las features se matan cuando los datos dejan de justificarlas

Al principio construí un parser para extraer la sede de cada empresa, como proxy de "¿esta empresa gringa contrata globalmente de verdad?". Después llegó un board con el dato directo (restricciones de ubicación explícitas), y el proxy quedó siendo peso muerto. Maté la feature, aunque ya estaba construida y me había enseñado a parsear texto. El costo hundido también aplica al código. El campo de la sede no le ganaba al LLM en ningún caso donde ambos pudieran actuar, así que se fue.

Dos más que moldearon el pipeline: **mirar la data cruda antes de filtrarla** (el campo "region" de un board dice "Anywhere in the World" el 82% de las veces; un campo que no distingue nada no es un filtro, es decoración), y **blindarse contra fallos silenciosos de la API** (una respuesta malformada se atrapa y se nombra, nunca se absorbe; un agente que se cae con el primer dato raro no es un agente, es una demo).

## Cómo correrlo

```bash
git clone https://github.com/factorSteph/job-agent.git
cd job-agent
pip install -r requirements.txt
```

Creá un archivo `.env` en la raíz del proyecto con tu propia API key:

```
OPENAI_API_KEY=tu-key-aqui
```

El `.env` está en el gitignore y nunca sale de tu máquina. Para la corrida agendada, la misma key vive en GitHub Secrets bajo el mismo nombre.

Después:

```bash
python buscar_empleos.py
```

Los criterios del juez (roles objetivo, NOs duros, reglas de filtrado) están escritos para mi perfil. Para usar esto en tu propia búsqueda, editá el system prompt en `buscar_empleos.py`. Una versión configurable está en el roadmap.

## Estado y roadmap

El agente corre de punta a punta: trae, filtra, juzga, avisa. Funcionando y en uso diario.

Lo que sigue, sin orden particular:

- Perfiles configurables (mismo motor, dos configs: el segundo usuario viene de ciberseguridad, que es lo que forzó el diseño de normalización desde el día uno)
- Reintento automático ante fallo de red (un hipo de DNS no debería matar una corrida agendada)
- Recuperar el filtro de región (descartar avisos de ubicaciones nombradas explícitamente antes de que lleguen al juez)

La bitácora completa de construcción vive en un log privado de Notion, sesión por sesión. Una versión narrativa del journey viene en camino a Substack; el link va a aterrizar acá cuando exista.
