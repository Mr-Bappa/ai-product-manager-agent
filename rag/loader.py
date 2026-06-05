import os
import glob
from pypdf import PdfReader
from docx import Document


def load_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_pdf_file(path: str) -> str:
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def load_docx_file(path: str) -> str:
    doc = Document(path)
    return "\n".join([para.text for para in doc.paragraphs])


def load_document(path: str) -> str:
    """
    Detects file type and loads it.
    Supports .txt, .pdf, .docx, .md
    """
    ext = os.path.splitext(path)[1].lower()

    if ext in [".txt", ".md"]:
        return load_text_file(path)
    elif ext == ".pdf":
        return load_pdf_file(path)
    elif ext == ".docx":
        return load_docx_file(path)
    else:
        print(f"[Skipping unsupported file: {path}]")
        return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """
    Splits text into overlapping chunks.

    chunk_size: characters per chunk
    overlap: characters shared between consecutive chunks
              (so context doesn't get cut off at boundaries)

    Example with chunk_size=20, overlap=5:
    "Hello world this is a test"
     chunk 1: "Hello world this is a"
     chunk 2: "is a test"          ← starts 5 chars before chunk 1 ended
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap  # move forward but keep overlap

    return chunks


def load_all_documents(knowledge_base_path: str = "knowledge_base") -> list:
    """
    Walks through all subfolders in knowledge_base/.
    Loads every supported document.
    Returns list of dicts with text, source, and category.
    """
    documents = []

    # Find all supported files recursively
    patterns = ["**/*.txt", "**/*.pdf", "**/*.docx", "**/*.md"]

    for pattern in patterns:
        files = glob.glob(
            os.path.join(knowledge_base_path, pattern),
            recursive=True
        )

        for file_path in files:
            print(f"Loading: {file_path}")
            text = load_document(file_path)

            if not text.strip():
                continue

            # Get category from subfolder name
            # e.g. knowledge_base/interviews/file.txt → category = "interviews"
            relative = os.path.relpath(file_path, knowledge_base_path)
            category = relative.split(os.sep)[0]

            # Split into chunks
            chunks = chunk_text(text)

            for i, chunk in enumerate(chunks):
                documents.append({
                    "text": chunk,
                    "source": file_path,
                    "category": category,
                    "chunk_id": f"{file_path}__chunk_{i}"
                })

    print(f"\n[Loaded {len(documents)} chunks from {knowledge_base_path}]")
    return documents