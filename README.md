# 🔎 RAG Engineering

> **Build a real RAG application from first principles — one component at a time.**

This repository is a hands-on learning project for building a **Retrieval-Augmented Generation (RAG)** application from the ground up.

The goal is not to hide the important concepts behind a framework on day one. We first implement and understand the individual building blocks, test them independently, learn the production alternatives and trade-offs, and only then introduce reusable abstractions/frameworks.

---

## 🎬 Start Here — What Is RAG?

**RAG = Retrieval-Augmented Generation.**

The simple idea is:

> **Don't ask the LLM to remember everything. Find the right information first, then ask the LLM to reason over it.**

A traditional LLM may know broad information from its training, but enterprise applications often need private, changing or domain-specific knowledge. RAG adds retrieval so relevant external information can be supplied to the LLM as context.

```text
User Question
      ↓
   Retrieval 🔎
      ↓
Relevant Context 📚
      ↓
  Augmentation 🧩
      ↓
      LLM 🤖
      ↓
 Grounded Answer 💬
```

### 💡 Why RAG?

RAG helps address practical problems such as:

- 📚 Knowledge that lives outside the model
- 🔄 Frequently changing information
- 🏢 Private/domain-specific enterprise knowledge
- 🧠 Avoiding the need to send an entire knowledge base to an LLM for every question
- 🔍 Source attribution and provenance

RAG does **not** automatically guarantee correctness. Retrieval quality, source quality, parsing, chunking, embeddings, prompting and evaluation still matter.

### 🏢 Real-world example

Imagine an enterprise HR assistant with thousands of policies and benefits documents.

An employee asks:

> **"How many days of parental leave am I eligible for in India?"**

Instead of expecting the LLM to memorize the company's HR library, the RAG system retrieves the relevant India parental-leave sections, supplies them as context and returns an answer with source information.

```text
HR Documents
     ↓
Ingest → Parse → Chunk → Embed → Knowledge Store
                                      ↑
Employee Question → Retrieve → Context → LLM → Answer + Sources
```

See **[`docs/RAG_FUNDAMENTALS.md`](docs/RAG_FUNDAMENTALS.md)** for the fundamentals, RAG motivation, RAG vs fine-tuning, offline vs online processing and the source-learning plan.

---

# 🎯 What We Are Building

A complete RAG application with two clearly separated paths:

```text
                         🔎 RAG APPLICATION
                                │
                ┌───────────────┴───────────────┐
                │                               │
                ▼                               ▼
       🔵 OFFLINE KNOWLEDGE              🟢 ONLINE RAG
          PREPARATION                       QUERY PATH
                │                               │
         Source ingestion                 User question
                ↓                               ↓
             Parsing                       Retrieval
                ↓                               ↓
            Chunking                    Augmentation
                ↓                               ↓
           Embeddings                    Generation
                ↓                               ↓
       Vector/Search Store                    LLM
                                                ↓
                                             Answer
```

**Offline** means the work prepares knowledge before a user's live question. **Online** means the work happens on the user's request path.

Strictly speaking, **RAG = Retrieval-Augmented Generation** describes retrieval → augmentation → generation. The offline ingestion/indexing pipeline prepares the knowledge store that makes the online RAG pipeline possible.

---

# 🗺️ Learning Roadmap

We will build in this order:

- [ ] **01 — Ingestion**: learn how to load different source types.
- [ ] **02 — Parsing / Normalization**: convert source-specific content into a common document representation.
- [ ] **03 — Chunking**: split documents into retrieval-friendly units.
- [ ] **04 — Embeddings**: convert chunks into vectors.
- [ ] **05 — Vector / Search Store**: persist and search vectors.
- [ ] **06 — Indexing Pipeline**: connect ingestion → parsing → chunking → embeddings → store.
- [ ] **07 — Retrieval**: retrieve the most relevant chunks for a question.
- [ ] **08 — Augmentation**: construct a grounded prompt using retrieved context.
- [ ] **09 — Generation**: call an LLM and produce an answer.
- [ ] **10 — Citations / Source Attribution**: show where the answer came from.
- [ ] **11 — Evaluation**: retrieval quality, answer quality, groundedness and latency.
- [ ] **12 — API / Application**: expose the RAG pipeline through a clean application interface.
- [ ] **13 — Advanced RAG**: metadata filtering, hybrid search, reranking, query rewriting, multi-query retrieval and parent/child retrieval.
- [ ] **14 — Production Engineering**: observability, security, configuration, testing, deployment and cost/performance engineering.
- [ ] **15 — Framework Layer**: only after understanding the pieces, introduce frameworks such as LangChain where they genuinely add value.
- [ ] **16 — Fine-tuning**: a separate learning track for SFT, LoRA/QLoRA, preference optimization and when fine-tuning should or should not complement RAG.

