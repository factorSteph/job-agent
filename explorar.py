import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

aprobados = [
    {"titulo": "Puesto de prueba A", "empresa": "Empresa X", "url": "https://ejemplo.com/a", "board": "WWR", "razon": "Strong fit por tal cosa"},
    {"titulo": "Puesto de prueba B", "empresa": "Empresa Y", "url": "https://ejemplo.com/b", "board": "Jobicy", "razon": "Short bridge en tal herramienta"}
]

load_dotenv()
clave = os.environ["GMAIL_APP_PASSWORD"]

correo = EmailMessage()
correo["Subject"] = "Prueba del job agent"
correo["From"] = "steph.jimenezcor@gmail.com"
correo["To"] = "steph.jimenezcor@gmail.com"
correo.set_content("Hola desde Python. Si estás leyendo esto, la ventanilla funciona.")

cuerpo = ""
for ficha in aprobados:
    cuerpo = cuerpo + ficha["titulo"] + "| " + ficha["razon"] + " Link: " + ficha["url"] + "\n"
print(cuerpo)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
    servidor.login("steph.jimenezcor@gmail.com", clave)
    servidor.send_message(correo)

print("Enviado.")