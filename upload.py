"""
CP14: Chunks aus chunks.json in Supabase hochladen.
"""
import json
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY"),
)

with open("chunks.json", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"{len(chunks)} Chunks werden hochgeladen …")

BATCH = 10
for i in range(0, len(chunks), BATCH):
    batch = chunks[i : i + BATCH]
    client.table("dokumente").insert(batch).execute()
    print(f"  {min(i + BATCH, len(chunks))}/{len(chunks)} hochgeladen")

print("Fertig.")
