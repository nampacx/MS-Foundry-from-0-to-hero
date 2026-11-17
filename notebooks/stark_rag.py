"""Helpers for chapter 11: RAG three ways (by hand, file search, Azure AI Search).

The notebook keeps the calls it teaches (embeddings, the ranking, `vector_stores`, `responses.create`,
`client.search`, the agent tools). These helpers load and chunk the archive, build the grounded prompt, read what
a managed retriever returned, and render each turn as Markdown. Every retriever's result becomes the same shape,
a list of `(score, chunk)` hits with `chunk = {"source", "heading", "text"}`, so one view fits all three variants.

Azure and IPython imports are inside the functions: the chunking and ranking functions run with plain Python.
"""
from __future__ import annotations

import math
import os
import re
from pathlib import Path

ARCHIVE = Path(__file__).resolve().parent.parent / "data" / "archive"
NOT_FOUND = "That is not in the archive."
RULES = (f"Answer the question using only the sources below. Cite each source you use as [1], [2], ... "
         f"If the sources do not contain the answer, say '{NOT_FOUND}' and do not guess.")
SOURCES_LINE = "Sources:"


# ---------------------------------------------------------------- section 1 and 2: the archive and its chunks
def load_archive(folder: Path | None = None) -> dict[str, str]:
    """File name -> text for every Markdown file in `data/archive`."""
    return {path.name: path.read_text(encoding="utf-8") for path in sorted((folder or ARCHIVE).glob("*.md"))}


def _title(text: str, source: str) -> str:
    """The `# Title` of a document, or its file name."""
    found = re.search(r"^# (.+)$", text, flags=re.M)
    return found.group(1).strip() if found else source


def split_by_heading(text: str, source: str) -> list[dict]:
    """One chunk per `## ` section. Each chunk starts with "Title › Heading", so it makes sense on its own."""
    title, stem = _title(text, source), Path(source).stem
    chunks = []
    for number, section in enumerate(re.split(r"^## ", text, flags=re.M)[1:], 1):
        heading, _, body = section.partition("\n")
        chunks.append({"id": f"{stem}-{number}", "source": source, "heading": heading.strip(),
                       "text": f"{title} › {heading.strip()}\n{body.strip()}"})
    return chunks


def split_fixed(text: str, source: str, size: int = 300, overlap: int = 0) -> list[dict]:
    """Chunks of `size` characters, cut wherever the count ends. Shows what a cut through a fact does."""
    stem, step = Path(source).stem, max(1, size - overlap)
    return [{"id": f"{stem}-c{start}", "source": source, "heading": f"characters {start}–{min(start + size, len(text))}",
             "text": text[start:start + size]} for start in range(0, len(text), step)]


# ---------------------------------------------------------------- section 2: embed, rank, prompt
def embed(texts: list[str]) -> list[list[float]]:
    """One embedding per text, with the embedding deployment (`STARK_EMBEDDING_MODEL`) on the account endpoint."""
    from stark_helpers import embeddings_client, model
    return [row.embedding for row in embeddings_client().embeddings.create(model=model("embedding"), input=texts).data]


def cosine_similarity(u, v) -> float:
    """Cosine of the angle between two vectors: 1 = same direction, 0 = unrelated (as in chapter 01)."""
    return sum(x * y for x, y in zip(u, v)) / (math.sqrt(sum(x * x for x in u)) * math.sqrt(sum(y * y for y in v)))


def top_k(query_vector, chunks: list[dict], vectors: list, k: int = 3) -> list[tuple[float, dict]]:
    """The `k` chunks whose vectors are closest to the query vector, best first, as `(score, chunk)` hits."""
    scored = [(cosine_similarity(query_vector, vector), chunk) for chunk, vector in zip(chunks, vectors)]
    return sorted(scored, key=lambda hit: hit[0], reverse=True)[:k]


def retrieve(question: str, chunks: list[dict], vectors: list, k: int = 3) -> list[tuple[float, dict]]:
    """Embed the question, then `top_k`: the two lines step 3 writes out."""
    return top_k(embed([question])[0], chunks, vectors, k)


def label(chunk: dict) -> str:
    """`file.md › Heading`, or the file name alone when a retriever returns no heading."""
    return f"{chunk['source']} › {chunk['heading']}" if chunk.get("heading") else str(chunk["source"])


def context_of(hits: list[tuple[float, dict]]) -> str:
    """The retrieved texts, numbered [1], [2], ... The model sees exactly this, and so does the groundedness judge."""
    return "\n\n".join(f"[{n}] {label(chunk)}\n{chunk['text']}" for n, (_, chunk) in enumerate(hits, 1))


def grounded_prompt(question: str, hits: list[tuple[float, dict]]) -> str:
    """The augmented prompt: the rules, the numbered sources, then the question."""
    return f"{RULES}\n\n{SOURCES_LINE}\n{context_of(hits)}\n\nQuestion: {question}"


def cited_numbers(text: str) -> set[int]:
    """The source numbers an answer cites: "42 Nm [1]" -> {1}."""
    return {int(n) for n in re.findall(r"\[(\d+)\]", text)}


