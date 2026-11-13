# NUEVO (Nov 2026) — lección del proyecto de Matt (life-distributable): cuando
# algo falla, el aviso le llega a la persona, no se queda en un log que nadie
# lee. Antes, si la corrida salía en ROJO, GitHub solo le avisaba a la dueña
# del repo; a Esteban simplemente no le llegaba el correo del día y no tenía
# cómo saber si era "hoy no hubo nada" o "el agente está roto".
#
# El workflow corre este script SOLO si un paso anterior falló
# (if: failure()). Le escribe al destinatario del perfil, con copia a Steph.

import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

from perfiles import PERFILES

nombre_perfil = os.environ.get("PERFIL", "STEPH")
perfil = PERFILES[nombre_perfil]

mi_correo = "steph.jimenezcor@gmail.com"  # remitente: siempre el Gmail autenticado
destino = perfil["correo_destino"]

# Modo prueba (botón "Run workflow" con "probar_aviso" marcado): manda el
# aviso SOLO a Steph, para revisar que el correo sale sin asustar a Esteban.
es_prueba = os.environ.get("PRUEBA") == "1"
if es_prueba:
    destino = mi_correo

# Link directo a la corrida que falló, para ver el log con un clic.
link_corrida = (
    os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/"
    + os.environ.get("GITHUB_REPOSITORY", "factorSteph/job-agent")
    + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "")
)

correo = EmailMessage()
correo["Subject"] = ("[PRUEBA] " if es_prueba else "") + "Job Agent (" + perfil["nombre"] + "): la corrida de hoy FALLÓ"
correo["From"] = mi_correo
correo["To"] = destino
if destino != mi_correo:
    correo["Cc"] = mi_correo
correo.set_content(
    "Hoy el agente no pudo terminar, así que no hay lista de puestos.\n\n"
    "Esto NO significa que no hubo ofertas: significa que algo se rompió "
    "(saldo de OpenAI, boards caídos, la red o el correo).\n\n"
    "Detalle de la corrida: " + link_corrida + "\n\n"
    "Mañana vuelve a intentar solo. Lo que no se alcanzó a juzgar hoy se "
    "vuelve a revisar mañana.\n"
)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
    servidor.login(mi_correo, os.environ["GMAIL_APP_PASSWORD"])
    servidor.send_message(correo)

print("Aviso de falla enviado a", destino)
