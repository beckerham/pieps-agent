"""
CP27: Persistente Session in Supabase statt SQLite.
Speichert den Gespraechsverlauf pro chat_id in der Tabelle 'sessions'.
"""
import os
from dotenv import load_dotenv
from supabase import create_client
from agents.memory import BaseSession

load_dotenv()

_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


class SupabaseSession(BaseSession):
    def __init__(self, session_id: str):
        self.session_id = session_id

    async def get_items(self):
        result = (
            _supabase.table("sessions")
            .select("role, content")
            .eq("session_id", self.session_id)
            .order("idx")
            .execute()
        )
        return [{"role": r["role"], "content": r["content"]} for r in result.data]

    async def add_items(self, items):
        existing = (
            _supabase.table("sessions")
            .select("idx")
            .eq("session_id", self.session_id)
            .order("idx", desc=True)
            .limit(1)
            .execute()
        )
        next_idx = (existing.data[0]["idx"] + 1) if existing.data else 0

        rows = [
            {
                "session_id": self.session_id,
                "idx": next_idx + i,
                "role": item["role"],
                "content": item["content"] if isinstance(item["content"], str) else str(item["content"]),
            }
            for i, item in enumerate(items)
        ]
        if rows:
            _supabase.table("sessions").insert(rows).execute()
