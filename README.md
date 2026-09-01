🧠 AI Product Manager

Turn raw customer feedback into prioritized product opportunities and an engineering-ready PRD.






AI Product Manager is a multi-agent product discovery copilot that converts unstructured customer feedback—such as interview transcripts, survey responses, and support tickets—into a complete product strategy. A five-agent pipeline identifies jobs to be done, builds a persona, extracts pain points, prioritizes opportunities with RICE, and produces a structured Product Requirements Document (PRD).

✨ What it delivers

Five-stage PM workflow: JTBD → Persona → Pain Points → RICE Scoring → PRD

Evidence-aware analysis: optional Pinecone RAG enrichment from product research and interview documents

Structured prioritization: transparent Reach, Impact, Confidence, and Effort scoring

Engineering-ready PRD: problem statement, goals, success metrics, user stories, MVP scope, risks, assumptions, and open questions

Contextual follow-up chat: generate sprint plans, investor pitches, validation questions, rewrites, and next steps from the completed report

Portable outputs: download the complete analysis as TXT or a formatted DOCX document

Interactive UI: live agent progress, generated-word count, output cards, and session-based conversation history

🚀 Live application

Try the deployed product: ai-pm-agent.streamlit.app

Paste customer feedback, run the pipeline, review each agent's output, download the PRD, and continue the analysis through the report-aware chat interface.

🏗️ Architecture

flowchart TD
    A["Customer feedback"] --> B["Optional RAG retrieval"]
    B --> C["1 · JTBD agent"]
    C --> D["2 · Persona agent"]
    D --> E["3 · Pain-point agent"]
    E --> F["4 · RICE scorer"]
    F --> G["5 · PRD writer"]
    G --> H["Report chat"]
    G --> I["TXT / DOCX export"]

The agents run sequentially so every stage inherits the structured output of the previous stage. The optional RAG path creates five task-specific retrieval queries and supplies relevant context to the corresponding agents when the CLI orchestrator is used.

🤖 Agent responsibilities

Agent

Responsibility

Primary output

JTBD Agent

Extracts functional, emotional, and social jobs from feedback

Job statement, motivations, desired outcomes

Persona Agent

Synthesizes behavioral and contextual user traits

Actionable user persona

Pain-Point Agent

Identifies problems, severity, frequency, and patterns

Prioritized pain-point analysis

Opportunity Scorer

Applies the RICE framework

Ranked opportunities and build recommendation

PRD Writer

Synthesizes all upstream analysis

Engineering-ready PRD

Report Chat

Answers follow-up questions using the generated report

Sprint plans, pitches, rewrites, and next steps

🧰 Technology stack

Layer

Technology

Frontend

Streamlit, custom CSS, session state

Language

Python

LLM inference

Groq API with llama-3.3-70b-versatile

API client

OpenAI-compatible Python SDK

Vector database

Pinecone Serverless

Embeddings

multilingual-e5-large, 1,024 dimensions, cosine similarity

Retrieval

Metadata-filtered semantic search with Top-K context

Document ingestion

PyPDF, python-docx, TXT, and Markdown loaders

Export

python-docx and Streamlit downloads

Deployment

Streamlit Community Cloud

📁 Project structure

ai-pm-agent/
├── agents/
│   ├── jtbd_agent.py
│   ├── persona_agent.py
│   ├── pain_point_agent.py
│   ├── opportunity_scorer_agent.py
│   ├── prd_writer_agent.py
│   └── chat_agent.py
├── rag/
│   ├── loader.py
│   ├── embedder.py
│   ├── retriever.py
│   └── ingest.py
├── utils/
│   └── docx_exporter.py
├── knowledge_base/
│   ├── interviews/
│   ├── competitors/
│   └── research/
├── app.py
├── orchestrator.py
└── requirements.txt

⚙️ Local setup

1. Clone the repository

git clone <your-repository-url>
cd ai-pm-agent

2. Create and activate a virtual environment

python -m venv venv

Windows:

venv\Scripts\activate

macOS/Linux:

source venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Configure environment variables

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=pm-knowledge

Do not commit .env or expose API keys in source control.

5. Run the application

streamlit run app.py

📚 Optional knowledge-base ingestion

Place supported files (.pdf, .docx, .txt, or .md) inside an appropriate knowledge_base/ category, then run:

python -m rag.ingest

The ingestion pipeline:

Recursively loads supported documents.

Splits text into 500-character chunks with 50-character overlap.

Generates 1,024-dimensional passage embeddings.

Upserts vectors and metadata to a Pinecone Serverless index.

Retrieves category-aware context for the PM agents.

To run the RAG-enriched command-line workflow:

python orchestrator.py

Implementation note: the current CLI orchestrator injects retrieved knowledge-base context into the agents. The deployed Streamlit path runs the five-agent workflow directly.

🔄 End-to-end workflow

Add raw customer feedback.

Extract the underlying job, motivation, and desired outcome.

Build an evidence-based target persona.

Identify and rank the most important pain points.

Calculate RICE scores and select the highest-value opportunity.

Generate a structured PRD with measurable success criteria.

Download the report or continue through contextual chat.

🔐 Production considerations

Store API keys in Streamlit Secrets or environment variables.

Add schema validation for agent outputs before downstream hand-offs.

Add retries, timeouts, rate limiting, and graceful error handling for external APIs.

Evaluate retrieval with Recall@K and answer quality with faithfulness and groundedness metrics.

Add tracing for per-agent latency, token usage, failures, and cost.

Introduce prompt-injection defenses before accepting untrusted knowledge-base documents.

🗺️ Roadmap

Connect RAG contexts to the Streamlit execution path

Add structured JSON/Pydantic contracts between agents

Run agents concurrently where dependencies allow

Add automated prompt, retrieval, and PRD-quality evaluations

Add authentication, saved projects, and report version history

Add observability for latency, tokens, cost, and failures

🤝 Contributing

Contributions and suggestions are welcome. Fork the repository, create a focused branch, and open a pull request with a clear description and validation notes.

📄 License

Add a license file before distributing or accepting external contributions. MIT is a common choice for open-source portfolio projects.

Built to turn the voice of the customer into clear product decisions—not another pile of unread feedback.