"""
CP19: Guardrails — Themen-Prüfung vor jeder PIEPS-Antwort.
Kein output_type / JSON-Schema — reines Text-Urteil (JA/NEIN).
"""
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrail,
    RunContextWrapper,
    Runner,
)


themen_waechter = Agent(
    name="ThemenWaechter",
    model="mistral-small-4",
    instructions="""Du prüfst ob eine Kundenanfrage zum Thema Grünspecht Gartentechnik gehört.

Erlaubt sind: Fragen zu Mährobotern, Heckenscheren, Laubbläsern, Bestellungen,
Preisen, Garantie, Ersatzteilen, Lieferung, Öffnungszeiten, Kundenservice,
Fehlercodes, Reparatur, Wartung, Widerrufsrecht und Kaufrecht.

Nicht erlaubt sind: alles andere — Gedichte, Rezepte, Politik, Allgemeinwissen,
Programmierung, andere Unternehmen, persönliche Beratung usw.

Antworte mit genau einem Wort:
JA  — wenn die Anfrage NICHTS mit Grünspecht zu tun hat.
NEIN — wenn die Anfrage zu Grünspecht gehört.""",
)


async def themen_guardrail(
    ctx: RunContextWrapper, agent: Agent, input: str
) -> GuardrailFunctionOutput:
    result = await Runner.run(themen_waechter, input, context=ctx.context)
    antwort = (result.final_output or "").strip().lower()
    ist_off_topic = antwort.startswith("ja")
    return GuardrailFunctionOutput(
        output_info=antwort,
        tripwire_triggered=ist_off_topic,
    )


pieps_guardrail = InputGuardrail(guardrail_function=themen_guardrail)
