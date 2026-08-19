"""
CP16-18: RAG-Suche - Frage -> Embedding -> Supabase -> relevante Chunks.
CP26 Fix: Embeddings via EUrouter statt lokalem Ollama (laeuft nicht auf Server).
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client

load_dotenv()

_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)

_openai = OpenAI(
    api_key=os.getenv("EUROUTER_API_KEY"),
    base_url="https://api.eurouter.ai/api/v1",
)

EMBED_MODEL = "bge-m3"
TOP_K = 3


def suche_dokumente(frage: str) -> str:
    """Sucht die relevantesten Dokument-Chunks zur gestellten Frage.

    Erzeugt ein Embedding der Frage und findet per Kosinus-Aehnlichkeit
    die passendsten Abschnitte aus den Gruenspecht-Dokumenten.

    Args:
        frage: Die Kundenanfrage als Freitext.

    Returns:
        Die relevantesten Textabschnitte als zusammengefuehrter String.
    """
    response = _openai.embeddings.create(
        model=EMBED_MODEL,
        input=frage,
    )
    embedding = response.data[0].embedding

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
