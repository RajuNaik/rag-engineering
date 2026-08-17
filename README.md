# 🔎 RAG Engineering

> **Build a real RAG application from first principles — one component at a time.**

This repository is the hands-on learning project for building a **Retrieval-Augmented Generation (RAG) application** from the ground up.

The goal is not to hide the important concepts behind a framework on day one. We will first implement and understand the individual building blocks, test them independently, and only then introduce reusable abstractions/frameworks.

---

## 🎬 Start Here — What Is RAG?

**RAG = Retrieval-Augmented Generation.**

The simple idea is:

> **Don't ask the LLM to remember everything. Find the right information first, then ask the LLM to reason over it.**

A traditional LLM may know broad information from its training, but an enterprise application often needs access to private, changing or domain-specific knowledge. RAG adds a retrieval step that finds relevant external information and provides it to the LLM as context.

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
- 🔄 Frequently changing documents and information
- 🏢 Private/domain-specific enterprise knowledge
- 🧠 Sending an entire knowledge base to an LLM for every question
- 🔍 Need for source attribution and provenance

It does **not** magically guarantee correctness. Retrieval quality, source quality, chunking, prompting and evaluation still matter.

### 🏢 Real-world example

Imagine an enterprise HR assistant with thousands of policies and benefits documents.

An employee asks:

> **"How many days of parental leave am I eligible for in India?"**

Instead of expecting the LLM to memorize the company's HR library, the RAG system can retrieve the relevant India parental-leave sections, provide them to the LLM, and return an answer with source information.

```text
HR Documents
     ↓
Ingest → Parse → Chunk → Embed → Knowledge Store
                                      ↑
Employee Question → Retrieve → Context → LLM → Answer + Sources
```

### 📘 Want the short fundamentals guide?

See **[`docs/RAG_FUNDAMENTALS.md`](docs/RAG_FUNDAMENTALS.md)** for:

- What RAG is
- Why RAG is needed
- Problems RAG helps address
- RAG vs. retraining/fine-tuning
- Offline vs. online RAG
- A real enterprise example
- The easiest-to-hardest ingestion learning plan

---

## 🎯 What We Are Building

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

Strictly speaking, **RAG = Retrieval-Augmented Generation** describes the retrieval → augmentation → generation part. The offline ingestion/indexing pipeline prepares the knowledge store that makes the online RAG pipeline possible.

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

### 🧭 Source-learning plan — easiest → hardest

For ingestion we intentionally learn sources individually and progressively increase complexity:

1. 📄 TXT / Markdown
2. 📕 PDF
3. 📊 CSV
4. 📗 Excel
5. 🌐 Web pages
6. 🔗 REST / JSON APIs
7. 🗄️ SQL databases
8. ☁️ Azure Blob / ADLS Gen2
9. 🏢 Additional enterprise/document sources later

For every source we will answer the same questions:

> **How do I connect? → How do I load? → What does the raw response look like? → How do I normalize it? → What metadata must I preserve? → What can go wrong?**

We will **learn and test each source independently first**. Only after the individual sources are understood will we consolidate the common patterns into a reusable ingestion framework.

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

We are currently implementing **only the ingestion foundation**.

The ingestion layer is responsible for getting content from a source. It should **not** decide how the content is chunked, embedded, retrieved or generated.

### Current ingestion contract

Every loader returns a common `Document` object:

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

This separation is important:

```text
SOURCE                INGESTION          LATER
────────────────────────────────────────────────────
PDF             →     PDF loader    →    Parsing
CSV             →     CSV loader    →    Parsing
Database        →     DB loader     →    Parsing
ADLS            →     ADLS loader   →    Parsing
Web             →     Web loader    →    Parsing
```

The ingestion layer should **preserve useful source metadata** instead of throwing it away.

---

# 📁 Ingestion Components Implemented

The first ingestion foundation now contains loaders for:

| Source | File | Initial approach |
|---|---|---|
| TXT / Markdown | `src/ingestion/local_file.py` | Local text → `Document` |
| PDF | `src/ingestion/pdf.py` | One `Document` per PDF page |
| CSV | `src/ingestion/csv.py` | One `Document` per row |
| Excel | `src/ingestion/excel.py` | One `Document` per worksheet row |
| Web | `src/ingestion/web.py` | Fetch raw HTML + provenance |
| REST API | `src/ingestion/api.py` | Fetch JSON + provenance |
| SQL | `src/ingestion/sql.py` | Query rows → `Document` objects |
| ADLS Gen2 | `src/ingestion/adls.py` | List/download text with Entra ID |

These are intentionally **learning implementations**, not the final framework. We will test each source, understand its edge cases, then refactor common patterns into reusable abstractions.

### Common contract

`src/ingestion/models.py` defines the shared `Document` object. The loader should preserve provenance such as file name, page number, row number, URL, SQL source, ADLS path and other source-specific metadata.

### Current ingestion guide

