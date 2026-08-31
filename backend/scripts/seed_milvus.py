import asyncio
import sys
from pathlib import Path

# Permet l'exécution directe avec `python scripts/seed_milvus.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.services.vector_store import VectorStoreService


async def main() -> None:
    count = await VectorStoreService(get_settings()).seed()
    print(f"{count} chunks indexés dans Milvus.")


if __name__ == "__main__":
    asyncio.run(main())
