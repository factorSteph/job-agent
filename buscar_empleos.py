import feedparser
import requests
import os
from dotenv import load_dotenv
regiones_buenas = ["worldwide", "americas", "latam", "cst", "utc-6"]

# ============================================================
# LAS MÁQUINAS TRADUCTORAS: una por board, todas producen la misma ficha estándar
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
    # ARREGLADO (Sesión 11) — antes esto era hardcodeado a "sin_dato", que el
    # Checkpoint 2 trata como "pasa siempre". Por eso TODO lo de Arbeitnow
    # pasaba el filtro de país sin importar si era Berlín, Londres o Konstanz
    # on-site. La API real trae "remote" (booleano) y "location" (texto).
    # Decisión de Steph: Arbeitnow es el board que más basura manda —
    # descarte duro si remote no es True. No pasa a la IA como contexto.
    es_remoto = puesto.get("remote", False)
    if es_remoto:
        restriccion = []
    else:
        restriccion = ["fuera"]

    ficha = {
        "titulo": puesto["title"],
        "empresa": puesto["company_name"],
        "url": puesto["url"],
        "texto": puesto["description"],
        "board": "Arbeitnow",
        "restriccion_pais": restriccion,
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
# BLOQUE 1: traer y traducir los seis boards a UNA bolsa común
# ============================================================

fichas = []

# NUEVO (Sesión 11) — deduplicación por URL. Un set() nunca permite
# repetidos, como una hoja de asistencia: si el nombre ya está marcado, no
# se vuelve a marcar. Se hace ACÁ, al armar la bolsa, no después: así un
# duplicado ni siquiera gasta checkpoints ni tokens de IA.
urls_vistas = set()

def agregar_si_nueva(ficha):
    if ficha["url"] in urls_vistas:
        return
    urls_vistas.add(ficha["url"])
    fichas.append(ficha)

# WWR
url_wwr = "https://weworkremotely.com/remote-jobs.rss"
feed = feedparser.parse(url_wwr)
for puesto in feed.entries:
    agregar_si_nueva(traducir_wwr(puesto))

# Himalayas (con paginación, con tope)
offset = 0
tope_himalayas = 2000

while offset < tope_himalayas:
    url_himalayas = "https://himalayas.app/jobs/api?limit=20&offset=" + str(offset)
    respuesta = requests.get(url_himalayas)
    datos = respuesta.json()
    lote = datos["jobs"]

    if lote == []:
        break

    for puesto in lote:
        agregar_si_nueva(traducir_himalayas(puesto))

    offset = offset + 20

# Remotive (una sola página, trae ~lo del día)
url_remotive = "https://remotive.com/api/remote-jobs"
respuesta = requests.get(url_remotive)
datos = respuesta.json()
for puesto in datos["jobs"]:
    agregar_si_nueva(traducir_remotive(puesto))

# Arbeitnow (una sola página, ~110 puestos)
url_arbeitnow = "https://www.arbeitnow.com/api/job-board-api"
respuesta = requests.get(url_arbeitnow)
datos = respuesta.json()
for puesto in datos["data"]:
    agregar_si_nueva(traducir_arbeitnow(puesto))

# Jobicy (una sola página, ~100 puestos)
url_jobicy = "https://jobicy.com/api/v2/remote-jobs"
respuesta = requests.get(url_jobicy)
datos = respuesta.json()
for puesto in datos["jobs"]:
    agregar_si_nueva(traducir_jobicy(puesto))

# RemoteOK (lista pelada, con metadata en [0] que hay que saltar)
url_remoteok = "https://remoteok.com/api"
headers = {"User-Agent": "job-alert-agent"}
respuesta = requests.get(url_remoteok, headers=headers)
datos = respuesta.json()
for puesto in datos[1:]:
    agregar_si_nueva(traducir_remoteok(puesto))

# ============================================================
# BLOQUE 2: filtrar la bolsa entera (los seis boards juntos)
# ============================================================

sospechosos = ["us only", "us based", "usa", "united states", "u.s.", "w2"]

# NUEVO (Capa 3.1) — PIEZA 1: filtro de título por ROL.
# Corre para los seis boards por igual, no depende de categorías.
# Rechaza los NO conocidos (Categoría A: áreas que no son lo tuyo;
# Categoría C: pasantías/entry-level). Es barato: mata antes de gastar IA.
titulos_no = [
    # --- Categoría A: áreas que no son lo tuyo ---
    # 'customer ' (con espacio) es amplio a propósito: cualquier título que
    # lidere con Customer casi seguro es servicio/soporte/CX, tu NO duro.
    "customer ",
    "advertising", "marketing",
    "it support", "it maintenance", "help desk", "helpdesk", "service desk",
    "security engineer", "web developer", "web development",
    "ai enablement", "ai strategy", "ai transformation",
    # --- Categoría A (Sesión 11): ingeniería genérica de software/infra.
    # Se colaban con razones tipo "aligns with her operations focus" solo
    # porque el título dice "automation" o "engineer" en algún lado.
    # OJO: NO se pone "automation engineer" suelto — mataría matches buenos
    # (AI Integration & Automation, Automation Specialist). Se apunta a las
    # combinaciones específicas que salieron hoy (QA/test/mobile automation
    # de software) y a ingeniería de infraestructura pura. ---
    "cloud engineer", "site reliability", " sre ", "it engineer",
    "software engineer", "qa engineer", "quality assurance engineer",
    "qa automation", "automation qa", "test automation", "automation tester",
    "mobile automation", "mobile engineer", "backend engineer", "frontend engineer",
    "full stack", "fullstack", "devops engineer", "platform engineer",
    "systems engineer", "infrastructure engineer",
    "machine learning engineer", "mlops", "computer vision",
    "llm application engineer",
    # --- Categoría A (Sesión 11): retail / logística.
    # Nada cubría esto — "Food store supervisor" y "Distribution Centers"
    # (Ulta) pasaron limpio con razones de "operations" genérico. ---
    "distribution center", "warehouse", "store supervisor",
    "retail supervisor", "retail store",
    # --- Categoría A (Capa 3.2): roles colados por sigla o campo ajeno.
    # La IA los vendía con "the bridge is learnable" aunque son otro campo. ---
    "csm", "customer success",     # Customer Success (se colaba por la sigla)
    "gtm", "go-to-market",         # go-to-market = ventas/marketing
    "hubspot",                     # herramienta de marketing/CRM
    "data labeler", "data annotator", "data annotation",  # trabajo por pieza
    "ai trainer",                  # anotación/entrenamiento por pieza
    "scrum master",                # no es el rol que busca
    # --- Categoría A (Capa 3.3): FINANZAS/CONTABILIDAD = campo ajeno.
    # OJO: payroll SÍ es su campo (viene de ahí). Estos NO: son finanzas pura. ---
    "accounts payable", "accounts receivable", "accountant",
    "investment banking", "treasury", "controller", "fp&a",
    "financial analyst", "bookkeep",
    # --- Categoría A (Capa 3.3): títulos de fábrica de anotación/entrenamiento
    # de IA (micro1 y similares publican decenas con títulos "expert/specialist"
    # que en realidad son trabajo por pieza para entrenar modelos). ---
    "domain expert", "domain specialist", "ai trainer", "competitive coder",
    "data entry", "data annotation", "annotator",
    # NOTA: 'solutions'/'solution engineer' se dejó FUERA a propósito:
    # vive en dos mundos (presales ajeno vs. Solution Engineer @ UiPath = RPA,
    # que sí es su campo). Un filtro de string no distingue contexto; que la
    # IA / la validación manual decidan esos.
    # --- Categoría C: pasantías / entry-level ---
    "intern", "internship", "werkstudent", "trainee",
    "office assistant", "entry level", "entry-level"
]

# NUEVO (Capa 3.3) — lista negra de EMPRESAS-fábrica. Algunas empresas publican
# decenas de pseudo-puestos (anotación/entrenamiento de IA por pieza) con títulos
# creativos que se cuelan por título. Se matan por empresa, no por título.
# Solo actúa en boards que traen 'empresa' (Himalayas, Jobicy, Remotive, RemoteOK,
# Arbeitnow); WWR manda 'sin_dato' y ahí no aplica. Crece con la experiencia,
# igual que titulos_no. micro1 NO se metió todavía: primero medimos cuántos
# sobreviven al prompt endurecido antes de usar el instrumento más brutal.
empresas_no = [
    "dataannotation",
    "micro1",           # fábrica de entrenamiento de modelos: publica decenas
                        # de pseudo-puestos que se disfrazan con vocabulario de
                        # ops/automation. Confirmado por su propio reclutamiento
                        # ("leveraging your expertise to train AI models").
]

# NUEVO (Capa 3.1) — 'junior' se rechaza SOLO pegado a roles administrativos,
# no como palabra suelta (un "junior automation" sí puede llegar a la IA).
titulos_no_junior = [
    "junior assistant", "junior analyst", "junior coordinator",
    "junior office", "junior administrative", "junior admin",
    "junior clerk", "junior support"
]

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
murio_titulo = 0          # US-only (geo)
murio_titulo_rol = 0      # NUEVO (Capa 3.1): rol que no es lo tuyo / pasantía
murio_empresa = 0         # NUEVO (Capa 3.3): empresa-fábrica (lista negra)
murio_pais = 0
# NUEVO (Capa 3.1): ya no hay muertes por categoría. Contamos cuántos
# pasaron SIN categoría útil (para vigilar cuánto trabajo le cae a la IA).
sin_categoria_util = 0

for ficha in fichas:

    titulo = ficha["titulo"].lower()
    empresa = ficha["empresa"].lower()
    restriccion = ficha["restriccion_pais"]
    categorias = ficha["categorias"]

    # --- CHECKPOINT 0 (NUEVO): título de ROL prohibido ---
    es_rol_no = False
    for malo in titulos_no:
        if malo in titulo:
            es_rol_no = True
    for malo in titulos_no_junior:
        if malo in titulo:
            es_rol_no = True

    if es_rol_no:
        murio_titulo_rol = murio_titulo_rol + 1
        continue

    # --- CHECKPOINT 0b (NUEVO Capa 3.3): empresa-fábrica ---
    # 'sin_dato' nunca calza con una empresa real, así que WWR pasa sin problema.
    es_empresa_no = False
    for mala in empresas_no:
        if mala in empresa:
            es_empresa_no = True

    if es_empresa_no:
        murio_empresa = murio_empresa + 1
        continue

    # --- CHECKPOINT 1: título sospechoso (geo US) ---
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

    # --- CHECKPOINT 3 (NUEVO comportamiento): categoría ya NO mata ---
    # Antes: categoría fuera de lista => descartado (mataba buenos matches
    # catalogados como "engineering"/"ai" en Himalayas/Jobicy).
    # Ahora: la categoría solo INFORMA. Si no calza, igual pasa a la IA,
    # que es mejor juez que una lista de strings. Solo lo anotamos.
    tiene_categoria_util = False
    if "sin_dato" in categorias:
        tiene_categoria_util = False
    else:
        for categoria in categorias:
            for buena in categorias_buenas:
                if buena in categoria.lower():
                    tiene_categoria_util = True

    if not tiene_categoria_util:
        sin_categoria_util = sin_categoria_util + 1

    # --- Si llegó hasta acá, pasó los checkpoints y va a la IA ---
    sobrevivientes.append(ficha)


# ============================================================
# BLOQUE 3: resumen
# ============================================================

print("---")
print("Total traído:", len(fichas))
print("Sobrevivientes (van a la IA):", len(sobrevivientes))
print("Murieron por ROL (no es lo tuyo / pasantía):", murio_titulo_rol)
print("Murieron por EMPRESA-fábrica:", murio_empresa)
print("Murieron por título (geo US):", murio_titulo)
print("Murieron por país:", murio_pais)
print("Pasaron sin categoría útil (le tocan a la IA):", sin_categoria_util)

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
if len(sobrevivientes) > 0:
    print("Promedio por ficha:", total_tokens // len(sobrevivientes))

# ============================================================
# BLOQUE 5 (Capa 3): la IA juzga
# ============================================================

load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]

# --- El briefing permanente (SOP en la pared) ---
instrucciones = """You are a screening assistant for Steph, a job seeker. You read ONE job posting and decide SEND or SKIP. You are the first filter before she looks at it.

# HOW TO DECIDE — run these steps IN ORDER. Stop at the first one that fires.

STEP 1 — WRONG FIELD? If the role's core function is in a different field, decide SKIP immediately. Do NOT reason about learnable tools or short bridges. These fields are all SKIP no matter how learnable they look:
- Customer support / success / service / experience (CX)
- Sales, presales, go-to-market (GTM), "new logo", account executive, solutions selling
- Marketing / advertising / growth / SEO / tracking / analytics-for-marketing
- Recruiting / talent acquisition
- Classic HR: HR Business Partner, HR Manager, generalist HR
- IT support / help desk / IT maintenance
- Data labeling / data annotation / AI training-by-example (piece work). This INCLUDES "domain expert" / "specialist" roles that are really about supplying knowledge to train an AI model by piece (finance domain expert, healthcare specialist, competitive coder, investment banking expert). If the real job is "lend your expertise to train a model", it is piece work — SKIP.
- Finance and accounting as the core: accounts payable, accounts receivable, accountant, bookkeeping, treasury, investment banking, financial analyst, FP&A, controller. NOTE: payroll operations IS her field (she came from there); do not confuse payroll with general accounting/AP/AR.
- Pure software engineering, security engineering, web development, DevOps, data engineering, data science, ML/AI research engineering (Member of Technical Staff, Research Engineer, Applied Scientist). These are long-runway technical roles, not her operations/automation field, even when the posting says "automation".
A role in the wrong field is a SKIP even if it names a tool she knows (Salesforce, HubSpot, Copilot). The tool does not save a wrong-field role.

STEP 2 — HARD BARRIER? If STEP 1 did not fire, SKIP if any of these is true:
- The role hard-REQUIRES a certification or degree she does not hold as a strict, non-negotiable prerequisite (her credentials are listed below).
- The role rests on a LONG bridge: a deep technical foundation that takes months or years to build (software dev from zero, CS degree required, senior coding in a language she does not use, deep finance/accounting as the core).
- GEOGRAPHY: the role hard-requires residency somewhere she is not, or names a non-remote locale (US-only, "London on-site", "must reside in Brazil", a German Werkstudent role). She is in Costa Rica and needs remote-global or LATAM-open roles. If it names a country/city as a requirement and is not clearly remote-global, SKIP.
- STRUCTURAL JUNK: you cannot tell what the role even is (empty/generic title, "Expression of Interest", "Speculative CV", no real description). Not "unsure if it fits" — "cannot tell what it is." That is always SKIP.

STEP 3 — ONLY IF IT SURVIVED STEPS 1 AND 2: decide SEND only if the CORE of the role is genuinely operations, process, or automation work — the kind of thing in the GOOD MATCH list below. The default here is SKIP. Flip to SEND only when the role's main purpose (not a side mention) is building/running automation, redesigning processes, or leading operations. A posting that merely CONTAINS the words "AI", "automation", "workflow", or "operations" is NOT enough — many wrong-field roles sprinkle those words. Ask: "is the PRIMARY job operations/process/automation, like her bullseye examples?" If yes, SEND. If it is some other job that happens to mention those words, or you are unsure what the core actually is, SKIP.
Do NOT send a role just because a missing tool is "learnable" — that only matters AFTER you have confirmed the core is in her field. "Learnable tool" is never a reason to SEND on its own.
The asymmetry note (a missed job is lost forever) still matters, but experience shows the bigger problem is a flood of wrong-field roles wearing automation vocabulary. So at STEP 3 the rule is: when genuinely unsure whether the CORE is her field, SKIP.

# THE BRIDGE RULE (this is what you keep getting wrong)
A "short bridge" is a missing TOOL inside a role that is ALREADY in her field. It is NEVER a way into a different field. Never justify a SEND by saying the field is "learnable." Learning HubSpot does not make a marketing role fit. Learning a CRM does not make a customer-success role fit. The bridge crosses a gap in tools, never a gap in career direction.

# WHO STEPH IS
Operations and automation leader, ~a decade running HR shared-services and payroll operations across Latin America and North America. Founded and scaled a regional operations hub, held service levels above 95% across 8 countries. Since early 2026 she builds automation end-to-end: Power Automate (Cloud and Desktop), Copilot Studio, Claude Code, agentic workflow design, Git/GitHub, spec-driven development. Learning Python by building a real project. Her lifelong pattern: enter a domain WITHOUT the formal credential, build the capability by doing, earn the title after. A posting asking for experience she is actively building is NOT an automatic disqualifier.

Her credentials (for STEP 2): Bachelor's in Public Administration (UCR), NLP Master (IANLP), Storytelling & Persuasion (INCAE), Certified Project Practitioner (GE360), Lean Six Sigma Green Belt in progress. If a role hard-requires a credential NOT on this list, that counts against it. If it IS on this list, she has it.

# WHAT A GOOD MATCH LOOKS LIKE (STEP 3 territory)
Operations / process / automation with building at the center: People Ops AI & Automation Manager, AI Process Operations Manager, Operations & Automation Lead, Workflow / Process Automation Specialist, Process Improvement / Operational Excellence Lead, RevOps or business-ops roles where automation is central. Remote-global or LATAM-open.

# CALIBRATION EXAMPLES
SEND — Enterprise AI Workflow / Automation Specialist: designs AI-powered workflows, process optimization, change management. Her exact bullseye. Missing an AI platform is a short bridge.
SEND — AI Workflow Engineer on a business background (names n8n): building automation is the core.
SEND — Operational Excellence / Process Improvement Lead: process redesign, Lean Six Sigma, Kaizen, change management.
SKIP — Customer Success Manager "CRM is learnable": wrong field (STEP 1), tool does not save it.
SKIP — Founding GTM Engineer "missing tools are short bridges": GTM is sales, wrong field (STEP 1).
SKIP — HubSpot Implementation Specialist: HubSpot is marketing/CRM, wrong field (STEP 1).
SKIP — Staff Solutions Architect, New Logo: presales sales, wrong field (STEP 1).
SKIP — Data Labeler / AI Trainer: piece work below her level, wrong field (STEP 1).
SKIP — Accounts Payable Specialist "missing Bill.com is learnable": finance is wrong field (STEP 1); the learnable tool does not save it.
SKIP — Investment Banking Expert / AI Finance Domain Expert: piece work training a model with domain knowledge, wrong field (STEP 1).
SKIP — Member of Technical Staff, Frontier AI / Research Engineering: ML research engineering, long-runway technical field (STEP 1), not her operations/automation work.
SKIP — Personal Assistant / Data Entry Administrator "in-field operations": admin/piece work, NOT operations/process/automation core. Mentioning "operations" does not make it her field (STEP 3 default SKIP).
SKIP — DevOps / Data Engineer "Kubernetes is learnable": long-runway technical field (STEP 1); learnable tool is irrelevant when the field is wrong.
SKIP — Senior Software Engineer / Security Engineer, CS degree + senior coding: long bridge (STEP 2).
SKIP — "Expression of Interest", no real description: structural junk (STEP 2).
SEND — Business Operations Partner / Chief Operating Officer where the CORE is running/redesigning operations: her field, send.

# CONSISTENCY RULE
Your DECISION must match your REASON. If your reason names a wrong field, a hard barrier, a long bridge, junk, or a geo restriction, you MUST decide SKIP — even if the role also mentions a tool she knows. Never let the decision contradict the reason.

# OUTPUT FORMAT
Respond with exactly two lines and nothing else:
DECISION: SEND or SKIP
REASON: one short sentence, max 15 words, plain and specific. Name which STEP fired if SKIP."""

# --- Capa 3: el juez evalúa las fichas y guarda las aprobadas ---
aprobados = []
cuenta_send = 0
cuenta_skip = 0
cuenta_error = 0

# TOPE: en producción va en len(sobrevivientes). Bajarlo a un número chico (ej. 20) para probar barato
tope_juez = len(sobrevivientes)

for i, ficha in enumerate(sobrevivientes[:tope_juez]):

    puesto_texto = "TITLE: " + ficha["titulo"] + "\n\nDESCRIPTION: " + ficha["texto"]

    # --- Blindaje de RED (Capa 3.2): la llamada puede fallar antes de que
    # llegue respuesta (timeout, conexión cortada). Eso NO es una respuesta
    # mala (que el blindaje del "choices" cubre): es una EXCEPCIÓN que mataría
    # el programa entero. try/except la atrapa, la cuenta como error y sigue
    # con la siguiente ficha. Una ficha perdida de cientos no mueve la aguja;
    # una corrida muerta a media noche en Actions, sí. ---
    try:
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
            },
            timeout=30
        )
        datos_ia = respuesta_ia.json()
    except requests.exceptions.RequestException as e:
        print("---")
        print("⚠️ [" + str(i + 1) + "/" + str(tope_juez) + "]", ficha["board"], "—", ficha["titulo"])
        print("Falló la llamada de red (timeout/conexión). Se salta esta ficha.")
        print("Detalle:", type(e).__name__)
        cuenta_error = cuenta_error + 1
        continue

    # --- Blindaje: si la IA no devolvió veredicto, anotamos y seguimos ---
    if "choices" not in datos_ia:
        print("---")
        print("⚠️ [" + str(i + 1) + "/" + str(tope_juez) + "]", ficha["board"], "—", ficha["titulo"])
        print("La IA no devolvió veredicto. HTTP:", respuesta_ia.status_code)
        cuenta_error = cuenta_error + 1
        continue

    veredicto = datos_ia["choices"][0]["message"]["content"]

    print("---")
    print("[" + str(i + 1) + "/" + str(tope_juez) + "]", ficha["board"], "—", ficha["titulo"])
    print(veredicto)

    # --- Leer la decisión y guardar si es SEND ---
    if "SEND" in veredicto:
        if "REASON:" in veredicto:
            ficha["razon"] = veredicto.split("REASON:")[1].strip()
        else:
            ficha["razon"] = "sin_dato"
        aprobados.append(ficha)
        cuenta_send = cuenta_send + 1
    else:
        cuenta_skip = cuenta_skip + 1

