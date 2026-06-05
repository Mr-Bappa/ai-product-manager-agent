import chromadb
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_PATH     = "chroma_db"

# Load model once at module level — avoids reloading on every search
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def retrieve(
    query: str,
    n_results: int = 4,
    category: str = None,
    collection_name: str = "pm_knowledge"
) -> str:
    """
    Takes a search query (plain text).
    Returns the most relevant chunks as a single formatted string.

    n_results: how many chunks to return
    category: optional filter — "interviews", "research", "competitors"
    """

    client     = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(collection_name)

    if collection.count() == 0:
        return ""

    model      = get_model()
    query_embedding = model.encode([query]).tolist()

    # Build optional category filter
    where_filter = {"category": category} if category else None

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    if not results["documents"][0]:
        return ""

    # Format results into readable context block
    context_parts = []
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        relevance = round((1 - dist) * 100, 1)  # convert distance to % similarity
        context_parts.append(
            f"[Source: {meta['source']} | Category: {meta['category']} | "
            f"Relevance: {relevance}%]\n{doc}"
        )

    return "\n\n---\n\n".join(context_parts)


def retrieve_for_agents(user_feedback: str) -> dict:
    return {
        "jtbd": retrieve(
            query=f"user jobs motivations goals: {user_feedback}",
            category="interviews"
        ),
        "persona": retrieve(
            query=f"user demographics behaviors profile: {user_feedback}",
            category="interviews"
        ),
        "pain_points": retrieve(
            query=f"user pain problems frustrations: {user_feedback}",
            n_results=5
        ),
        "opportunities": retrieve(
            query=f"market gaps product opportunities solutions: {user_feedback}",
            category="research"
        ),
        "prd": retrieve(                                     # ← new
            query=f"product requirements features specifications: {user_feedback}",
            category="research"
        )
    }