---

# 📥 Source Learning Plan — Easiest → Hardest

We intentionally learn sources individually and progressively increase complexity:

1. 📄 TXT / Markdown
2. 📊 CSV
3. 📗 Excel
4. 📕 PDF
5. 🌐 Web pages
6. 🔗 REST / JSON APIs
7. 🗄️ SQL databases
8. ☁️ Azure Blob / ADLS Gen2
9. 🏢 Additional enterprise/document sources later

For every source we will answer:

> **How do I connect? → How do I extract? → How do I parse? → What do I normalize? → What metadata must I preserve? → Should the source be persisted? → What can go wrong? → How does production scale it?**

We learn and test each source independently first. Only after the individual sources are understood will we consolidate common patterns into a reusable ingestion framework.

---

# 🏗️ Target Architecture

This is the destination architecture. We are **not implementing everything at once**.

```text
rag-engineering/
│
├── README.md                    ← 🧭 Single source of truth
├── requirements.txt             ← Python dependencies
├── .env.example                 ← Configuration template
├── .gitignore
├── config.yaml                  ← Non-secret configuration
│
├── docs/
│   └── RAG_FUNDAMENTALS.md      ← 🎬 RAG concepts + motivation
│
├── src/
│   ├── ingestion/               ← 🔵 Source connectors/loaders
│   ├── parsing/                 ← Normalize source content
│   ├── chunking/                ← Split documents
│   ├── embeddings/              ← Text → vectors
│   ├── vector_store/            ← Persist/search vectors
│   ├── retrieval/               ← Query → relevant chunks
│   ├── prompts/                 ← Prompt construction
│   ├── llm/                     ← LLM clients
│   ├── api/                     ← Application/API layer
│   └── utils/                   ← Shared helpers
│
├── examples/
│   └── data/                    ← Small, safe learning datasets
│
├── tests/                       ← Unit/integration tests
│
└── main.py                      ← Future application entry point
```

---

# 🚀 Current Phase: Ingestion

The ingestion layer is responsible for getting content from a source and producing a reliable common representation. It should **not** decide how content is chunked, embedded, retrieved or generated.

### Current ingestion contract

Every loader should converge on a common `Document` object:

```text
Document
├── id
├── content
├── metadata
│   ├── source_type
│   ├── source
│   └── ...source-specific metadata
└── created_at
```

The source-specific metadata is important because later retrieval must be able to answer:

> **Where did this chunk come from?**

Examples include file name, page number, row number, URL, database/table information, ADLS path, content hash and ingestion timestamps.

---

# 🔵 Production-Style Ingestion Pattern

For file/document sources, our learning implementation follows this production-oriented lifecycle:

```text
📄 SOURCE
   ↓
1. Validate
   ↓
2. Persist raw source (when appropriate)
   ↓
3. Extract
   ↓
4. Parse / normalize
   ↓
5. Create common Document
   ↓
6. Persist processed representation
   ↓
7. Hand off to Chunking
```

### Why persist raw data?

Persistence is **source- and use-case-dependent**. It is common for documents/files because it enables:

- 🔁 Reprocessing after parser changes
- ✂️ Re-chunking after chunking strategy changes
- 🧮 Re-embedding after embedding-model changes
- 🧾 Auditability and provenance
- ♻️ Recovery after downstream failures
- 🧪 Reproducible experiments

Databases, APIs and already-persisted object stores require more nuanced decisions; RAG does not mean every source must be copied into another storage system.

### Raw vs processed vs index

```text
Source
  ↓
🔵 RAW STORAGE
  Original source bytes/data
  ↓
🟢 PROCESSED STORAGE
  Normalized Document representation
  ↓
✂️ CHUNKS
  Document-level retrieval units
  ↓
🧮 EMBEDDINGS
  Vector representation
  ↓
🔎 SEARCH / VECTOR INDEX
  Persistent searchable representation
```

