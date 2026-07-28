import requests

url = "https://remoteok.com/api"
headers = {"User-Agent": "job-alert-agent"}
respuesta = requests.get(url, headers=headers)
datos = respuesta.json()
puestos = datos[1:]   # saltamos la metadata

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
    "change-management", "program management", "project management"
]

pasan = 0
mueren = 0
tags_que_pasan = set()
tags_que_mueren = set()

for puesto in puestos:
    tags = puesto["tags"]

    pasa_categoria = False
    for tag in tags:
        for buena in categorias_buenas:
            if buena in tag.lower():
                pasa_categoria = True

    if pasa_categoria:
        pasan = pasan + 1
        for tag in tags:
            tags_que_pasan.add(tag)
    else:
        mueren = mueren + 1

print("Pasarían:", pasan)
print("Morirían:", mueren)
print()
print("--- Tags que dispararon un PASE (los que tu lista captura) ---")
for tag in sorted(tags_que_pasan):
    capturado = False
    for buena in categorias_buenas:
        if buena in tag.lower():
            capturado = True
    if capturado:
        print(tag)