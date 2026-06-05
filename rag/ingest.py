from rag.loader import load_all_documents
from rag.embedder import embed_and_store, get_index_stats


def ingest():
    print("=" * 50)
    print("  RAG Ingestion Pipeline — Pinecone")
    print("  Reading knowledge_base/ folder...")
    print("=" * 50 + "\n")

    documents = load_all_documents("knowledge_base")

    if not documents:
        print("\n[No documents found]")
        print("Add .txt, .pdf, or .docx files to:")
        print("  knowledge_base/interviews/")
        print("  knowledge_base/research/")
        print("  knowledge_base/competitors/")
        return

    embed_and_store(documents)
    get_index_stats()
    print("\n[✓ Knowledge base ready in Pinecone]")


if __name__ == "__main__":
    ingest()