Processed documents are kept **individually traceable**. The eventual search index can contain chunks from many sources while preserving document/source metadata on every chunk.

### Chunking is document-level

Production pipelines can process documents in parallel batches, but a document's chunk boundaries remain within that document. We should never accidentally create a chunk by joining unrelated documents.

```text
Many Documents
      ↓
Batch / Parallel Processing
      ↓
Chunk each document independently
      ↓
Many Chunks
      ↓
Embeddings
      ↓
Search / Vector Index
```

---

# 📄 TXT Ingestion — First Production-Style Exercise

Our first source is a simple local TXT/Markdown file because it lets us understand the ingestion contract before introducing complex parsers.

### Source

```text
examples/data/sample.txt
```

### Target ADLS layout

We use the existing Azure storage account:

```text
Storage account: aiengrag
File system:     rag-raw

rag-raw/
├── raw/
│   ├── txt/
│   ├── csv/
│   ├── excel/
│   ├── pdf/
│   ├── web/
│   ├── api/
│   ├── sql/
│   └── adls/
│
└── processed/
    ├── txt/
    ├── csv/
    ├── excel/
    ├── pdf/
    ├── web/
    ├── api/
    ├── sql/
    └── adls/
```

For TXT, the execution is:

```text
examples/data/sample.txt
        ↓
Validate file
        ↓
Calculate SHA-256
        ↓
Upload exact bytes → raw/txt/sample.txt
        ↓
Decode + normalize
        ↓
Create Document
        ↓
Write JSON → processed/txt/<document_id>.json
        ↓
Ready for Chunking
```

### Why SHA-256?

The content hash gives us a deterministic fingerprint of the source content. It helps detect unchanged content and supports idempotent/incremental ingestion decisions.

We keep two concepts separate:

- **Document ID** → stable identity for the source path.
- **Content hash** → identity of the current content/version.

This allows us to recognize a document even when its content changes and detect whether the content itself changed.

### TXT command

Run from the repository root:

```powershell
python -m src.ingestion.local_file examples/data/sample.txt
```

This validates and loads the file without external persistence.

For the production-style ADLS flow:

```powershell
python -m src.ingestion.local_file examples/data/sample.txt --persist-to-adls
```

The command uses `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_FILE_SYSTEM`, `AZURE_STORAGE_RAW_ROOT` and `AZURE_STORAGE_PROCESSED_ROOT` from `.env` when available.

Expected output includes:

```text
Loaded: sample.txt
Document ID: <stable-id>
Characters: <count>
Content SHA-256: <hash>
Raw ADLS path: raw/txt/sample.txt
Processed ADLS path: processed/txt/<stable-id>.json
```

### Azure authentication

The loader uses `DefaultAzureCredential`, so local development can use the signed-in Azure CLI identity:

```powershell
az login
az account show
```

No storage account keys or SAS tokens are required by this implementation.

### TXT validation checks

The loader now checks:

- ✅ Source exists
- ✅ Source is a file
- ✅ Extension is supported (`.txt`, `.md`, `.markdown`)
- ✅ File is not empty
- ✅ Content can be decoded with the configured encoding
- ✅ Raw bytes are preserved before transformation
- ✅ Content hash is calculated
- ✅ Provenance metadata is retained
- ✅ Raw and processed paths are recorded when ADLS persistence is enabled

---

# 📁 Ingestion Components

The repository contains initial learning loaders for:

| Source | File | Learning approach |
|---|---|---|
| TXT / Markdown | `src/ingestion/local_file.py` | Local text → raw/processed → `Document` |
| PDF | `src/ingestion/pdf.py` | Initial page-level extraction |
| CSV | `src/ingestion/csv.py` | Initial row-level extraction |
| Excel | `src/ingestion/excel.py` | Initial worksheet-row extraction |
| Web | `src/ingestion/web.py` | Fetch HTML + provenance |
| REST API | `src/ingestion/api.py` | Fetch JSON + provenance |
| SQL | `src/ingestion/sql.py` | Query rows → `Document` objects |
| ADLS Gen2 | `src/ingestion/adls.py` | Entra ID access and text download |

These are intentionally **learning implementations**, not the final framework. We will test each source, understand its edge cases and production alternatives, then refactor common patterns into reusable abstractions.

---

# 🔐 Azure / ADLS Setup

