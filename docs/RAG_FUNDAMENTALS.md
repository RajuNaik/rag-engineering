# 🔎 RAG Fundamentals — The Why Before the How

> **Before we build RAG, understand the problem RAG is solving.**

This note is intentionally short and audience-friendly. The detailed implementation comes later in the project.

---

## 🤔 What is RAG?

**RAG = Retrieval-Augmented Generation.**

A normal LLM mainly answers from what it learned during training. RAG adds an external knowledge-retrieval step so the model can use relevant information from a knowledge source at query time.

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

In simple terms:

> **Don't ask the LLM to remember everything. Find the right information first, then ask the LLM to reason over it.**

---

## 🚨 Why Do We Need RAG?

Imagine an employee asks:

> **"What is our company's parental leave policy for employees in India?"**

A general-purpose LLM may know what parental leave means, but it does **not automatically know your company's latest internal policy**.

The policy may also change next month.

Instead of retraining the entire model every time a document changes, RAG can retrieve the latest approved policy and provide it to the LLM as context.

```text
Company Policy PDF
        ↓
   Ingestion
        ↓
     Parsing
        ↓
    Chunking
        ↓
   Embeddings
        ↓
 Knowledge Store
        ↓
 User Question
        ↓
   Retrieval
        ↓
 Relevant Policy Sections
        ↓
      LLM
        ↓
 Answer based on retrieved context
```

---

## 💥 What Problems Does RAG Help Address?

### 1. 📚 Knowledge outside the model

Organizations have their own documents, databases, manuals, policies and knowledge bases.

RAG connects the LLM to that external knowledge.

### 2. 🔄 Frequently changing information

Company policies, product documentation, prices, procedures and operational data can change frequently.

With RAG, the knowledge source can be updated without retraining the underlying LLM for every document change.

### 3. 🎯 Domain-specific knowledge

A general LLM may have broad knowledge but still lack access to a company's private terminology, processes and documents.

RAG brings the relevant domain context into the request.

### 4. 🧠 Context-window pressure

A naive approach is to send an entire knowledge base to the LLM for every question.

That can be huge, expensive and noisy.

RAG attempts to retrieve only the most relevant pieces.

```text
10,000 documents
      ↓
Retrieve top relevant chunks
      ↓
5–10 useful chunks
      ↓
LLM
```

### 5. 🔍 Source attribution

Because retrieved chunks retain provenance, a RAG application can expose the source used to generate an answer.

```text
Answer
  +-- Source: employee_handbook.pdf
  +-- Page: 42
  +-- Section: Parental Leave
```

This is extremely useful for enterprise applications, debugging and user trust.

> **Important:** RAG can improve grounding and traceability, but it does not automatically guarantee that an answer is correct. Retrieval quality, source quality, prompting and evaluation still matter.

---

## 🏢 Real-World Example — Enterprise HR Assistant

Consider a company with:

- 5,000+ HR documents
- Different policies by country
- Benefits documents
- Employee handbooks
- Leave policies
- Payroll procedures
- Frequently updated rules

An employee asks:

> **"How many days of parental leave am I eligible for in India?"**

A RAG system could do this:

```text
Question
   ↓
Identify relevant concepts
   ↓
Search HR knowledge store
   ↓
Retrieve India + parental-leave sections
   ↓
Add those sections to the LLM prompt
   ↓
LLM generates answer
   ↓
Return answer + source references
```

The LLM is not expected to memorize the company's entire HR library.

**The system retrieves the knowledge; the LLM uses the knowledge.**

---

## 🧩 RAG Has Two Practical Sides

This distinction is important for this project.

### 🔵 Offline / Knowledge Preparation

This happens before the user's question:

```text
Sources
  ↓
Ingestion
  ↓
Parsing
  ↓
Chunking
  ↓
Embeddings
  ↓
Vector / Search Store
```

The purpose is to prepare searchable knowledge.

### 🟢 Online / Query-Time RAG

This happens when the user asks a question:

```text
User Question
  ↓
Retrieval
  ↓
Augmentation
  ↓
Generation
  ↓
Answer
```

Strictly speaking, **RAG refers to Retrieval-Augmented Generation**, while the offline ingestion/indexing pipeline prepares the knowledge store that enables the online RAG path.

---

## ⚠️ Why Not Just Retrain the LLM?

Retraining or fine-tuning and RAG solve different problems.

For example:

> A new 50-page company policy is published today.

With a RAG approach, the new document can be ingested and indexed so it becomes available to retrieval.

You don't need to teach the model's parameters the entire document simply because the document changed.

### A useful mental model

```text
Fine-tuning
→ Change/model behavior
→ Teach patterns, style, task behavior, etc.

RAG
→ Change/access knowledge
→ Retrieve external information at runtime
```

They can also be combined in real systems.

---

## 🏗️ What We Are Going to Build

We are deliberately building the system from the ground up instead of immediately hiding everything behind a framework.

```text
              RAG ENGINEERING
                    │
       ┌────────────┴────────────┐
       │                         │
   OFFLINE PATH             ONLINE PATH
       │                         │
   Ingestion                 Question
       ↓                         ↓
   Parsing                  Retrieval
       ↓                         ↓
   Chunking               Augmentation
       ↓                         ↓
   Embedding                Generation
       ↓                         ↓
 Knowledge Store               LLM
                                 ↓
                              Answer
```

And we will learn the source side from **easiest → hardest** rather than trying to build everything simultaneously.

---

# 🗺️ Ingestion Learning Order

We will start simple and progressively introduce real-world complexity:

1. 📄 **TXT / Markdown** — easiest; understand the basic loader contract.
2. 📕 **PDF** — pages, extraction quality and document metadata.
3. 📊 **CSV** — structured data and row-level documents.
4. 📗 **Excel** — workbooks, sheets, rows and metadata.
5. 🌐 **Web pages** — HTTP, HTML and noisy content.
6. 🔗 **REST / JSON APIs** — authentication, pagination and structured responses.
7. 🗄️ **SQL databases** — connections, queries, schemas and large datasets.
8. ☁️ **Azure Blob / ADLS Gen2** — cloud authentication, paths, permissions and scalable object access.
9. 🏢 **Enterprise-style sources** — additional connectors and patterns as the learning journey expands.

For every source, we will learn:

> **Connect → Load → Inspect → Normalize → Preserve metadata → Handle failures → Test**

Only after we understand these individually will we build the reusable ingestion framework.

---

## 🎯 The Big Idea

A RAG system is not simply:

> **"LLM + Vector Database."**

The engineering challenge is the complete journey:

```text
Raw enterprise data
      ↓
Can we access it?
      ↓
Can we extract it correctly?
      ↓
Can we preserve its meaning and metadata?
      ↓
Can we split it intelligently?
      ↓
Can we represent it for search?
      ↓
Can we retrieve the right information?
      ↓
Can we give the LLM the right context?
      ↓
Can we prove where the answer came from?
      ↓
Can we evaluate whether the system is actually good?
```

That is the engineering journey this repository is designed to teach. 🚀
