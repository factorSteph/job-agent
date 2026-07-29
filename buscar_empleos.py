import feedparser
import requests
import os
from dotenv import load_dotenv
regiones_buenas = ["worldwide", "americas", "latam", "cst", "utc-6"]

# ============================================================
# LAS DOS MÁQUINAS TRADUCTORAS (se definen, todavía no se usan)
# ============================================================

def traducir_wwr(puesto):
    ficha = {
        "titulo": puesto.title,
        "empresa": "sin_dato",
        "url": puesto.link,
        "texto": puesto.summary,
        "board": "WWR",
        "restriccion_pais": ["sin_dato"],
        "categorias": ["sin_dato"]
    }

    return ficha


def traducir_himalayas(puesto):
    ficha = {
        "titulo": puesto["title"],
        "empresa": puesto["companyName"],
        "url": puesto["applicationLink"],
        "texto": puesto["description"],
        "board": "Himalayas",
        "restriccion_pais": puesto["locationRestrictions"],
        "categorias": puesto["categories"]
    }

    return ficha

def traducir_remotive(puesto):
    texto_region = puesto["candidate_required_location"].lower()
    incluye = False
    for region in regiones_buenas:
        if region in texto_region:
            incluye = True
    if incluye:
        restriccion = []
    else:
        restriccion = ["fuera"]

    ficha = {
        "titulo": puesto["title"],
        "empresa": puesto["company_name"],
        "url": puesto["url"],
        "texto": puesto["description"],
        "board": "Remotive",
        "restriccion_pais": restriccion,
        "categorias": ["sin_dato"]
    }

    return ficha

def traducir_arbeitnow(puesto):
    ficha = {
        "titulo": puesto["title"],
        "empresa": puesto["company_name"],
        "url": puesto["url"],
        "texto": puesto["description"],
        "board": "Arbeitnow",
        "restriccion_pais": ["sin_dato"],
        "categorias": ["sin_dato"]
    }

    return ficha

def traducir_jobicy(puesto):
    texto_geo = puesto["jobGeo"].lower()
    incluye = False
    for region in regiones_buenas:
        if region in texto_geo:
            incluye = True
    if incluye:
        restriccion = []
    else:
        restriccion = ["fuera"]

    ficha = {
        "titulo": puesto["jobTitle"],
        "empresa": puesto["companyName"],
        "url": puesto["url"],
        "texto": puesto["jobDescription"],
        "board": "Jobicy",
        "restriccion_pais": restriccion,
        "categorias": puesto["jobIndustry"]
    }

    return ficha

def traducir_remoteok(puesto):
    ficha = {
        "titulo": puesto["position"],
        "empresa": puesto["company"],
        "url": puesto["url"],
        "texto": puesto["description"],
        "board": "RemoteOK",
        "restriccion_pais": ["sin_dato"],
        "categorias": ["sin_dato"]
    }

    return ficha


# ============================================================
# BLOQUE 1: traer y traducir los dos boards a UNA bolsa común
# ============================================================

fichas = []

# WWR
url_wwr = "https://weworkremotely.com/remote-jobs.rss"
feed = feedparser.parse(url_wwr)
for puesto in feed.entries:
    fichas.append(traducir_wwr(puesto))

# Himalayas (con paginación, con tope)
offset = 0
tope = 2000

while offset < tope:
    url_himalayas = "https://himalayas.app/jobs/api?limit=20&offset=" + str(offset)
    respuesta = requests.get(url_himalayas)
    datos = respuesta.json()
    lote = datos["jobs"]

    if lote == []:
        break

    for puesto in lote:
        fichas.append(traducir_himalayas(puesto))

    offset = offset + 20

# Remotive (una sola página, trae ~lo del día)
url_remotive = "https://remotive.com/api/remote-jobs"
respuesta = requests.get(url_remotive)
datos = respuesta.json()
for puesto in datos["jobs"]:
    fichas.append(traducir_remotive(puesto))