def cited_labels(text: str, hits: list[tuple[float, dict]]) -> list[str]:
    """The sources behind the `[n]` markers of an answer, in order of their number."""
    return [label(hits[n - 1][1]) for n in sorted(cited_numbers(text)) if 0 < n <= len(hits)]


def rank_of(hits: list[tuple[float, dict]], source: str, heading: str | None = None) -> int | None:
    """The 1-based rank of the first hit from `source` (and `heading`, when given); None when it is not in the hits."""
    for n, (_, chunk) in enumerate(hits, 1):
        if chunk["source"] == source and (heading is None or chunk.get("heading") == heading):
            return n
    return None


def yes_no(found: bool, expected: bool | None = None) -> str:
    """`yes` / `no` for a check, plus the expected value with ✅ / ❌ when there is a right answer."""
    shown = "yes" if found else "no"
    if expected is None:
        return shown
    return f"{shown} (expected {'yes' if expected else 'no'}) {'✅' if found == expected else '❌'}"


# ---------------------------------------------------------------- section 3: what file search returned
def _get(obj, name, default=None):
    """An attribute of an SDK model or a key of a dict."""
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def file_search_queries(response) -> list[str]:
    """The search queries the model wrote: `queries` of every `file_search_call` item."""
    return [query for item in response.output if item.type == "file_search_call" for query in (_get(item, "queries") or [])]


def file_search_hits(response) -> list[tuple[float, dict]]:
    """The chunks file search returned, as hits. Empty unless the request had `include=["file_search_call.results"]`."""
    hits = []
    for item in response.output:
        if item.type != "file_search_call":
            continue
        for result in _get(item, "results") or []:
            hits.append((_get(result, "score") or 0.0,
                         {"source": _get(result, "filename") or _get(result, "file_id") or "?", "heading": "",
                          "text": _get(result, "text") or ""}))
    return hits


def citations(response) -> list[dict]:
    """The annotations of the answer: `file_citation` (file search) and `url_citation` (Azure AI Search, web search)."""
    found = []
    for item in response.output:
        if item.type != "message":
            continue
        for part in item.content:
            for note in _get(part, "annotations") or []:
                kind = _get(note, "type")
                found.append({"type": kind, "source": _get(note, "filename") or _get(note, "title") or _get(note, "url")
                              or _get(note, "file_id") or "?", "url": _get(note, "url")})
    return found


def cited_sources(response) -> list[str]:
    """The distinct sources the answer's annotations name, in order."""
    return list(dict.fromkeys(note["source"] for note in citations(response)))


