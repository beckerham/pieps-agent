"""
CP16–18: RAG-Suche — Frage → Embedding → Supabase → relevante Chunks.
"""
import os
from dotenv import load_dotenv
import ollama
from supabase import create_client

load_dotenv()

_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)

EMBED_MODEL = "bge-m3"
TOP_K = 3


def suche_dokumente(frage: str) -> str:
    """Sucht die relevantesten Dokument-Chunks zur gestellten Frage.

    Erzeugt ein Embedding der Frage und findet per Kosinus-Ähnlichkeit
    die passendsten Abschnitte aus den Grünspecht-Dokumenten.

    Args:
        frage: Die Kundenanfrage als Freitext.

    Returns:
        Die relevantesten Textabschnitte als zusammengeführter String.
    """
    embedding = ollama.embeddings(model=EMBED_MODEL, prompt=frage)["embedding"]

    result = _supabase.rpc(
        "match_dokumente",
        {
            "query_embedding": embedding,
            "match_count": TOP_K,
        },
    ).execute()

    if not result.data:
        return "Keine relevanten Dokumente gefunden."

    teile = [f"[{r['quelle']}]\n{r['text']}" for r in result.data]
    return "\n\n---\n\n".join(teile)
