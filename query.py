#!/usr/bin/env python3
"""
query.py — Retrieval + grounded generation for the SJSU Financial Aid RAG system

  retrieve(question)  →  top-5 relevant chunks from ChromaDB
  ask(question)       →  {answer, sources}  from Groq llama-3.3-70b-versatile

Grounding design:
  • The system prompt explicitly forbids using knowledge outside the context.
  • Sources are built from chunk metadata — the LLM cannot fabricate them.
  • If the context has no answer, the model is instructed to say so plainly.

Run this file directly to test 3 evaluation queries:
  python query.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import chromadb

# ── load environment variables from .env ───────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError("GROQ_API_KEY not found — add it to your .env file")

# ── settings ────────────────────────────────────────────────────────────────────
CHROMA_DIR  = Path("chroma_db")
COLLECTION  = "sjsu_financial_aid"
MODEL_NAME  = "all-MiniLM-L6-v2"
GROQ_MODEL  = "llama-3.3-70b-versatile"
TOP_K       = 5

# ── system prompt ──────────────────────────────────────────────────────────────
# This is the grounding contract with the LLM. Every line here matters:
#   - "ONLY the context" → prevents training-knowledge answers
#   - "every statement must be traceable" → explicit attribution requirement
#   - "Do not guess or speculate" → closes the gap the word "only" sometimes leaves
#   - Fixed fallback phrase → makes it easy to detect no-answer responses in tests
SYSTEM_PROMPT = """You are a financial aid assistant for San José State University (SJSU).

Use ONLY the context documents provided below to answer the student's question.
Do not add any information from your own knowledge — every statement in your
answer must be directly traceable to the provided context.

If the context does not contain enough information to answer the question,
respond with exactly: "I don't have enough information on that in the provided documents."
Do not guess, speculate, or fill in gaps from general knowledge.

When the context contains specific details (dollar amounts, deadlines, GPA thresholds,
program names), include them — accuracy on those details matters to students.
Keep your answer concise and direct: 3–6 sentences."""


# ── load resources once at import time ────────────────────────────────────────
# These are loaded when query.py is first imported (or run directly), and then
# reused for every call to retrieve() or ask() — no re-loading between queries.

print("Loading embedding model…", flush=True)
_model = SentenceTransformer(MODEL_NAME)

if not CHROMA_DIR.exists():
    raise FileNotFoundError(
        f"ChromaDB not found at '{CHROMA_DIR}/' — run embed.py first"
    )
_client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
_collection = _client.get_collection(COLLECTION)
print(f"ChromaDB ready — {_collection.count()} chunks indexed\n", flush=True)

_groq = Groq(api_key=GROQ_API_KEY)


# ══════════════════════════════════════════════════════════════════════════════
# RETRIEVAL
# ══════════════════════════════════════════════════════════════════════════════
def retrieve(question: str, k: int = TOP_K) -> list[dict]:
    """
    Embed the question and return the top-k most relevant chunks.
    Each returned dict has: text, source_name, source_url, distance.
    """
    vector = _model.encode(question)
    results = _collection.query(
        query_embeddings=[vector.tolist()],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text":        doc,
            "source_name": meta["source_name"],
            "source_url":  meta["source_url"],
            "distance":    round(dist, 4),
        })
    return hits


# ══════════════════════════════════════════════════════════════════════════════
# GENERATION
# ══════════════════════════════════════════════════════════════════════════════
def ask(question: str) -> dict:
    """
    Full RAG pipeline: retrieve relevant chunks → generate a grounded answer.

    Returns:
      {
        "answer":  str               — LLM response grounded in retrieved context
        "sources": list[str]         — unique source names, built from metadata
        "urls":    list[str]         — corresponding source URLs for attribution
        "chunks":  list[dict]        — raw retrieved chunks (for debugging)
      }

    Source attribution is programmatic — it comes from chunk metadata, not from
    whatever the LLM decides to write. The LLM cannot fabricate or omit sources.
    """
    # ── step 1: retrieve ───────────────────────────────────────────────────────
    hits = retrieve(question)

    # ── step 2: build context string for the prompt ───────────────────────────
    # Each chunk is labelled with its source so the LLM can refer to it,
    # though we don't rely on the LLM to cite — we do that ourselves below.
    context_parts = []
    for i, hit in enumerate(hits, 1):
        context_parts.append(
            f"[Document {i} — {hit['source_name']}]\n{hit['text']}"
        )
    context = "\n\n".join(context_parts)

    # ── step 3: call Groq ──────────────────────────────────────────────────────
    response = _groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system",  "content": SYSTEM_PROMPT},
            {"role": "user",    "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.1,    # low temperature = more factual, less creative
        max_tokens=512,
    )
    answer = response.choices[0].message.content.strip()

    # ── step 4: build source list from metadata (programmatic, not LLM output) ─
    # Use dict.fromkeys to deduplicate while preserving the retrieval rank order.
    seen = {}
    for hit in hits:
        name = hit["source_name"]
        if name not in seen:
            seen[name] = hit["source_url"]

    sources = list(seen.keys())
    urls    = list(seen.values())

    return {
        "answer":  answer,
        "sources": sources,
        "urls":    urls,
        "chunks":  hits,    # included so callers can inspect distances
    }


# ══════════════════════════════════════════════════════════════════════════════
# SELF-TEST  (runs when you execute  python query.py  directly)
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    TEST_QUERIES = [
        # Queries 1, 3, 5 from planning.md §Evaluation Plan
        "What is the priority deadline to apply for financial aid at SJSU?",
        "Am I eligible for financial aid as an undocumented student at SJSU?",
        "What is the EOP grant and who qualifies for it at SJSU?",
        # One out-of-scope question — system should say it doesn't know
        "What is the parking situation near the SJSU engineering building?",
    ]

    BAR = "=" * 65

    for question in TEST_QUERIES:
        print(f"\n{BAR}")
        print(f"Q: {question}")
        print(BAR)

        result = ask(question)

        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources ({len(result['sources'])}):")
        for name, url in zip(result["sources"], result["urls"]):
            print(f"  • {name}")
            print(f"    {url}")
        print(f"\nChunk distances: {[c['distance'] for c in result['chunks']]}")