# Arbeitnow (una sola página, ~110 puestos)
url_arbeitnow = "https://www.arbeitnow.com/api/job-board-api"
respuesta = requests.get(url_arbeitnow)
datos = respuesta.json()
for puesto in datos["data"]:
    fichas.append(traducir_arbeitnow(puesto))

# Jobicy (una sola página, ~100 puestos)
url_jobicy = "https://jobicy.com/api/v2/remote-jobs"
respuesta = requests.get(url_jobicy)
datos = respuesta.json()
for puesto in datos["jobs"]:
    fichas.append(traducir_jobicy(puesto))

# RemoteOK (lista pelada, con metadata en [0] que hay que saltar)
url_remoteok = "https://remoteok.com/api"
headers = {"User-Agent": "job-alert-agent"}
respuesta = requests.get(url_remoteok, headers=headers)
datos = respuesta.json()
for puesto in datos[1:]:
    fichas.append(traducir_remoteok(puesto))

# ============================================================
# BLOQUE 2: filtrar la bolsa entera (WWR + Himalayas juntos)
# ============================================================

sospechosos = ["us only", "us based", "usa", "united states", "u.s.", "w2"]

categorias_buenas = [
    "automation", "ai-automation", "ai-workflow", "workflow",
    "process-automation", "orchestration", "integration", "rpa",
    "agent", "no-code", "low-code",
    "operations", "operational", "process-improvement",
    "process-optimization", "business-process", "continuous-improvement",
    "operational-excellence", "lean", "six-sigma", "kaizen",
    "people-operations", "people-leadership", "coaching", "mentoring",
    "talent-development", "team-lead", "operations-manager",
    "shared-services", "program-manager", "project-manager",
    "change-management", 
    "program management", "project management"
]
sobrevivientes = []
murio_titulo = 0
murio_pais = 0
murio_categoria = 0

for ficha in fichas:

    titulo = ficha["titulo"].lower()
    restriccion = ficha["restriccion_pais"]
    categorias = ficha["categorias"]

    # --- CHECKPOINT 1: título sospechoso ---
    es_sospechoso = False
    for sospechoso in sospechosos:
        if sospechoso in titulo:
            es_sospechoso = True

    if es_sospechoso:
        murio_titulo = murio_titulo + 1
        continue

    # --- CHECKPOINT 2: país ---
    pasa_pais = True
    if "sin_dato" in restriccion:
        pasa_pais = True
    elif restriccion == []:
        pasa_pais = True
    elif "Costa Rica" in restriccion:
        pasa_pais = True
    else:
        pasa_pais = False

    if not pasa_pais:
        murio_pais = murio_pais + 1
        continue

    # --- CHECKPOINT 3: categoría ---
    pasa_categoria = False
    if "sin_dato" in categorias:
        pasa_categoria = True
    else:
        for categoria in categorias:
            for buena in categorias_buenas:
                if buena in categoria.lower():
                    pasa_categoria = True

    if not pasa_categoria:
        murio_categoria = murio_categoria + 1
        continue

    # --- Si llegó hasta acá, pasó los tres ---
    sobrevivientes.append(ficha)


# ============================================================
# BLOQUE 3: resumen
# ============================================================

print("---")
print("Total traído:", len(fichas))
print("Sobrevivientes:", len(sobrevivientes))
print("Murieron por título:", murio_titulo)
print("Murieron por país:", murio_pais)
print("Murieron por categoría:", murio_categoria)

# ============================================================
# BLOQUE 4: pesar los sobrevivientes en tokens
# ============================================================

import tiktoken

balanza = tiktoken.get_encoding("cl100k_base")

total_tokens = 0

for ficha in sobrevivientes:
    texto_a_pesar = ficha["titulo"] + " " + ficha["texto"]
    tokens_de_esta = len(balanza.encode(texto_a_pesar))
    total_tokens = total_tokens + tokens_de_esta

