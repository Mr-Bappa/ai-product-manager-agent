import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

INDEX_NAME    = os.getenv("PINECONE_INDEX", "pm-knowledge")
EMBEDDING_DIM = 1024  # multilingual-e5-large dimension


def get_pinecone_client():
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def get_pinecone_index():
    pc = get_pinecone_client()
    existing_indexes = [i.name for i in pc.list_indexes()]

    if INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index: {INDEX_NAME}")
        pc.create_index(
            name      = INDEX_NAME,
            dimension = EMBEDDING_DIM,
            metric    = "cosine",
            spec      = ServerlessSpec(
                cloud  = "aws",
                region = "us-east-1"
            )
        )
        print(f"[✓ Index created: {INDEX_NAME}]")
    else:
        print(f"[✓ Index found: {INDEX_NAME}]")

    return pc.Index(INDEX_NAME)


def embed_text(pc: Pinecone, texts: list) -> list:
    """
    Uses Pinecone hosted embedding model.
    No local model download needed — works on any server.
    """
    response = pc.inference.embed(
        model      = "multilingual-e5-large",
        inputs     = texts,
        parameters = {"input_type": "passage"}
    )
    return [item["values"] for item in response]


def embed_and_store(documents: list):
    if not documents:
        print("[No documents to embed]")
        return

    pc    = get_pinecone_client()
    index = get_pinecone_index()

    texts     = [doc["text"]     for doc in documents]
    ids       = [doc["chunk_id"] for doc in documents]
    metadatas = [
        {
            "source":   doc["source"],
            "category": doc["category"],
            "text":     doc["text"]
        }
        for doc in documents
    ]

    # Pinecone inference allows max 96 inputs per call
    batch_size  = 50
    all_vectors = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        batch_ids   = ids[i:i+batch_size]
        batch_meta  = metadatas[i:i+batch_size]

        print(f"Embedding batch {i//batch_size + 1} of {-(-len(texts)//batch_size)}...")
        embeddings = embed_text(pc, batch_texts)

        for j in range(len(batch_texts)):
            all_vectors.append((
                batch_ids[j],
                embeddings[j],
                batch_meta[j]
            ))

    # Upload to Pinecone in batches of 100
    for i in range(0, len(all_vectors), 100):
        index.upsert(vectors=all_vectors[i:i+100])
        print(f"Uploaded batch {i//100 + 1} of {-(-len(all_vectors)//100)}")

    print(f"\n[✓ {len(all_vectors)} chunks stored in Pinecone]")


def get_index_stats():
    index = get_pinecone_index()
    stats = index.describe_index_stats()
    count = stats["total_vector_count"]
    print(f"[Pinecone has {count} vectors stored]")
    return count