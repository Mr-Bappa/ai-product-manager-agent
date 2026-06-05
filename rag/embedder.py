import chromadb
from sentence_transformers import SentenceTransformer

# This model runs locally — no API call needed
# Downloads once (~90MB), then cached on your machine
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Where ChromaDB stores its files
CHROMA_PATH = "chroma_db"


def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)


def get_or_create_collection(client, collection_name: str = "pm_knowledge"):
    """
    Gets existing collection or creates a new one.
    A collection is like a table in a regular database.
    """
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # cosine = best for text similarity
    )


def embed_and_store(documents: list, collection_name: str = "pm_knowledge"):
    """
    Takes list of document dicts from loader.py.
    Converts each chunk to a vector.
    Stores vectors + original text in ChromaDB.
    """
    if not documents:
        print("[No documents to embed]")
        return

    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    client = get_chroma_client()
    collection = get_or_create_collection(client, collection_name)

    # Prepare data for ChromaDB
    texts     = [doc["text"]     for doc in documents]
    ids       = [doc["chunk_id"] for doc in documents]
    metadatas = [
        {
            "source":   doc["source"],
            "category": doc["category"]
        }
        for doc in documents
    ]

    print(f"Embedding {len(texts)} chunks... (this takes a minute first time)")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # Store in batches of 100 to avoid memory issues
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            documents=texts[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )
        print(f"Stored batch {i//batch_size + 1}")

    print(f"\n[✓ {len(texts)} chunks embedded and stored in ChromaDB]")


def get_collection_stats():
    """Shows how many chunks are stored."""
    client = get_chroma_client()
    collection = get_or_create_collection(client)
    count = collection.count()
    print(f"[ChromaDB has {count} chunks stored]")
    return count