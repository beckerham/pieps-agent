"""
CP10–12: Dokumente einlesen, aufteilen, Embeddings erzeugen.
Ergebnis wird in chunks.json gespeichert (Zwischenschritt vor Supabase/CP13).

OCR für Scan-PDFs: Mistral OCR (mistral-ocr-latest).
"""
import os
import json
import base64
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import ollama

load_dotenv()

DOCS_DIR = Path("gruenspecht_dokumente")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBED_MODEL = "bge-m3"
OUTPUT_FILE = "chunks.json"


# --- CP10: PDF einlesen ---

def ist_scan_pdf(pfad: Path) -> bool:
    reader = PdfReader(str(pfad))
    text = "".join(p.extract_text() or "" for p in reader.pages)
    return len(text.strip()) < 50


def lese_pdf_mit_pypdf(pfad: Path) -> str:
    reader = PdfReader(str(pfad))
    return "\n".join(p.extract_text() or "" for p in reader.pages)


def lese_pdf_mit_mistral_ocr(pfad: Path) -> str:
    from mistralai.client import Mistral

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY fehlt in der .env-Datei.")

    client = Mistral(api_key=api_key)

    with open(pfad, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.ocr.process(
        model="mistral-ocr-latest",
        document={
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{pdf_data}",
        },
    )

    return "\n\n".join(page.markdown for page in response.pages)


def lade_dokument(pfad: Path) -> str:
    if ist_scan_pdf(pfad):
        print(f"  → Mistral OCR: {pfad.name}")
        return lese_pdf_mit_mistral_ocr(pfad)
    else:
        print(f"  → pypdf:       {pfad.name}")
        return lese_pdf_mit_pypdf(pfad)


# --- CP11: Text aufteilen ---

def teile_in_chunks(text: str, quelle: str) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    teile = splitter.split_text(text)
    return [{"text": t, "quelle": quelle} for t in teile if t.strip()]


# --- CP12: Embeddings erzeugen ---

def erstelle_embedding(text: str) -> list[float]:
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]


# --- Hauptprogramm ---

def main():
    pdf_dateien = sorted(DOCS_DIR.glob("*.pdf"))
    print(f"{len(pdf_dateien)} PDFs gefunden.\n")

    alle_chunks = []

    for pfad in pdf_dateien:
        print(f"Lese: {pfad.name}")
        text = lade_dokument(pfad)
        chunks = teile_in_chunks(text, pfad.name)
        print(f"  → {len(chunks)} Chunks")
        alle_chunks.extend(chunks)

    print(f"\n{len(alle_chunks)} Chunks insgesamt. Erstelle Embeddings …")

    for i, chunk in enumerate(alle_chunks):
        chunk["embedding"] = erstelle_embedding(chunk["text"])
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(alle_chunks)} fertig")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(alle_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nFertig. {len(alle_chunks)} Chunks gespeichert in '{OUTPUT_FILE}'.")
    print(f"Embedding-Dimension: {len(alle_chunks[0]['embedding'])}")


if __name__ == "__main__":
    main()
