import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    function_tool,
    set_default_openai_client,
    set_default_openai_api,
    set_tracing_disabled,
)
from agents import handoff
from rag import suche_dokumente as _suche_dokumente
from guardrails import pieps_guardrail

load_dotenv()

# --- EUrouter-Konfiguration (Checkpoint 2) ---
client = AsyncOpenAI(
    api_key=os.getenv("EUROUTER_API_KEY"),
    base_url="https://api.eurouter.ai/api/v1",
)
set_default_openai_client(client)
set_default_openai_api("chat_completions")
set_tracing_disabled(True)

# --- Testdaten Bestellungen (Checkpoint 4) ---
BESTELLUNGEN = {
    "GS-2026-0042": {
        "artikel": "RASENFLITZER 3000",
        "status": "versendet",
        "sendungsnummer": "DHL-771234567",
    },
    "GS-2026-0043": {
        "artikel": "Heckenschere HS-40",
        "status": "in Bearbeitung",
        "sendungsnummer": None,
    },
    "GS-2026-0044": {
        "artikel": "RASENFLITZER 1000 Ersatzmesser (4er-Set)",
        "status": "storniert",
        "sendungsnummer": None,
    },
}


@function_tool
def bestellstatus_pruefen(bestellnummer: str) -> str:
    """Prüft den aktuellen Lieferstatus einer Kundenbestellung bei Grünspecht Gartentechnik.

    Verwende dieses Werkzeug immer, wenn ein Kunde nach einer Bestellung,
    dem Lieferstatus oder einer Sendungsnummer fragt und eine Bestellnummer nennt
    oder danach gefragt werden kann.

    Args:
        bestellnummer: Die Bestellnummer im Format GS-JJJJ-NNNN, z. B. GS-2026-0042.

    Returns:
        Artikelname, Bestellstatus und ggf. Sendungsnummer der Bestellung.
    """
    key = bestellnummer.strip().upper().replace(" ", "")
    bestellung = BESTELLUNGEN.get(key)

    if not bestellung:
        return (
            f"Keine Bestellung mit der Nummer '{bestellnummer}' gefunden. "
            "Bitte prüfen Sie die Schreibweise der Bestellnummer."
        )

    antwort = (
        f"Bestellung {key}: {bestellung['artikel']} – Status: {bestellung['status']}."
    )
    if bestellung["sendungsnummer"]:
        antwort += f" Sendungsnummer: {bestellung['sendungsnummer']}."
    return antwort


# --- CP16: RAG-Suche als Tool ---
@function_tool
def dokumente_durchsuchen(frage: str) -> str:
    """Durchsucht die Grünspecht-Produktdokumentation nach relevanten Informationen.

    Verwende dieses Werkzeug bei Fragen zu Produkten, technischen Daten, Preisen,
    Garantie, Ersatzteilen, Fehlercodes, Bedienung oder Lieferbedingungen.

    Args:
        frage: Die Kundenfrage als Freitext.

    Returns:
        Relevante Abschnitte aus den Grünspecht-Dokumenten.
    """
    return _suche_dokumente(frage)


# --- Eigenes Werkzeug: Öffnungszeiten & Kontakt (Checkpoint 5) ---
@function_tool
def servicezeiten_und_kontakt() -> str:
    """Gibt die Servicezeiten und Kontaktdaten des Grünspecht-Kundenservice zurück.

    Verwende dieses Werkzeug, wenn ein Kunde nach Öffnungszeiten, Erreichbarkeit,
    Telefonnummer, E-Mail-Adresse oder allgemeinen Kontaktmöglichkeiten fragt.

    Returns:
        Servicezeiten, Telefonnummer und E-Mail-Adresse des Kundenservice.
    """
    return (
        "Grünspecht Kundenservice – Bad Salzuflen\n"
        "Telefon: 05222 / 123456\n"
        "E-Mail: support@gruenspecht.de\n"
        "Montag bis Freitag: 8:00 – 17:00 Uhr\n"
        "Samstag: 9:00 – 13:00 Uhr"
    )


# --- Rollenbeschreibung (Checkpoint 3) ---
INSTRUCTIONS = """Du bist PIEPS, der Kundenservice-Assistent der Grünspecht Gartentechnik GmbH aus Bad Salzuflen.

Grünspecht stellt Mähroboter der Serie RASENFLITZER, Heckenscheren und Laubbläser her. Das Unternehmen existiert seit 1978 und beschäftigt 140 Mitarbeitende.

Deine Kundschaft ist im Durchschnitt 58 Jahre alt. Sieze die Kunden stets. Antworte freundlich, klar und ohne technischen Fachjargon. Halte deine Antworten kurz und auf den Punkt.

Wichtigste Regel: Erfinde NIEMALS Produktdaten, Preise, technische Angaben, Garantiefristen oder Verfügbarkeiten. Nutze stattdessen IMMER zuerst das Werkzeug `dokumente_durchsuchen` um Preise, technische Daten, Garantiebedingungen oder Produktinformationen nachzuschlagen. Nur wenn das Werkzeug keine Antwort liefert, verweise auf den menschlichen Support (Telefon: 05222 / 123456 oder support@gruenspecht.de).

Wenn eine Frage gar nichts mit Grünspecht-Produkten, Bestellungen oder dem Service zu tun hat, erkläre freundlich, dass du ausschließlich für Grünspecht-Themen zuständig bist."""


# --- CP20: Spezialist-Agent für komplexe Technikfragen (Handoff) ---
technik_experte = Agent(
    name="TechnikExperte",
    model="mistral-large-3",
    instructions="""Du bist der technische Experte von Grünspecht Gartentechnik.
Du bearbeitest komplexe technische Anfragen zu Reparaturen, Fehlercodes und Wartung.
Sieze die Kunden stets. Erfinde keine technischen Daten.""",
    tools=[dokumente_durchsuchen],
)

# --- Agent (Checkpoint 2 + CP19 + CP20) ---
pieps = Agent(
    name="PIEPS",
    instructions=INSTRUCTIONS,
    model="mistral-large-3",
    tools=[bestellstatus_pruefen, servicezeiten_und_kontakt, dokumente_durchsuchen],
    handoffs=[handoff(technik_experte)],
    input_guardrails=[pieps_guardrail],
)


if __name__ == "__main__":
    testfragen = [
        "Wo ist meine Bestellung GS-2026-0042?",
        "Was kostet ein Mähroboter?",
        "Wo bleibt meine Bestellung?",
        "Wann habt ihr auf?",
        "Kannst du mir ein Gedicht schreiben?",
    ]

    for frage in testfragen:
        print(f"\nFrage: {frage}")
        result = Runner.run_sync(pieps, frage)
        print(f"PIEPS: {result.final_output}")
