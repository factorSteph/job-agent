import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["OPENAI_API_KEY"]

# ============================================================
# EL PROMPT (copia temporal para probar — la fuente real vive en buscar_empleos.py)
# ============================================================
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

# ============================================================
# FICHAS DE PRUEBA — escritas a mano, yo controlo los casos
# ============================================================
fichas_prueba = [
    {
        "titulo": "AI Workflow Engineer",
        "texto": "Build and maintain automation pipelines using n8n and low-code tools. Integrate internal systems via APIs. Ideal for someone who built automation on top of a business background. 2-4 years experience."
    },
    {
        "titulo": "HR Business Partner",
        "texto": "Partner with business leaders on employee relations, performance management, and organizational development. Advise managers on HR policy. 5+ years as an HRBP required."
    },
    {
        "titulo": "Senior Software Engineer",
        "texto": "Design distributed systems in Java. Computer Science degree required. 7+ years of senior backend engineering. Deep expertise in microservices and cloud architecture."
    },
    {
        "titulo": "SharePoint & Microsoft 365 / Copilot Automation Specialist",
        "texto": "Build Copilot automations across Microsoft 365. Requires deep expertise in SharePoint governance, Microsoft Purview compliance, SPFx development, and Graph API integration. 5+ years administering enterprise M365 environments required."
    },
]

# ============================================================
# EL JUEZ — con blindaje: si la IA no devuelve veredicto, lo vemos
# ============================================================
for i, ficha in enumerate(fichas_prueba):

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

    print("---")
    print("[" + str(i + 1) + "/3]", ficha["titulo"])

    if "choices" not in datos_ia:
        print("⚠️ La IA NO devolvió veredicto. Código HTTP:", respuesta_ia.status_code)
        print("Respuesta cruda:", datos_ia)
        continue

    veredicto = datos_ia["choices"][0]["message"]["content"]
    print(veredicto)