The project uses the existing storage account created for our local LLM project.

```text
Storage account : aiengrag
File system     : rag-raw
Raw root        : raw
Processed root  : processed
```

### Azure CLI authentication

```powershell
az login
az account show
```

### Required access

The authenticated identity needs appropriate **data-plane** permissions on the ADLS Gen2 storage account/file system. Depending on the storage configuration, this can involve:

- Azure RBAC data-plane roles
- ADLS Gen2 filesystem/path ACLs
- Appropriate read/write permissions for the paths being accessed

For local learning, use the identity already authenticated with Azure CLI. For deployed applications, use managed identity/service identity and the minimum required permissions.

**Never commit access keys, SAS tokens, passwords, client secrets or real `.env` files.**

### Create the TXT directories manually if desired

```powershell
az storage fs directory create `
  --account-name aiengrag `
  --file-system rag-raw `
  --name raw/txt `
  --auth-mode login

az storage fs directory create `
  --account-name aiengrag `
  --file-system rag-raw `
  --name processed/txt `
  --auth-mode login
```

The Python uploader is also designed to create required parent directories when needed.

### Verify ADLS paths

```powershell
az storage fs directory list `
  --account-name aiengrag `
  --file-system rag-raw `
  --auth-mode login `
  --output table
```

---

# 🧪 Local Setup

## 1. Clone

```powershell
git clone https://github.com/RajuNaik/rag-engineering.git
cd rag-engineering
```

## 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure environment variables

```powershell
Copy-Item .env.example .env
```

The template contains non-secret configuration:

```text
AZURE_STORAGE_ACCOUNT=aiengrag
AZURE_STORAGE_FILE_SYSTEM=rag-raw
AZURE_STORAGE_RAW_ROOT=raw
AZURE_STORAGE_PROCESSED_ROOT=processed
```

`.env` is intentionally ignored by Git.

## 5. Verify Python

```powershell
python --version
where.exe python
```

The active Python path should contain:

```text
rag-engineering\.venv\Scripts\python.exe
```

---

# ▶️ Running Ingestion Examples

Run commands from the repository root.

### TXT / Markdown

```powershell
python -m src.ingestion.local_file examples/data/sample.txt
```

Production-style raw + processed persistence:

```powershell
python -m src.ingestion.local_file examples/data/sample.txt --persist-to-adls
```

### PDF

```python
from src.ingestion.pdf import load_pdf

documents = load_pdf("path/to/file.pdf")
print(len(documents))
print(documents[0].metadata)
```

### CSV

```python
from src.ingestion.csv import load_csv

documents = load_csv("path/to/file.csv")
```

### Excel

```python
from src.ingestion.excel import load_excel

documents = load_excel("path/to/file.xlsx", sheet_name=0)
```

### Web

```python
from src.ingestion.web import load_web_page

document = load_web_page("https://example.com")
```

### REST API

```python
from src.ingestion.api import load_json_api

document = load_json_api("https://example.com/api/data")
```

### SQL

```python
from src.ingestion.sql import create_sql_engine, load_sql_query

engine = create_sql_engine("YOUR_SQLALCHEMY_DATABASE_URL")
documents = load_sql_query(engine, "SELECT * FROM your_table")
```

### ADLS Gen2

```python
from src.ingestion.adls import create_adls_service_client, load_text_file

client = create_adls_service_client("aiengrag")
content = load_text_file(client, "rag-raw", "raw/txt/sample.txt")
```

For external systems, do not place credentials directly in source code. Use Entra ID, environment variables, managed identity or an appropriate secret-management mechanism.

### Run tests

```powershell
pytest -q
```

---

# 🧠 Why We Are NOT Starting With LangChain

LangChain will eventually be useful, but using it immediately can hide the engineering concepts we are trying to learn.

Before using framework abstractions, we want to understand:

```text
Loader
  ↓
Document
  ↓
Chunk
  ↓
Embedding
  ↓
Vector
  ↓
Similarity Search
  ↓
Retrieved Context
  ↓
Prompt
  ↓
LLM
```

Once these pieces are understood, we can compare our implementation with framework abstractions and decide where a framework genuinely improves maintainability.

---

# 🧱 Engineering Principles

### 1. Separation of concerns

A loader loads. A parser parses. A chunker chunks. An embedder embeds. A retriever retrieves. An LLM client calls an LLM.

