# 🔎 RAG Engineering

> **Build a real RAG application from first principles — one component at a time.**

This repository is the hands-on learning project for building a **Retrieval-Augmented Generation (RAG) application** from the ground up.

The goal is not to hide the important concepts behind a framework on day one. We will first implement and understand the individual building blocks, test them independently, and only then introduce reusable abstractions/frameworks.

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

### 🧭 Source-learning plan

For ingestion we intentionally learn sources individually:

1. 📄 TXT / Markdown
2. 📕 PDF
3. 📊 CSV
4. 📗 Excel
5. 🌐 Web pages
6. 🔗 REST / JSON APIs
7. 🗄️ SQL databases
8. ☁️ Azure Blob / ADLS Gen2
9. 📁 Additional enterprise/document sources later

For every source we will answer the same questions:

> **How do I connect? → How do I load? → What does the raw response look like? → How do I normalize it? → What metadata must I preserve? → What can go wrong?**

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

# 📁 What We Will Implement First

The first ingestion milestone covers:

| Source | Initial implementation | Purpose |
|---|---|---|
| TXT / MD | Local text loader | Simplest source; establish the contract |
| PDF | `pypdf` based loader | Document ingestion |
| CSV | `pandas` based loader | Structured file ingestion |
| Excel | `pandas` + `openpyxl` | Workbook/sheet ingestion |
| Web | `requests` + BeautifulSoup | HTML ingestion |
| REST API | `requests` | JSON/API ingestion |
| SQL | SQLAlchemy | Database ingestion |
| ADLS Gen2 | Azure SDK | Cloud object/file ingestion |

We will test each source independently before moving to parsing.

---

# 🔐 Azure / ADLS Notes

The project can use the existing Azure storage account used during the Local LLM project.

**Storage account:** `aiengrag`

For learning, the ADLS Gen2 source loader will support Microsoft Entra ID authentication rather than putting storage keys into source code.

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

The first examples will be simple Python scripts so that the ingestion concepts remain visible.

Example pattern:

```powershell
python -m src.ingestion.local_file_loader
```

As new source loaders are added, the README will contain the exact command and expected output for each one.

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
| Ingestion contract | ✅ Defined |
| TXT / Markdown | 🔄 Current learning stage |
| PDF | ⏳ |
| CSV | ⏳ |
| Excel | ⏳ |
| Web | ⏳ |
| REST API | ⏳ |
| SQL database | ⏳ |
| ADLS Gen2 | ⏳ |
| Parsing | ⏳ |
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
