import logging
import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

from .config import config

_COLLECTION_NAME = 'apps'


def build_chroma_client(db_name: str) -> ClientAPI:
    """Create a persistent Chroma client scoped to the given database name."""
    path = config.CHROMA_DIR / db_name
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(path),
        settings=Settings(anonymized_telemetry=False, allow_reset=False),
    )


def get_app_collection(client: ClientAPI) -> Collection:
    """Return the cosine-similarity collection used for app embeddings."""
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={'hnsw:space': 'cosine'},
    )