print("---")
print("Sobrevivientes pesados:", len(sobrevivientes))
print("Tokens totales (título + texto):", total_tokens)
print("Promedio por ficha:", total_tokens // len(sobrevivientes))

# ============================================================
# BLOQUE 5 (Capa 3): la IA juzga
# ============================================================

load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]

# --- El briefing permanente (SOP en la pared) ---
instrucciones = """You are a screening assistant for Steph, a job seeker. Your only job is to read one job posting and decide whether it is worth sending to her inbox. You are the first filter before a human looks at it. Be her advocate, not a gatekeeper.

# WHO STEPH IS
Steph is an operations and automation leader with about a decade running HR shared-services and payroll operations across Latin America and North America. She founded and scaled a regional operations hub, held service levels above 95% across 8 countries, and led teams through high-complexity, multi-country work.

Since early 2026 she has moved deliberately into the technical side of that work: she teaches herself tools and builds automation end-to-end. She already works hands-on with Power Automate (Cloud and Desktop), Copilot Studio, Claude Code, agentic workflow design, Git/GitHub, and spec-driven development. She is in the early stages of learning Python by building a real project.

Her formal credentials: a Bachelor's degree in Public Administration (Universidad de Costa Rica), a Neuro-Linguistic Programming Master certification (IANLP), a Storytelling and Persuasion certification (INCAE), a Certified Project Practitioner credential (GE360), and a Lean Six Sigma Green Belt in progress. Use this list when judging roles that require a specific certification or degree: if a role hard-requires a credential NOT on this list, that counts against it; if the required credential IS on this list, she has it.

Her defining pattern: she enters a domain WITHOUT the formal credential, builds the capability by doing, and earns the title afterward. She did exactly this in payroll (first-ever internal transfer, zero prior payroll experience) and in end-to-end HR operations leadership. She is now doing it again with AI and automation. Treat this pattern as central: a posting asking for experience she is actively building is NOT an automatic disqualifier.

# WHAT SHE IS LOOKING FOR
Roles where operational credibility and technical fluency coexist, with neither overshadowing the other. Strong matches look like:
- People Operations AI & Automation Manager / Lead
- AI Process Operations Manager
- Operations & Automation Lead
- Process improvement / process engineering roles with an automation core
- Any operations role where building AI agents or automation is central, not incidental
Remote and global-friendly. She is based in Costa Rica (CST).

# HARD NO — do not send these
- HR Business Partner (HRBP) or classic HR Manager roles centered on the traditional HR function
- Recruiting / talent acquisition as the core function
- Roles whose CORE requires deep finance or accounting knowledge (e.g. actuarial, financial analysis, controllership as the main job)
- Roles that REQUIRE a formal certification or degree she does not hold as a strict, non-negotiable prerequisite (not merely "nice to have")
- Roles built on a long-runway technical foundation she does not have and that would take MONTHS OR YEARS to acquire (e.g. software engineering from scratch, computer science degree required, senior-level coding in a language she does not use)

# THE ENTRY-BARRIER TEST (the key judgment)
Do NOT reject a role just because it is technical or asks for years of experience. Judge the SIZE OF THE BRIDGE she would have to cross:
- SHORT bridge (counts IN FAVOR): the role asks for a tool or skill she could pick up in days or weeks (e.g. n8n, a new workflow tool, a specific low-code platform). She learns these fast; not knowing one today is fine.
- GRAY ZONE (does not disqualify on its own): the role asks for years of experience in something she is building right now (automation, AI agents). Her whole career pattern is entering without the formal credential. Let these through.
- LONG bridge (HARD NO): the role rests on a deep foundation that takes months or years to build (software development from zero, CS fundamentals, deep finance). If she would basically have to use AI to fake her way across the bridge, it is too far. Reject.

The difference is NOT "technical vs non-technical." It is "short bridge vs long bridge." A Workday-configuration or automation role she is excited to grow into is a YES. A senior software-engineer role is a NO. Both are technical; only one is reachable.

# CALIBRATION EXAMPLES (how postings map to decisions)
Use these as anchors. Judge a new posting by which examples it most resembles.

SEND — AI Workflow Engineer building automation on a business background (names tools like n8n): building automation is the core, and any missing tool is a short bridge.
SEND — Partner Operations & AI Automation Manager: building AI agents is central to the role, not incidental; missing platform exposure is learnable.
SEND — Operational Excellence / Process Improvement Lead: process redesign, Lean Six Sigma, Kaizen, SOPs, change management, all core strengths.
SKIP — IT Support Specialist (Google Cloud, M365, Salesforce): a support role operating tools, not building automation.
SKIP — HR Manager / HR Business Partner centered on the traditional HR function: this is the function she is deliberately moving away from.
SKIP — Senior Software Engineer / AI Architect requiring a CS degree and years of senior coding in a language she does not use: a long-bridge technical foundation, not reachable.

# DECISION RULE — when in doubt, let it through
The cost of error is asymmetric:
- False positive (you send a job that turns out not to fit): she opens it, deletes it in 3 seconds. Cheap. Recoverable.
- False negative (you filter out a job that actually fit): she never sees it. The opportunity is lost forever. Expensive. Unrecoverable.
Because of this imbalance, when a posting is ambiguous and does NOT clearly hit a HARD NO, lean toward sending it. The HARD NO list is the line you never cross; the "when in doubt, send" rule applies ONLY inside the gray area, not to override a hard no.

# CONSISTENCY RULE (read before deciding)
Your DECISION must match your REASON. If your reasoning identifies a HARD NO or a LONG bridge, you MUST decide SKIP, even if the role also mentions tools she knows. A role that names one of her tools does NOT override a long-bridge or hard-no requirement elsewhere in the posting. If you decide SEND, the reason must clearly support sending. Never let the decision contradict the reason.

# OUTPUT FORMAT
Respond with exactly two lines and nothing else:
DECISION: SEND or SKIP
REASON: one short sentence, max 15 words, plain and specific."""

