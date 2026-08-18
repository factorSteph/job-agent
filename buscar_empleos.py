import feedparser
import requests
import os
from dotenv import load_dotenv

# NUEVO ronda 4 — load_dotenv() tiene que correr ANTES de importar perfiles,
# porque perfiles.py lee os.environ["ESTEBAN_EMAIL"] apenas se importa
# (a nivel de módulo, no dentro de una función). Si esto corriera después,
# localmente reventaría con KeyError aunque el .env sí tenga la variable.
load_dotenv()

from perfiles import PERFILES

# NUEVO (Sesión 11) — un motor, dos moldes. La variable de entorno PERFIL
# decide qué molde cargar (STEPH o ESTEBAN). Si no se define, corre STEPH
# por default (así los comandos locales de siempre no se rompen).
nombre_perfil = os.environ.get("PERFIL", "STEPH")
perfil = PERFILES[nombre_perfil]
print("=== Corriendo perfil:", perfil["nombre"], "===")

import time

def pedir_json(url, board_nombre, headers=None, timeout=15):
    """
    SOP de red: pide una URL y la lee como JSON, sin reventar el script
    si algo sale mal (respuesta vacía, timeout, servidor caído, rate limit).
    Devuelve el diccionario/lista si salió bien, o None si falló —
    y en ese caso imprime por qué, para que nunca sea una caja negra.
    """
    try:
        respuesta = requests.get(url, headers=headers, timeout=timeout)
    except requests.exceptions.RequestException as e:
        print("⚠️", board_nombre, "— falló la conexión:", type(e).__name__)
        return None

    if respuesta.status_code != 200:
        print("⚠️", board_nombre, "— HTTP", respuesta.status_code, "en vez de 200")
        return None

    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        print("⚠️", board_nombre, "— la respuesta no era JSON válido (posible rate limit o página vacía)")
        return None

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

