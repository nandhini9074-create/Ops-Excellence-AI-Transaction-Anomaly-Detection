import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from app.database.connection import init_db_pool, close_db_pool
from app.scheduler import run_anomaly_detection

async def main():
    print("Running Anomaly Detection Engine...")
    await init_db_pool()
    try:
        await run_anomaly_detection()
        print("Anomaly Detection Engine complete.")
    finally:
        await close_db_pool()

if __name__ == "__main__":
    asyncio.run(main())
