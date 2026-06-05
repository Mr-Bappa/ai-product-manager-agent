import os
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
INDEX_NAME      = os.getenv("PINECONE_INDEX", "pm-knowledge")

# Dimension of all-MiniLM-L6-v2 output — always 384
EMBEDDING_DIM   = 384

_model = None

def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_pinecone_index():
    """
    Connects to Pinecone and returns the index.
    Creates the index if it does not exist yet.
    """
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    existing_indexes = [i.name for i in pc.list_indexes()]

    if INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index: {INDEX_NAME}")
        pc.create_index(
            name      = INDEX_NAME,
            dimension = EMBEDDING_DIM,
            metric    = "cosine",
            spec      = ServerlessSpec(
                cloud  = "aws",
                region = "us-east-1"     # change if your account uses a different region
            )
        )
        print(f"[✓ Index created: {INDEX_NAME}]")
    else:
        print(f"[✓ Index found: {INDEX_NAME}]")

    return pc.Index(INDEX_NAME)


def embed_and_store(documents: list):
    """
    Takes list of document dicts from loader.py.
    Embeds each chunk and stores in Pinecone.
    """
    if not documents:
        print("[No documents to embed]")
        return

    model = get_model()
    index = get_pinecone_index()

    texts     = [doc["text"]     for doc in documents]
    ids       = [doc["chunk_id"] for doc in documents]
    metadatas = [
        {
            "source":   doc["source"],
            "category": doc["category"],
            "text":     doc["text"]      # store text in metadata for retrieval
        }
        for doc in documents
    ]

    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # Pinecone expects: list of (id, vector, metadata)
    vectors = [
        (ids[i], embeddings[i], metadatas[i])
        for i in range(len(texts))
    ]

    # Upload in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
        print(f"Uploaded batch {i//batch_size + 1} of {(len(vectors)-1)//batch_size + 1}")

    print(f"\n[✓ {len(texts)} chunks stored in Pinecone]")


def get_index_stats():
    """Shows how many vectors are stored."""
    index = get_pinecone_index()
    stats = index.describe_index_stats()
    count = stats["total_vector_count"]
    print(f"[Pinecone has {count} vectors stored]")
    return count