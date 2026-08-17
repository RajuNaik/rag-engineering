# 🔵 Ingestion Learning Guide

## Goal

The ingestion stage answers one question:

> **How do we reliably get content out of a source?**

It does **not** answer how to chunk, embed, retrieve or generate.

## Current loaders

- `local_file.py` — TXT / Markdown
- `pdf.py` — PDF pages
- `csv.py` — CSV rows
- `excel.py` — Excel worksheet rows
- `web.py` — raw HTML from a web page
- `api.py` — JSON from a REST endpoint
- `sql.py` — rows returned by a SQL query
- `adls.py` — ADLS Gen2 paths and text files

## Common contract

Every loader produces `Document` objects from `models.py`.

At minimum, a document has:

- `content`
- `metadata`
- `id`
- `created_at`

### Why metadata matters

Later, when a RAG answer contains a citation, we need provenance such as:

```text
source_type = pdf
source      = /documents/policy.pdf
page_number = 7
```

or:

```text
source_type = sql
source      = sql_query
row_number  = 42
```

Do not throw this information away during ingestion.

## First exercise

From the repository root:

```powershell
python -m src.ingestion.local_file examples/data/sample.txt
```

Expected output includes the file name, character count and the beginning of the document.

Then run:

```powershell
pytest -q
```

## Learning sequence

We will not simply add loaders and move on. For each source we will inspect:

1. Authentication/connection method
2. Raw source response
3. Loader responsibility
4. Metadata/provenance
5. Error handling
6. Output `Document` objects
7. What parsing still needs to do

After all source types are understood, we will refactor common patterns into reusable interfaces.