# --- Capa 3: el juez evalúa las fichas y guarda las aprobadas ---
aprobados = []
cuenta_send = 0
cuenta_skip = 0
cuenta_error = 0

# TOPE DE SEGURIDAD: primero 20, no las 401. Subir a len(sobrevivientes) cuando esté validado.
tope_prueba = len(sobrevivientes)

for i, ficha in enumerate(sobrevivientes[:tope_prueba]):

    puesto_texto = "TITLE: " + ficha["titulo"] + "\n\nDESCRIPTION: " + ficha["texto"]

    respuesta_ia = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-5-nano",
            "messages": [
                {"role": "system", "content": instrucciones},
                {"role": "user", "content": puesto_texto}
            ]
        }
    )

    datos_ia = respuesta_ia.json()

    # --- Blindaje: si la IA no devolvió veredicto, anotamos y seguimos ---
    if "choices" not in datos_ia:
        print("---")
        print("⚠️ [" + str(i + 1) + "/" + str(tope_prueba) + "]", ficha["board"], "—", ficha["titulo"])
        print("La IA no devolvió veredicto. HTTP:", respuesta_ia.status_code)
        cuenta_error = cuenta_error + 1
        continue

    veredicto = datos_ia["choices"][0]["message"]["content"]

    print("---")
    print("[" + str(i + 1) + "/" + str(tope_prueba) + "]", ficha["board"], "—", ficha["titulo"])
    print(veredicto)

    # --- Leer la decisión y guardar si es SEND ---
    if "SEND" in veredicto:
        aprobados.append(ficha)
        cuenta_send = cuenta_send + 1
    else:
        cuenta_skip = cuenta_skip + 1

# ============================================================
# BLOQUE 6: resumen del juicio
# ============================================================

print("---")
print("=== RESUMEN DEL JUEZ ===")
print("Juzgadas:", tope_prueba)
print("SEND (aprobadas):", cuenta_send)
print("SKIP (descartadas):", cuenta_skip)
print("Errores de IA:", cuenta_error)
print("Fichas en la lista de aprobados:", len(aprobados))