# ---------------------------------------------------------------- Markdown views (they display and return nothing)
def _cell(text) -> str:
    """Text that is safe inside a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\r", "").replace("\n", " ")


def _hit_table(hits: list[tuple[float, dict]]) -> list[str]:
    """Rank, score and source of each hit, then the retrieved texts folded."""
    if not hits:
        return ["_nothing retrieved_"]
    md = ["| rank | score | source |", "|---|---|---|"]
    md += [f"| {n} | {score:.3f} | {_cell(label(chunk))} |" for n, (score, chunk) in enumerate(hits, 1)]
    md += ["", "<details><summary>Retrieved text</summary>", "", "````text", context_of(hits), "````", "", "</details>"]
    return md


def show_chunks(chunks: list[dict]) -> None:
    """The chunks as a table: id, source, heading and size."""
    from IPython.display import Markdown, display
    md = [f"**{len(chunks)} chunks**", "", "| id | source | heading | characters |", "|---|---|---|---|"]
    md += [f"| `{c['id']}` | {c['source']} | {_cell(c['heading'])} | {len(c['text'])} |" for c in chunks]
    display(Markdown("\n".join(md)))


def show_hits(question: str, hits: list[tuple[float, dict]], checks: dict[str, str] | None = None) -> None:
    """A retrieval without an answer: the question, the ranked hits (texts folded) and the checks."""
    from IPython.display import Markdown, display
    md = [f"**Question:** {question}", ""] + _hit_table(hits)
    if checks:
        md += ["", "**Check**", "", "| | |", "|---|---|"] + [f"| {name} | {value} |" for name, value in checks.items()]
    display(Markdown("\n".join(md)))


def show_rag_turn(prompt: str, answer: str, checks: dict[str, str] | None = None, *, to: str | None = None,
                  hits: list[tuple[float, dict]] | None = None, queries: list[str] | None = None,
                  cites: list[dict] | None = None) -> None:
    """One turn as Markdown: the prompt (sources folded), what was retrieved, the whole answer, citations, checks.

    `hits=None` means no retrieval happened (the baseline); an empty list means a retriever ran and found nothing.
    """
    from IPython.display import Markdown, display
    head, marker, sources = prompt.partition(f"\n{SOURCES_LINE}\n")
    md = [f"**Prompt sent to `{to}`**" if to else "**Prompt**", ""] + [f"> {line}  " for line in head.strip().splitlines()]
    if marker:
        sources, _, question = sources.rpartition("\n\nQuestion: ")
        md += [f"> {SOURCES_LINE} see below  ", f"> Question: {question}", "",
               "<details><summary>Sources in the prompt</summary>", "", "````text", sources, "````", "", "</details>"]
    if queries:
        md += ["", "**Search queries the model wrote:** " + ", ".join(f"`{q}`" for q in queries)]
    if hits is not None:
        md += ["", "**Retrieved**", ""] + _hit_table(hits)
    md += ["", "**Answer**", "", answer or "_(no message)_"]
    if cites is not None:
        listed = [f"`{c['type']}` {c['source']}" for c in cites]
        md += ["", "**Citations:** " + (", ".join(dict.fromkeys(listed)) if listed else "none")]
    if checks:
        md += ["", "**Check**", "", "| | |", "|---|---|"] + [f"| {name} | {value} |" for name, value in checks.items()]
    display(Markdown("\n".join(md)))


# ---------------------------------------------------------------- section 4: Azure AI Search (optional)
VECTOR_PROFILE = "archive-hnsw"


def search_ready(quiet: bool = False) -> bool:
    """True when the optional Azure AI Search service is deployed; otherwise say how to deploy it (unless `quiet`)."""
    import stark_helpers  # noqa: F401 - loads .env
    if os.environ.get("STARK_ENABLE_SEARCH", "").lower() == "true" and os.environ.get("STARK_SEARCH_ENDPOINT"):
        return True
    if quiet:
        return False
    print("Azure AI Search is not deployed, so this cell does nothing. To deploy it (billed while it exists):\n"
          "  azd env set STARK_ENABLE_SEARCH true\n  azd provision\nThen restart the kernel and run the notebook again.")
    return False


def search_index_client():
    """`SearchIndexClient` on `STARK_SEARCH_ENDPOINT` with your Entra identity: creates and deletes indexes."""
    from azure.search.documents.indexes import SearchIndexClient
    from stark_helpers import cfg, credential
    return SearchIndexClient(cfg("STARK_SEARCH_ENDPOINT"), credential())


def search_client(index_name: str):
    """`SearchClient` for one index with your Entra identity: uploads and queries documents."""
    from azure.search.documents import SearchClient
    from stark_helpers import cfg, credential
    return SearchClient(cfg("STARK_SEARCH_ENDPOINT"), index_name, credential())


def archive_index(name: str, dimensions: int):
    """The index definition: one document per chunk, with text fields for keyword search and a vector field."""
    from azure.search.documents.indexes.models import (HnswAlgorithmConfiguration, SearchableField, SearchField,
                                                       SearchFieldDataType, SearchIndex, SimpleField, VectorSearch,
                                                       VectorSearchProfile)
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String),            # what keyword search reads
        SearchableField(name="title", type=SearchFieldDataType.String),              # "file.md › Heading"
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="heading", type=SearchFieldDataType.String),
        SimpleField(name="url", type=SearchFieldDataType.String),                    # the agent tool cites this field
        SearchField(name="content_vector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True, vector_search_dimensions=dimensions, vector_search_profile_name=VECTOR_PROFILE),
    ]
    vector_search = VectorSearch(algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
                                 profiles=[VectorSearchProfile(name=VECTOR_PROFILE, algorithm_configuration_name="hnsw")])
    return SearchIndex(name=name, fields=fields, vector_search=vector_search)


def search_documents(chunks: list[dict], vectors: list, base_url: str) -> list[dict]:
    """One search document per chunk: its text, where it came from, a link to the file and its vector."""
    return [{"id": chunk["id"], "content": chunk["text"], "title": label(chunk), "source": chunk["source"],
             "heading": chunk["heading"], "url": f"{base_url}/{chunk['source']}", "content_vector": vector}
            for chunk, vector in zip(chunks, vectors)]


def search_hits(results) -> list[tuple[float, dict]]:
    """The documents a `client.search(...)` call returned, as hits (`@search.score` is the score)."""
    return [(doc.get("@search.score") or 0.0,
             {"source": doc.get("source", "?"), "heading": doc.get("heading", ""), "text": doc.get("content", "")})
            for doc in results]


# ---------------------------------------------------------------- section 5: rows for the evaluation
def eval_row(query: str, hits: list[tuple[float, dict]], response: str) -> dict:
    """One evaluation row: the question, the retrieved context and the answer that was given."""
    return {"query": query, "context": context_of(hits) or "(nothing retrieved)", "response": response}


def rows_dataset_name(variant: str) -> str:
    """The dataset name of one variant's rows: "file search" -> `stark-rag-file-search`."""
    return "stark-rag-" + re.sub(r"[^a-z0-9]+", "-", variant.lower()).strip("-")


def upload_rows(variant: str, rows: list[dict]):
    """Upload one variant's rows as the dataset `stark-rag-<variant>` (version 1), replacing an earlier upload."""
    import json
    import tempfile
    from stark_helpers import project
    name = rows_dataset_name(variant)
    try:
        project().datasets.delete(name=name, version="1")   # a re-run uploads the rows again
    except Exception:  # noqa: BLE001 - nothing to replace
        pass
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / f"{name}.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        return project().datasets.upload_file(name=name, version="1", file_path=str(path))
