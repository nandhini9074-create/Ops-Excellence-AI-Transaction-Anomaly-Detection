import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database.connection import init_db_pool, close_db_pool
from backend.app.scheduler import run_baseline_builder

async def main():
    print("Running Baseline Builder...")
    await init_db_pool()
    try:
        await run_baseline_builder()
        print("Baseline Builder complete.")
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(main())
