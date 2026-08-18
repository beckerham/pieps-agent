"""
CP19: Guardrails — Themen-Prüfung vor jeder PIEPS-Antwort.
"""
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrail,
    RunContextWrapper,
    Runner,
)


class ThemenPruefung(BaseModel):
    ist_off_topic: bool
    begruendung: str


themen_waechter = Agent(
    name="ThemenWaechter",
    model="mistral-small-4",
    instructions="""Du prüfst ob eine Kundenanfrage zum Thema Grünspecht Gartentechnik gehört.

Erlaubt sind: Fragen zu Mährobotern, Heckenscheren, Laubbläsern, Bestellungen,
Preisen, Garantie, Ersatzteilen, Lieferung, Öffnungszeiten und Kundenservice.

Nicht erlaubt sind: alles andere — Gedichte, Rezepte, Politik, Allgemeinwissen,
Programmierung, andere Unternehmen, persönliche Beratung usw.

Antworte ausschließlich im vorgegebenen JSON-Format.""",
    output_type=ThemenPruefung,
)


async def themen_guardrail(
    ctx: RunContextWrapper, agent: Agent, input: str
) -> GuardrailFunctionOutput:
    result = await Runner.run(themen_waechter, input, context=ctx.context)
    pruefung = result.final_output_as(ThemenPruefung)
    return GuardrailFunctionOutput(
        output_info=pruefung,
        tripwire_triggered=pruefung.ist_off_topic,
    )


pieps_guardrail = InputGuardrail(guardrail_function=themen_guardrail)
