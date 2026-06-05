import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

load_dotenv()

INDEX_NAME      = os.getenv("PINECONE_INDEX", "pm-knowledge")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_pinecone_index():
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return pc.Index(INDEX_NAME)


def retrieve(
    query: str,
    n_results: int = 4,
    category: str = None
) -> str:
    """
    Searches Pinecone for chunks relevant to the query.
    Returns formatted context string.
    """
    try:
        model = get_model()
        index = get_pinecone_index()

        # Check index has content
        stats = index.describe_index_stats()
        if stats["total_vector_count"] == 0:
            return ""

        query_embedding = model.encode([query]).tolist()[0]

        # Build category filter
        filter_dict = {"category": {"$eq": category}} if category else None

        results = index.query(
            vector          = query_embedding,
            top_k           = n_results,
            include_metadata= True,
            filter          = filter_dict
        )

        if not results["matches"]:
            return ""

        # Format into readable context block
        context_parts = []
        for match in results["matches"]:
            meta       = match["metadata"]
            relevance  = round(match["score"] * 100, 1)
            text       = meta.get("text", "")
            source     = meta.get("source", "unknown")
            cat        = meta.get("category", "unknown")

            context_parts.append(
                f"[Source: {source} | Category: {cat} | "
                f"Relevance: {relevance}%]\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        print(f"[RAG retrieval error: {e}]")
        return ""


def retrieve_for_agents(user_feedback: str) -> dict:
    """
    Runs targeted searches for each agent.
    Returns a dict of context strings.
    """
    return {
        "jtbd": retrieve(
            query    = f"user jobs motivations goals: {user_feedback}",
            category = "interviews"
        ),
        "persona": retrieve(
            query    = f"user demographics behaviors profile: {user_feedback}",
            category = "interviews"
        ),
        "pain_points": retrieve(
            query     = f"user pain problems frustrations: {user_feedback}",
            n_results = 5
        ),
        "opportunities": retrieve(
            query    = f"market gaps product opportunities solutions: {user_feedback}",
            category = "research"
        ),
        "prd": retrieve(
            query    = f"product requirements features specifications: {user_feedback}",
            category = "research"
        )
    }