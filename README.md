# DocIQ — RAG Document Intelligence

Upload any document. Ask any question. Get cited answers in seconds.

DocIQ is a production-ready document intelligence API and application built on a 
Retrieval-Augmented Generation (RAG) pipeline. It lets businesses extract precise, 
sourced answers from their documents without hallucination — powered by semantic 
search, not keyword matching.

---

## What It Does

Most AI tools summarize your documents and hope for the best. DocIQ retrieves the 
exact relevant sections first, then answers strictly from that evidence — citing 
which document and passage the answer came from.

**Upload a contract** → ask "what are the termination clauses?" → get the exact answer with the source paragraph

**Upload 50 customer reviews** → ask "what are the most common complaints?" → get a synthesized answer across all documents

**Upload a research report** → ask "what does this say about Q3 revenue?" → get a precise answer, not a summary

---

## Technical Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Vector Database | PostgreSQL + pgvector |
| Vector Index | HNSW (cosine similarity) |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | GPT-3.5-turbo |
| PDF Extraction | PyMuPDF |
| Frontend | Streamlit |
| ORM | SQLAlchemy |

---

## Architecture
Document Upload
↓
Text Extraction (PDF / TXT)
↓
Sentence-Aware Chunking with Overlap
↓
Batch Embedding (OpenAI)
↓
pgvector Storage with HNSW Index
↓
Query → Embed → Semantic Search → Retrieve Top 5 Chunks
↓
GPT answers strictly from retrieved context
↓
Cited answer with similarity scores

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /index | Chunk, embed and index a document |
| POST | /query | Ask a question, get a cited answer |
| POST | /analyze-ai | Full AI analysis — summary, sentiment, insights |
| POST | /upload | NLP analysis — keywords, reading level, stats |
| GET | /history | Last 10 analyses |
| GET | /history/{id} | Full analysis by ID |
| DELETE | /documents/{filename} | Remove document from index |

---

## Key Engineering Decisions

**Sentence-aware chunking** — documents are split at sentence boundaries with 
overlap, never mid-sentence. This preserves meaning at chunk boundaries and 
improves retrieval accuracy.

**Batch embeddings** — chunks are embedded 50 at a time instead of sequentially, 
reducing indexing time by ~45x on large documents.

**HNSW vector index** — approximate nearest neighbor search scales to millions of 
chunks without performance degradation.

**Similarity threshold filtering** — chunks below 0.15 cosine similarity are 
filtered before reaching the LLM, preventing irrelevant context from corrupting 
answers.

**Upsert deduplication** — re-indexing the same document updates existing records 
instead of creating duplicates.

**No LangChain** — the entire pipeline is built from scratch. Every component is 
understood, controlled, and optimizable.

---

## What This Enables

- Enterprise document search that understands meaning, not just keywords
- Compliance and legal document Q&A with cited sources
- Customer feedback analysis across thousands of documents
- Internal knowledge base that answers employee questions from company docs
- Research assistant that synthesizes findings across multiple papers

---

## Built By

Data engineer specializing in AI infrastructure. Available for freelance projects 
involving RAG pipelines, vector databases, document intelligence, and AI-powered 
data systems.

Contact: info.eyilmaz@gmail.com