### 2. Common interfaces

Different sources should eventually expose predictable interfaces while retaining source-specific metadata.

### 3. Configuration over hard-coding

Connection settings, storage paths, model names and tunable parameters belong in configuration/environment variables.

### 4. Secrets never enter Git

Use `.env` locally for non-secret configuration, Azure identity mechanisms for Azure resources, and secret managers for deployed applications.

### 5. Test every stage independently

We should be able to test ingestion without an LLM and retrieval without a UI.

### 6. Production style without premature abstraction

We follow production concepts from the beginning, but we do not hide them behind a framework until we understand the underlying implementation.

### 7. Preserve provenance

Every piece of content entering the RAG system should retain enough metadata to answer:

> **Where did this information come from?**

This becomes critical for citations, debugging, access control and evaluation.

### 8. Idempotent and incremental processing

Where practical, source identity and content hashes should allow the pipeline to skip unchanged content and reprocess only changed documents.

---

# 🧪 Quality Checks We Will Add

For every new component we will progressively add:

- ✅ Happy-path test
- ✅ Empty input test
- ✅ Invalid input test
- ✅ Missing file/source test
- ✅ Authentication failure handling where applicable
- ✅ Useful logging
- ✅ Deterministic examples where possible
- ✅ Metadata/provenance validation
- ✅ Content-hash/idempotency checks
- ✅ Integration tests for real external services where appropriate
- ✅ Retry/timeout behavior where the source supports transient failures

---

# 📚 Learning Philosophy

This repository is intentionally built as a **learning journey**, not just a finished code dump.

We will repeatedly follow this pattern:

```text
Understand
   ↓
Implement
   ↓
Run
   ↓
Inspect output
   ↓
Test failure cases
   ↓
Compare production alternatives
   ↓
Document
   ↓
Refactor
   ↓
Move to the next component
```

The README is a **living engineering handbook** and will be updated as the project progresses.

---

# 📌 Project Status

**Current stage:** 🟢 Ingestion — TXT production-style implementation

| Stage | Status |
|---|---|
| Repository setup | ✅ Complete |
| Target architecture | ✅ Defined |
| RAG fundamentals notes | ✅ Added |
| Ingestion contract | ✅ Defined |
| TXT / Markdown basic loader | ✅ Complete |
| TXT raw ADLS persistence | ✅ Implemented |
| TXT processed Document persistence | ✅ Implemented |
| TXT validation + content hash | ✅ Implemented |
| TXT end-to-end local verification | 🟢 In progress |
| CSV | ⏳ Next source |
| Excel | ⏳ |
| PDF | ⏳ |
| Web | ⏳ |
| REST API | ⏳ |
| SQL database | ⏳ |
| ADLS Gen2 source ingestion | ⏳ |
| Parsing / normalization | ⏳ |
| Chunking | ⏳ |
| Embeddings | ⏳ |
| Vector/Search store | ⏳ |
| Retrieval | ⏳ |
| Augmentation | ⏳ |
| Generation | ⏳ |
| Citations | ⏳ |
| Evaluation | ⏳ |
| API/Application | ⏳ |
| Advanced RAG | ⏳ |
| Framework layer | ⏳ |
| Fine-tuning track | ⏳ |

---

# 🔗 Useful Official Resources

- Python: https://www.python.org/
- PyPDF: https://pypdf.readthedocs.io/
- pandas: https://pandas.pydata.org/docs/
- openpyxl: https://openpyxl.readthedocs.io/
- Requests: https://requests.readthedocs.io/
- Beautiful Soup: https://beautiful-soup-4.readthedocs.io/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Azure Identity: https://learn.microsoft.com/python/api/azure-identity/
- Azure Data Lake Storage Gen2 Python SDK: https://learn.microsoft.com/python/api/overview/azure/storage-file-datalake-readme
- Azure Data Lake Storage Gen2 overview: https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-introduction

---

## ⭐ The End Goal

By the end of this repository, the goal is to confidently explain and implement:

> **How raw enterprise data becomes searchable knowledge, how a user query retrieves the right context, and how an LLM uses that context to generate a grounded answer.**

Not just:

> ❌ **"I used LangChain to build RAG."**

But:

> ✅ **"I understand and built the RAG pipeline itself, including its production trade-offs."** 🚀
