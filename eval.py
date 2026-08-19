"""
CP29: Evals - messen statt raten.
CP30: Token-Verbrauch erfassen und Kosten hochrechnen.

Aufruf: python eval.py
Laeuft direkt gegen den PIEPS-Agenten, nicht ueber Telegram.
Jede Frage bekommt eine eigene Session (kein Gedaechtnis zwischen Fragen).
"""
import asyncio
import json
import os
import time
from dotenv import load_dotenv
from agents import Runner, InputGuardrailTripwireTriggered
from pieps import pieps

load_dotenv()

# CP30: Preise in EUR je 1 Million Tokens (Datum: 2026-08-19, Quelle: EUrouter)
# Aktuell pruefen unter: https://eurouter.ai/pricing
PREIS_INPUT_PRO_MILLION = 0.40
PREIS_OUTPUT_PRO_MILLION = 1.20
ANFRAGEN_PRO_TAG = 200


async def frage_stellen(frage: str, erwartet: str) -> dict:
    start = time.time()
    try:
        result = await Runner.run(pieps, frage)
        dauer = round(time.time() - start, 2)
        antwort = result.final_output or ""

        tokens_rein = sum(
            r.usage.input_tokens for r in result.raw_responses if getattr(r, "usage", None)
        )
        tokens_raus = sum(
            r.usage.output_tokens for r in result.raw_responses if getattr(r, "usage", None)
        )

        if erwartet == "ABGELEHNT":
            bestanden = False
        else:
            bestanden = erwartet.lower() in antwort.lower()

        return {
            "bestanden": bestanden,
            "antwort_kurz": antwort[:80],
            "dauer": dauer,
            "tokens_rein": tokens_rein,
            "tokens_raus": tokens_raus,
            "guardrail": False,
        }

    except InputGuardrailTripwireTriggered:
        dauer = round(time.time() - start, 2)
        return {
            "bestanden": erwartet == "ABGELEHNT",
            "antwort_kurz": "[GUARDRAIL AUSGELÖST]",
            "dauer": dauer,
            "tokens_rein": 0,
            "tokens_raus": 0,
            "guardrail": True,
        }
    except Exception as e:
        dauer = round(time.time() - start, 2)
        return {
            "bestanden": False,
            "antwort_kurz": f"[FEHLER: {type(e).__name__}: {str(e)[:60]}]",
            "dauer": dauer,
            "tokens_rein": 0,
            "tokens_raus": 0,
            "guardrail": False,
        }


async def main():
    with open("eval_questions.json", encoding="utf-8") as f:
        fragen = json.load(f)

    print(f"PIEPS Eval — {len(fragen)} Fragen\n")
    ergebnisse = []

    for q in fragen:
        vorschau = q["frage"][:55].ljust(55)
        print(f"  #{q['id']:2d} {vorschau} ", end="", flush=True)
        e = await frage_stellen(q["frage"], q["erwartet"])
        ergebnisse.append({**q, **e})
        status = "OK  " if e["bestanden"] else "FEHL"
        print(f"[{status}] {e['dauer']}s")

    # --- Auswertung CP29 ---
    gesamt = len(ergebnisse)
    bestanden = sum(1 for e in ergebnisse if e["bestanden"])
    quote = bestanden / gesamt * 100

    print(f"\n{'─'*60}")
    print(f"Trefferquote: {bestanden}/{gesamt} ({quote:.0f}%)")

    fehlschlaege = [e for e in ergebnisse if not e["bestanden"]]
    if fehlschlaege:
        print("\nFehlschlaege:")
        for e in fehlschlaege:
            print(f"  #{e['id']} [{e['sorte']}] Erwartet: '{e['erwartet']}'")
            print(f"       Antwort: {e['antwort_kurz']}")

    # --- Auswertung CP30 ---
    messungen = [e for e in ergebnisse if e["tokens_rein"] > 0]
    if messungen:
        avg_rein = sum(e["tokens_rein"] for e in messungen) / len(messungen)
        avg_raus = sum(e["tokens_raus"] for e in messungen) / len(messungen)

        kosten_je = (avg_rein * PREIS_INPUT_PRO_MILLION + avg_raus * PREIS_OUTPUT_PRO_MILLION) / 1_000_000
        kosten_tag = kosten_je * ANFRAGEN_PRO_TAG
        kosten_monat = kosten_tag * 30

        print(f"\n{'─'*60}")
        print(f"Token-Verbrauch (Ø aus {len(messungen)} Messungen):")
        print(f"  Input:  {avg_rein:.0f} Tokens")
        print(f"  Output: {avg_raus:.0f} Tokens")
        print(f"\nKosten je Anfrage:     {kosten_je * 100:.3f} Cent")
        print(f"Hochrechnung {ANFRAGEN_PRO_TAG} Anf./Tag: {kosten_tag:.2f} EUR/Tag")
        print(f"                       {kosten_monat:.2f} EUR/Monat (ohne Cache)")
        print(f"\n⚠  Preise gueltig: 2026-08-19 — vor Entscheidungen aktuell pruefen.")
    else:
        print("\nToken-Verbrauch: keine Daten (usage nicht verfuegbar)")


if __name__ == "__main__":
    asyncio.run(main())
