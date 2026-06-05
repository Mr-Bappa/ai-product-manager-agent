import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX", "pm-knowledge")


def get_pinecone_client():
    return Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


def embed_query(pc: Pinecone, query: str) -> list:
    """
    Embeds a search query using Pinecone hosted model.
    input_type 'query' is different from 'passage' used during storage.
    """
    response = pc.inference.embed(
        model      = "multilingual-e5-large",
        inputs     = [query],
        parameters = {"input_type": "query"}
    )
    return response[0]["values"]


def retrieve(
    query: str,
    n_results: int = 4,
    category: str = None
) -> str:
    try:
        pc    = get_pinecone_client()
        index = pc.Index(INDEX_NAME)

        stats = index.describe_index_stats()
        if stats["total_vector_count"] == 0:
            return ""

        query_embedding = embed_query(pc, query)

        filter_dict = {"category": {"$eq": category}} if category else None

        results = index.query(
            vector           = query_embedding,
            top_k            = n_results,
            include_metadata = True,
            filter           = filter_dict
        )

        if not results["matches"]:
            return ""

        context_parts = []
        for match in results["matches"]:
            meta      = match["metadata"]
            relevance = round(match["score"] * 100, 1)
            text      = meta.get("text", "")
            source    = meta.get("source", "unknown")
            cat       = meta.get("category", "unknown")

            context_parts.append(
                f"[Source: {source} | Category: {cat} | "
                f"Relevance: {relevance}%]\n{text}"
            )

        return "\n\n---\n\n".join(context_parts)

    except Exception as e:
        print(f"[RAG retrieval error: {e}]")
        return ""


def retrieve_for_agents(user_feedback: str) -> dict:
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