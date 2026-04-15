import asyncio
import os
from core import database as db

async def main():
    print(f"Checking DB: {os.path.abspath(db.DB_PATH)}")
    await db.init_db()
    
    # Check if tables exist
    import aiosqlite
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
            tables = [row[0] for row in await cursor.fetchall()]
            print(f"Tables found: {tables}")

if __name__ == "__main__":
    asyncio.run(main())