See [`src/ingestion/README.md`](src/ingestion/README.md) for the source-by-source learning sequence and first exercises.

---

# 🔐 Azure / ADLS Notes

The project can use the existing Azure storage account used during the Local LLM project.

**Storage account:** `aiengrag`

For learning, the ADLS Gen2 source loader supports Microsoft Entra ID authentication rather than putting storage keys into source code.

A typical local setup uses:

```powershell
az login
az account show
```

The authenticated identity needs appropriate data-plane permissions on the storage account/container. For ADLS Gen2, this generally means the required Azure RBAC role plus ACL access when hierarchical namespace ACLs are being enforced.

**Never commit access keys, SAS tokens, passwords, client secrets or real `.env` files.**

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

If PowerShell blocks activation, use:

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

Copy the template:

```powershell
Copy-Item .env.example .env
```

Then update only the values required for the source you are testing.

`.env` is intentionally ignored by Git.

---

# ▶️ Running the Current Ingestion Examples

Run from the repository root.

### TXT / Markdown

```powershell
python -m src.ingestion.local_file examples/data/sample.txt
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
document = load_text_file(client, "rag-raw", "files/sample.txt")
```

For external systems, do not place credentials directly in source code. Use Entra ID, environment variables, managed identity or a proper secret-management mechanism as appropriate.

### Run tests

```powershell
pytest -q
```

---

# 🧠 Why We Are NOT Starting With LangChain

LangChain will eventually be useful, but using it immediately can hide the engineering concepts we are trying to learn.

For example, before using a framework abstraction, we want to understand:

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

Once these pieces are understood, we can compare our implementation with framework abstractions and decide where a framework improves maintainability.

---

# 🧱 Engineering Principles

### 1. Separation of concerns

A loader loads. A parser parses. A chunker chunks. A retriever retrieves. An LLM client calls an LLM.

### 2. Common interfaces

Different sources should eventually expose predictable interfaces while retaining source-specific metadata.

### 3. Configuration over hard-coding

Connection strings, paths, model names and tunable parameters belong in configuration/environment variables.

### 4. Secrets never enter Git

Use `.env` locally, Azure identity mechanisms for Azure resources, and secret managers for deployed applications.

### 5. Test every stage independently

We should be able to test ingestion without an LLM and retrieval without a UI.

### 6. Keep examples teachable

Production-style architecture is useful, but unnecessary abstraction will be avoided until the underlying concept has been demonstrated.

### 7. Preserve provenance

Every piece of content entering the RAG system should retain enough metadata to answer:

> **Where did this information come from?**

This becomes critical for citations, debugging and evaluation later.

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
- ✅ Integration test for real external services where appropriate

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
Document
   ↓
Refactor
   ↓
Move to the next component
```

The README is therefore treated as a **living engineering handbook** and will be updated as the project progresses.

---

# 📌 Project Status

**Current stage:** 🟢 Ingestion foundation

| Stage | Status |
|---|---|
| Repository setup | ✅ Complete |
| Target architecture | ✅ Defined |
| RAG fundamentals notes | ✅ Added |
| Ingestion contract | ✅ Defined |
| TXT / Markdown | ✅ Implemented |
| PDF | 🟢 Loader implemented — learning/test next |
| CSV | 🟢 Loader implemented — learning/test next |
| Excel | 🟢 Loader implemented — learning/test next |
| Web | 🟢 Loader implemented — learning/test next |
| REST API | 🟢 Loader implemented — learning/test next |
| SQL database | 🟢 Loader implemented — learning/test next |
| ADLS Gen2 | 🟢 Loader implemented — learning/test next |
| Parsing | ⏳ Next major stage after ingestion |
| Chunking | ⏳ |
| Embeddings | ⏳ |
| Vector/Search store | ⏳ |
| Retrieval | ⏳ |
| Augmentation | ⏳ |
| Generation | ⏳ |
| Evaluation | ⏳ |
| API/Application | ⏳ |
| Advanced RAG | ⏳ |
| Framework layer | ⏳ |

---

# 🔗 Useful Official Resources

- Python: https://www.python.org/
- PyPDF: https://pypdf.readthedocs.io/
- pandas: https://pandas.pydata.org/docs/
- openpyxl: https://openpyxl.readthedocs.io/
- Requests: https://requests.readthedocs.io/
- Beautiful Soup: https://beautiful-soup-4.readthedocs.io/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Azure Storage Python SDK: https://learn.microsoft.com/azure/storage/blobs/storage-quickstart-blobs-python
- Azure Data Lake Storage Gen2: https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-introduction

---

## ⭐ The End Goal

By the end of this repository, the goal is to be able to confidently explain and implement:

> **How raw enterprise data becomes searchable knowledge, how a user query retrieves the right context, and how an LLM uses that context to generate a grounded answer.**

Not just **"I used LangChain to build RAG."**

But:

> **"I understand and built the RAG pipeline itself."** 🚀
