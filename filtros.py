import re

# NUEVO (Nov 2026) — los filtros de título viven acá, aparte de
# buscar_empleos.py, para que las pruebas (tests/) los puedan revisar sin
# correr el agente entero (sin bajar boards, sin gastar OpenAI, sin correo).
# Lección del proyecto de Matt (life-distributable): cada cambio pasa por
# pruebas automáticas antes de darse por bueno.


# NUEVO (Issue #1, gracias a @mattabate) — antes cada palabra de las listas
# se buscaba como pedazo de texto suelto ("intern" in titulo), así que
# "intern" mataba "International Payroll Manager" e "Internal Process Lead",
# "usa" mataba "Usability" y "it support" mataba "Audit Support".
# Ahora la palabra tiene que aparecer completa: ni pegada a una letra o
# número antes, ni después. Se usan (?<!\w) y (?!\w) en vez de \b para que
# también funcionen entradas con puntuación o espacios ("u.s.", "fp&a",
# "customer ", " sre ").
def calza(palabra, titulo):
    patron = r"(?<!\w)" + re.escape(palabra.strip()) + r"(?!\w)"
    return re.search(patron, titulo) is not None


def es_rol_no(titulo, perfil):
    """Checkpoint 0: el título es un rol que no es lo tuyo, o una pasantía.
    `titulo` tiene que venir en minúscula."""
    for malo in perfil["titulos_no"] + perfil["titulos_no_junior"]:
        if calza(malo, titulo):
            return True
    return False


def es_sospechoso(titulo, perfil):
    """Checkpoint 1: el título dice que es solo para EE. UU.
    `titulo` tiene que venir en minúscula."""
    for sospechoso in perfil["sospechosos"]:
        if calza(sospechoso, titulo):
            return True
    return False