# ============================================================
# BLOQUE 6: resumen del juicio
# ============================================================

print("---")
print("=== RESUMEN DEL JUEZ ===")
print("Juzgadas:", tope_juez)
print("SEND (aprobadas):", cuenta_send)
print("SKIP (descartadas):", cuenta_skip)
print("Errores de IA:", cuenta_error)
print("Fichas en la lista de aprobados:", len(aprobados))

# ============================================================
# BLOQUE 7 (Capa 4): despachar el correo
# ============================================================

import smtplib
from email.message import EmailMessage

clave_gmail = os.environ["GMAIL_APP_PASSWORD"]
mi_correo = "steph.jimenezcor@gmail.com"

if aprobados == []:
    print("---")
    print("0 aprobados hoy. No se manda correo.")
else:
    cuerpo = "Tu agente encontró " + str(len(aprobados)) + " puestos hoy:\n\n"
    # NUEVO (Capa 3.1) — PIEZA 5: numeración. enumerate arranca en 1 para
    # que cada puesto salga con su número y no te pierdas al validar.
    for numero, ficha in enumerate(aprobados, start=1):
        cuerpo = cuerpo + str(numero) + ". " + ficha["titulo"] + " | " + ficha["razon"] + " Link: " + ficha["url"] + "\n\n"

    correo = EmailMessage()
    correo["Subject"] = "Job Agent: " + str(len(aprobados)) + " puestos encontrados"
    correo["From"] = mi_correo
    correo["To"] = mi_correo
    correo.set_content(cuerpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(mi_correo, clave_gmail)
        servidor.send_message(correo)

    print("---")
    print("Correo despachado con", len(aprobados), "puestos.")