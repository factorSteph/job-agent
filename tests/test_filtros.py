# NUEVO (Nov 2026) — lección del proyecto de Matt (life-distributable): cada
# cambio pasa por pruebas automáticas antes de darse por bueno. El bug del
# Issue #1 ("intern" mataba "International") lo habría atrapado una prueba
# de tres líneas como las de abajo.
#
# Corren solas en GitHub cada vez que se sube un cambio (workflow "pruebas").
# Para correrlas a mano:  python -m unittest discover -s tests -t .
#
# Cómo usarlas: si un puesto bueno se pierde, o se cuela uno malo, se agrega
# su título a la lista que corresponde. Así ese error no vuelve nunca.

import os
import unittest

# perfiles.py lee ESTEBAN_EMAIL apenas se importa; en las pruebas no hace
# falta el correo real.
os.environ.setdefault("ESTEBAN_EMAIL", "prueba@example.com")

from filtros import calza, es_rol_no, es_sospechoso  # noqa: E402
from perfiles import PERFILES  # noqa: E402


def descartado(titulo, perfil):
    t = titulo.lower()  # buscar_empleos.py también lo pasa a minúscula
    return es_rol_no(t, perfil) or es_sospechoso(t, perfil)


# Títulos que el filtro NUNCA debe botar (le tocan a la IA).
PASAN = {
    "STEPH": [
        "International Payroll Operations Manager",   # Issue #1
        "Internal Process Improvement Lead",          # Issue #1
        "Business Process Automation Lead",
        "Operations Manager (Remote, LATAM)",
        "Audit Support Specialist",                   # antes "it support" lo mataba
        "Usability Research Program Manager",         # antes "usa" lo mataba
        "Shared Services Program Manager",
    ],
    "ESTEBAN": [
        "Technical Account Manager - Security",
        "Technical Engagement Manager",
        "Solutions Engineer (Cybersecurity)",
        "International Security Consultant",          # Issue #1
        "Internal Penetration Tester",                # Issue #1
        "Senior Pentester - LATAM",
        # Nov 2026 — técnicos y mixtos que le sirven; la IA decide, el
        # filtro de títulos no los puede botar.
        "Engagement Manager, Offensive Security",
        "Cybersecurity Instructor",
        "Security Trainer - Remote",
        "Customer Success Engineer - Security",
        "Systems Engineer - Palo Alto Networks",      # preventa en vendors
        "Cloud Security Engineer",                     # no lo mata "cloud engineer"
        "Developer Advocate, Security",
        "Incident Response Consultant",
        "PAM Consultant (BeyondTrust)",
        "Knowledge Staff Engineer",
        "Product Facilitator",
    ],
}

# Títulos que el filtro SIEMPRE debe botar.
CAEN = {
    "STEPH": [
        "Software Engineer Intern",
        "Customer Success Manager",
        "CSM - Mid Market",
        "GTM Operations Lead",
        "Data Entry Clerk",
        "Senior Accountant",
        "Payroll Specialist (US only)",
        "Operations Manager - USA",
        "Junior Analyst, Operations",
    ],
    "ESTEBAN": [
        "Security Intern",
        "Cybersecurity Internship 2027",
        "Entry-Level SOC Analyst",
        "AI Trainer - Security",
        "Security Engineer (US based)",
        # Nov 2026 — títulos reales que le llegaron y NO quería.
        "Knack: Cloud Engineer",
        "OneImaging: Cloud Systems Administrator",
        "Horizon3: Staff Technical Support Engineer (Web App)",
        "Research Engineer Privacy and Anonymization",
        "Entwickler One Identity Manager – IAM, C# / .NET (m/w/d)",
        "Consultant Informationssicherheit / IT-Risikomanagement – ISO 27001 (m/w/d)",
        "DevSecOps Engineer",
        "Senior Software Engineer, Security",
        "Site Reliability Engineer (Security)",
        "Account Executive - Cybersecurity",
        "Account Manager | Legal Tech | SaaS (x/w/m) - Remote",
    ],
}


class PruebaCalza(unittest.TestCase):
    def test_palabra_completa(self):
        self.assertTrue(calza("intern", "software intern"))
        self.assertFalse(calza("intern", "international payroll"))
        self.assertFalse(calza("intern", "internal audit"))

    def test_entradas_con_puntuacion_y_espacios(self):
        self.assertTrue(calza("u.s.", "payroll lead (u.s.)"))
        self.assertTrue(calza("fp&a", "fp&a manager"))
        self.assertTrue(calza(" sre ", "senior sre"))
        self.assertTrue(calza("customer ", "customer support lead"))
        self.assertFalse(calza("customer ", "customers ops"))


class PruebaPerfiles(unittest.TestCase):
    def test_los_buenos_pasan(self):
        for nombre, titulos in PASAN.items():
            perfil = PERFILES[nombre]
            for titulo in titulos:
                with self.subTest(perfil=nombre, titulo=titulo):
                    self.assertFalse(descartado(titulo, perfil), "se botó un puesto bueno")

    def test_los_malos_caen(self):
        for nombre, titulos in CAEN.items():
            perfil = PERFILES[nombre]
            for titulo in titulos:
                with self.subTest(perfil=nombre, titulo=titulo):
                    self.assertTrue(descartado(titulo, perfil), "se coló un puesto que no va")


if __name__ == "__main__":
    unittest.main()
