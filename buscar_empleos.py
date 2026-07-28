import feedparser
import requests
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