def traducir_getonboard(puesto):
    # NUEVO (Sesión 11) — Paso 4 adelantado. Board LATAM, categorías
    # 'operations-management' y 'hr'. Reconocimiento hecho en vivo con
    # explorar.py antes de escribir esto (regla de Sesión 1: nunca filtrar
    # data que no viste).
    #
    # 'remote_modality' es un campo de 4 valores reales, mucho más honesto
    # que el 'region' de WWR: fully_remote, remote_local, hybrid, no_remote.
    # hybrid/no_remote piden presencia física -> descarte duro, sin duda.
    # remote_local es el gris (puede ser LATAM entero o un solo país; el
    # campo 'countries' no distingue, siempre dice ['Remote']) -> se deja
    # pasar a la IA en vez de matar a ciegas, mismo principio costo-asimétrico
    # de siempre. fully_remote -> pasa limpio.
    a = puesto["attributes"]

    modalidad = a.get("remote_modality", "")
    paises = a.get("countries", [])

    if modalidad == "fully_remote":
        restriccion = []
    elif modalidad == "remote_local":
        restriccion = []
    elif "Costa Rica" in paises:
        # NUEVO (Sesión 11, ronda 3) — regla confirmada por Steph, aplica a
        # los dos perfiles (motor compartido): una empresa LOCAL de Costa
        # Rica con modalidad híbrida o presencial SÍ se acepta, aunque no
        # sea remota. A diferencia de 'remote_local' (dato ambiguo, país
        # real desconocido), acá 'countries' SÍ trae el país real para
        # hybrid/no_remote — por eso solo entra por esta rama si dice
        # explícitamente "Costa Rica", no un "Remote" genérico.
        restriccion = []
    else:
        restriccion = ["fuera"]

    # 'company' llega expandido (pedido con expand[]=company) anidado en
    # attributes.company.data.attributes.name — NO en un bloque 'included'
    # aparte como el JSON:API típico. Si algún día el expand falla,
    # empresa cae a "sin_dato" en vez de romper el programa.
    empresa_data = a.get("company", {})
    empresa_data = empresa_data.get("data", {}) if isinstance(empresa_data, dict) else {}
    empresa_attrs = empresa_data.get("attributes", {}) if isinstance(empresa_data, dict) else {}
    empresa = empresa_attrs.get("name", "sin_dato")

    ficha = {
        "titulo": a["title"],
        "empresa": empresa,
        "url": puesto["links"]["public_url"],
        "texto": a.get("description", ""),
        "board": "GetOnBoard",
        "restriccion_pais": restriccion,
        "categorias": [a.get("category_name", "sin_dato")]
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
tope_himalayas = 5000

while offset < tope_himalayas:
    url_himalayas = "https://himalayas.app/jobs/api?limit=20&offset=" + str(offset)
    datos = pedir_json(url_himalayas, "Himalayas (offset " + str(offset) + ")")

    if datos is None:
        print("Himalayas: se corta la paginación en offset", offset, "— se conserva lo ya traído.")
        break

    lote = datos["jobs"]

    if lote == []:
        print("Himalayas: terminó solo, no chocó con el techo. Offset final:", offset)
        break

    for puesto in lote:
        agregar_si_nueva(traducir_himalayas(puesto))

    offset = offset + 20
    time.sleep(0.2)  # pausa chica para no gatillar rate limiting con ~250 pedidos seguidos
else:
    print("⚠️ Himalayas: CHOCÓ CON EL TECHO de", tope_himalayas, "— probablemente hay más puestos sin traer. Subir el techo de nuevo.")

# Remotive (una sola página, trae ~lo del día)
url_remotive = "https://remotive.com/api/remote-jobs"
datos = pedir_json(url_remotive, "Remotive")
if datos:
    for puesto in datos["jobs"]:
        agregar_si_nueva(traducir_remotive(puesto))

# Arbeitnow (una sola página, ~110 puestos)
url_arbeitnow = "https://www.arbeitnow.com/api/job-board-api"
datos = pedir_json(url_arbeitnow, "Arbeitnow")
if datos:
    for puesto in datos["data"]:
        agregar_si_nueva(traducir_arbeitnow(puesto))

# Jobicy (una sola página, ~100 puestos)
url_jobicy = "https://jobicy.com/api/v2/remote-jobs"
datos = pedir_json(url_jobicy, "Jobicy")
if datos:
    for puesto in datos["jobs"]:
        agregar_si_nueva(traducir_jobicy(puesto))

# RemoteOK (lista pelada, con metadata en [0] que hay que saltar)
url_remoteok = "https://remoteok.com/api"
headers = {"User-Agent": "job-alert-agent"}
datos = pedir_json(url_remoteok, "RemoteOK", headers=headers)
if datos:
    for puesto in datos[1:]:
        agregar_si_nueva(traducir_remoteok(puesto))

# Get on Board (dos categorías, cada una blindada por separado —
# si "hr" falla, "operations-management" igual puede pasar)
categorias_getonboard = ["operations-management", "hr"]
for categoria_gob in categorias_getonboard:
    url_getonboard = (
        "https://www.getonbrd.com/api/v0/categories/" + categoria_gob +
        "/jobs?per_page=100&lang=en&expand[]=company"
    )
    datos = pedir_json(url_getonboard, "GetOnBoard (" + categoria_gob + ")")
    if datos:
        for puesto in datos.get("data", []):
            agregar_si_nueva(traducir_getonboard(puesto))

print("--- Resumen de la traída (Bloque 1) ---")
conteo_por_board = {}
for ficha in fichas:
    b = ficha["board"]
    conteo_por_board[b] = conteo_por_board.get(b, 0) + 1
for board_nombre, cantidad in conteo_por_board.items():
    print(" ", board_nombre, "-", cantidad)

# ============================================================
# BLOQUE 2: filtrar la bolsa entera (los seis boards juntos)
# ============================================================

sospechosos = perfil["sospechosos"]

# NUEVO (Sesión 11) — PIEZA 1: filtro de título por ROL, ahora viene del
# perfil cargado arriba. Corre para los siete boards por igual.
titulos_no = perfil["titulos_no"]

empresas_no = perfil["empresas_no"]

titulos_no_junior = perfil["titulos_no_junior"]

categorias_buenas = perfil["categorias_buenas"]
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

api_key = os.environ["OPENAI_API_KEY"]
# --- El briefing permanente (SOP en la pared) — viene del perfil cargado ---
instrucciones = perfil["instrucciones"]

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
mi_correo = "steph.jimenezcor@gmail.com"  # remitente: siempre tu Gmail autenticado
correo_destino = perfil["correo_destino"]  # NUEVO (Sesión 11) — destinatario por perfil

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
    correo["Subject"] = "Job Agent (" + perfil["nombre"] + "): " + str(len(aprobados)) + " puestos encontrados"
    correo["From"] = mi_correo
    correo["To"] = correo_destino
    correo.set_content(cuerpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(mi_correo, clave_gmail)
        servidor.send_message(correo)

    print("---")
    print("Correo despachado con", len(aprobados), "puestos.")