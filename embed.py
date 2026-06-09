#!/usr/bin/env python3
"""
embed.py — Embed chunks into ChromaDB and test retrieval
SJSU Financial Aid RAG system — Milestone 3

Pipeline so far:
  ingest.py  →  documents/chunks/all_chunks.json
  embed.py   →  chroma_db/   (vector store, persistent on disk)

How this script works:
  1. Load the 50 chunks produced by ingest.py
  2. Embed each chunk's text with all-MiniLM-L6-v2 (runs locally, no API key)
  3. Store the embeddings + source metadata in ChromaDB
  4. Run retrieve(query) to find the most relevant chunks for a question

Run: python embed.py
Re-running is safe — it clears and rebuilds the collection each time.
"""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb

# ── settings ────────────────────────────────────────────────────────────────────
CHUNKS_FILE = Path("documents/chunks/all_chunks.json")
CHROMA_DIR  = Path("chroma_db")
COLLECTION  = "sjsu_financial_aid"
MODEL_NAME  = "all-MiniLM-L6-v2"
TOP_K       = 5


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Load the embedding model
# ══════════════════════════════════════════════════════════════════════════════
# SentenceTransformer downloads the model (~90 MB) on the very first run, then
# caches it locally. Every run after that loads from cache in a few seconds.
print("Loading embedding model…")
model = SentenceTransformer(MODEL_NAME)
print(f"  Ready: {MODEL_NAME}\n")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Load chunks from ingest.py output
# ══════════════════════════════════════════════════════════════════════════════
if not CHUNKS_FILE.exists():
    raise FileNotFoundError(f"{CHUNKS_FILE} not found — run ingest.py first")

chunks = json.load(open(CHUNKS_FILE))
print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Set up ChromaDB
# ══════════════════════════════════════════════════════════════════════════════
# PersistentClient saves everything to disk under chroma_db/ so embeddings
# survive between runs. Delete + recreate the collection so re-runs are clean.
client = chromadb.PersistentClient(path=str(CHROMA_DIR))

try:
    client.delete_collection(COLLECTION)
    print("Cleared existing ChromaDB collection")
except Exception:
    pass  # collection didn't exist yet — that's fine

collection = client.create_collection(
    name=COLLECTION,
    # "hnsw:space": "cosine" tells ChromaDB to measure similarity with cosine
    # distance instead of the default Euclidean. Cosine works better for text
    # because it ignores vector length and focuses on direction (meaning).
    metadata={"hnsw:space": "cosine"},
)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Embed all chunks and store in ChromaDB
# ══════════════════════════════════════════════════════════════════════════════
print("\nEmbedding chunks (takes ~10–20 seconds on first run)…")

# model.encode() returns a 2-D numpy array: one 384-dim vector per chunk.
# show_progress_bar=True prints a progress bar so you can see it working.
texts      = [c["text"] for c in chunks]
embeddings = model.encode(texts, show_progress_bar=True)

# Build one metadata dict per chunk. ChromaDB metadata values must be
# str, int, float, or bool — no lists or nested dicts.
metadatas = [
    {
        "source_name": c["source_name"],   # e.g. "faso_seven_steps"
        "source_url":  c["source_url"],    # full URL for attribution
        "source_type": c["source_type"],   # "html" or "pdf"
        "chunk_index": c["chunk_index"],   # position within that document
    }
    for c in chunks
]

# Each chunk needs a unique string ID so ChromaDB can look it up later.
ids = [f"{c['source_name']}_{c['chunk_index']}" for c in chunks]

collection.add(
    ids        = ids,
    documents  = texts,
    embeddings = embeddings.tolist(),   # numpy → plain Python list
    metadatas  = metadatas,
)

print(f"\nStored {collection.count()} chunks in ChromaDB  →  {CHROMA_DIR}/")


# ══════════════════════════════════════════════════════════════════════════════
# RETRIEVAL FUNCTION
# ══════════════════════════════════════════════════════════════════════════════
def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """
    Find the k most relevant chunks for a natural-language query.

    Steps:
      1. Embed the query into the same 384-dim vector space as the chunks
      2. ChromaDB finds the k chunks whose vectors are closest to the query
         vector (lowest cosine distance = most similar meaning)
      3. Return those chunks with their text, source, and distance score

    Distance scores guide (cosine distance, lower = better match):
      < 0.3   strong match — chunk is clearly about this topic
      0.3–0.5 decent match — related content
      0.5–0.7 weak match   — only loosely related
      > 0.7   poor match   — probably off-topic
    """
    query_vector = model.encode(query)

    results = collection.query(
        query_embeddings = [query_vector.tolist()],
        n_results        = k,
        include          = ["documents", "metadatas", "distances"],
    )

    hits = []
    # results["documents"][0] is a list because ChromaDB supports batch queries;
    # [0] gets the results for our single query.
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
# TEST — 3 evaluation plan queries
# ══════════════════════════════════════════════════════════════════════════════
# Using queries 1, 3, and 5 from planning.md §Evaluation Plan.
# For each: inspect the chunks returned and their distance scores.
# Good retrieval: top result is on-topic, distance < 0.5.
# Bad retrieval:  top result is off-topic, or distance > 0.6.

TEST_QUERIES = [
    {
        "question": "What is the priority deadline to apply for financial aid at SJSU?",
        "expected": "March 2nd — for both FAFSA and California Dream Act",
    },
    {
        "question": "Am I eligible for financial aid as an undocumented student at SJSU?",
        "expected": "Yes — via California Dream Act (not FAFSA); eligible for Cal Grant, EOP, campus scholarships",
    },
    {
        "question": "What is the EOP grant and who qualifies for it at SJSU?",
        "expected": "Low-income, first-gen undergrads admitted via EOP; FAFSA/Dream Act by Jan 31",
    },
]

BAR = "=" * 65

print(f"\n\n{BAR}")
print("RETRIEVAL TEST — 3 evaluation queries")
print(BAR)

for item in TEST_QUERIES:
    question = item["question"]
    expected = item["expected"]

    print(f"\nQuery:    {question}")
    print(f"Expected: {expected}")
    print("-" * 60)

    hits = retrieve(question)

    for rank, hit in enumerate(hits, 1):
        dist = hit["distance"]
        # Label each score so it's easy to judge at a glance
        if dist < 0.3:
            label = "strong"
        elif dist < 0.5:
            label = "ok"
        elif dist < 0.7:
            label = "weak"
        else:
            label = "poor"

        print(f"\n  [{rank}] {hit['source_name']}   distance: {dist} ({label})")

        # Print a 300-char preview; collapse newlines so it fits on screen
        preview = " ".join(hit["text"].split())[:300]
        print(f"       {preview}")

    print()
