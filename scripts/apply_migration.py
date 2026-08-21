import asyncio
import sys
import os
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import app.database.connection as db_conn

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")

async def main():
    print("Applying migrations...")
    await db_conn.init_db_pool()
    try:
        migration_files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, "*.sql")))
        async with db_conn._pool.acquire() as conn:
            for migration_file in migration_files:
                filename = os.path.basename(migration_file)
                print(f"  Applying {filename}...")
                with open(migration_file, "r") as f:
                    sql = f.read()
                await conn.execute(sql)
                print(f"  [OK] {filename} applied.")
        print("All migrations applied successfully.")
    finally:
        await db_conn.close_db_pool()

if __name__ == "__main__":
    asyncio.run(main())

