"""
CP27: Persistente Session in Supabase statt SQLite.
Speichert den Gespraechsverlauf pro chat_id in der Tabelle 'sessions'.
"""
import json
import os
from dotenv import load_dotenv
from agents.memory import SessionABC, SessionSettings
from supabase import create_client

load_dotenv()

_supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)


class SupabaseSession(SessionABC):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_settings = SessionSettings()

    async def get_items(self, limit=None):
        result = (
            _supabase.table("sessions")
            .select("message_data")
            .eq("session_id", self.session_id)
            .order("id")
            .execute()
        )
        items = []
        for r in result.data:
            try:
                items.append(json.loads(r["message_data"]))
            except Exception:
                pass
        if limit:
            return items[-limit:]
        return items

    async def add_items(self, items):
        rows = [
            {
                "session_id": self.session_id,
                "message_data": json.dumps(item),
            }
            for item in items
        ]
        if rows:
            _supabase.table("sessions").insert(rows).execute()

    async def pop_item(self):
        result = (
            _supabase.table("sessions")
            .select("id, message_data")
            .eq("session_id", self.session_id)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        _supabase.table("sessions").delete().eq("id", row["id"]).execute()
        try:
            return json.loads(row["message_data"])
        except Exception:
            return None

    async def clear_session(self):
        _supabase.table("sessions").delete().eq("session_id", self.session_id).execute()
