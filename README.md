# The Unofficial Guide — Project 1
**SJSU Financial Aid & Scholarships RAG System**
*Akshata Madavi — AI 201*

---

## Domain

**Financial Aid & Scholarships at San José State University**

This system covers the full landscape of financial aid available to SJSU students: federal grants (Pell, SEOG, TEACH), California state aid (Cal Grant A and B, Middle Class Scholarship), SJSU campus and department scholarships, the Educational Opportunity Program (EOP) grant, federal loans, work-study, and external scholarship resources — along with the step-by-step process for applying, completing verification, and receiving disbursements.

This knowledge is valuable because while SJSU's Financial Aid and Scholarship Office (FASO) publishes official information, it is scattered across 15+ separate web pages, multiple PDFs, and department-specific subsites. A first-generation student trying to answer a question like "What aid am I eligible for as an undocumented student?" has to navigate the main FASO site, the UndocuSpartan center, the California Dream Act page, and department scholarship listings separately, with no single source connecting them. Deadlines, eligibility thresholds, and dollar amounts are buried in different documents, making it easy to miss aid you qualify for or misread a deadline. The RAG system solves this by unifying all sources into one searchable knowledge base that can answer specific, high-stakes questions — deadline dates, eligibility requirements, award amounts, verification steps — in a single response.

---

## Document Sources

| # | Source | Type | URL |
|---|--------|------|-----|
| 1 | SJSU FASO – Main Financial Aid Page | HTML | https://www.sjsu.edu/faso/ |
| 2 | SJSU FASO – Types of Aid | HTML | https://www.sjsu.edu/faso/types-of-aid/ |
| 3 | SJSU FASO – Seven Steps to Financial Aid | HTML | https://www.sjsu.edu/faso/process/seven-steps.php |
| 4 | SJSU FASO – Scholarships | HTML | https://www.sjsu.edu/faso/types-of-aid/scholarships/index.php |
| 5 | SJSU FASO – External Scholarship Resources | HTML | https://www.sjsu.edu/faso/types-of-aid/scholarships/scholarship-resources.php |
| 6 | SJSU FASO – EOP Grant | HTML | https://www.sjsu.edu/faso/types-of-aid/grants/eop-grant.php |
| 7 | SJSU Financial Aid Brochure 2025–26 (PDF) | PDF | https://www.sjsu.edu/enrollmentmanagement/docs/fall2025/FinancialAid2025-26.pdf |
| 8 | SJSU Associated Students – Scholarships | HTML | https://www.sjsu.edu/as/departments/government/scholarships.php |
| 9 | SJSU FASO – Verification Process | HTML | https://www.sjsu.edu/faso/process/verification.php |
| 10 | SJSU UndocuSpartan – Financial Aid Resources | HTML | https://www.sjsu.edu/undocuspartan/paying-for-college/fin-aid-resources.php |
| 11 | SJSU FASO – Loans | HTML | https://www.sjsu.edu/faso/types-of-aid/loans/index.php |
| 12 | SJSU FASO – Work-Study | HTML | https://www.sjsu.edu/faso/types-of-aid/work-study/index.php |

> **Note on Source 9:** The original planned source (a fraud-avoidance PDF) returned HTTP 404 at the time of collection. It was replaced with the FASO Verification page, which covers an equally important topic — what students must do when selected for verification. Sources 11 and 12 (Loans, Work-Study) were added after the initial chunk count fell below 50; both cover topics referenced in the brochure PDF and fill genuine gaps in the knowledge base.

---

## Chunking Strategy

**Chunk size:** 450 tokens target (~1,800 characters), with a hard ceiling at 500 tokens (~2,000 characters)

**Overlap:** 60 tokens (~240 characters) between consecutive chunks from the same section

**Why these choices fit these documents:**

FASO pages are organized around discrete, self-contained aid topics — one section covers Cal Grant, the next Pell, the next EOP. Each section is typically 3–6 sentences answering one specific type of student question. A 400–500 token window captures one full section without bleeding into the next topic, keeping retrieved chunks topically clean and preventing mixed-aid answers (e.g., a chunk that conflates Pell Grant eligibility with loan repayment terms).

The chunking approach varies by source type:

- **HTML pages (Sources 1–6, 8–12):** The HTML cleaner replaces `<h2>` and `<h3>` tags with `## heading` markers before extracting text. The chunker then splits on those markers first, so each chunk corresponds to one semantic section (e.g., "Federal Pell Grant", "Cal Grant A and B", "Verification Process"). If a section exceeds 500 tokens, it is subdivided at paragraph boundaries; if a paragraph is still too long, a sliding character window with sentence-boundary detection is used as a last resort.

- **PDF (Source 7 — Financial Aid Brochure):** The brochure uses bold section headers that appear as short all-caps or title-case lines when extracted by pdfplumber. The chunker detects these with a regex heuristic and splits on them, then applies paragraph-level subdivision for sections that exceed the limit. The brochure's 3-column magazine layout causes some columns to merge during extraction (a known pdfplumber limitation), producing ~8 chunks with garbled text. These are identifiable by their low token count and mixed content, and they represent an accepted limitation noted in the Failure Case section.

The 60-token overlap preserves cross-sentence context at section boundaries — FASO documents frequently carry eligibility conditions from the end of one sentence into the beginning of the next, and without overlap a retriever could return a chunk whose opening ("This grant requires a 2.0 GPA") lacks the antecedent that names which grant.

**Preprocessing before chunking:**

1. BeautifulSoup removes `<nav>`, `<header>`, `<footer>`, `<script>`, `<style>`, `<aside>`, and any element whose CSS class or ID matches a regex of 30+ boilerplate patterns (nav, menu, breadcrumb, cookie, banner, sidebar, share, social, etc.). Boilerplate tags are collected into a list before any are removed to avoid a mutation-during-iteration bug where decomposing a parent sets child `.attrs` to `None`.
2. Heading tags (`<h2>`, `<h3>`) are replaced with `## heading` plain-text markers before text extraction, giving the chunker semantic split points.
3. HTML entities (`&amp;`, `&nbsp;`, `&gt;`, `&lt;`) are normalized to their ASCII equivalents.
4. In-page anchor navigation ("Jump to: X, Y, Z") is removed with a regex post-clean pass.
5. Whitespace is normalized: horizontal runs collapsed to single space, 3+ consecutive newlines collapsed to 2.

**Final chunk count:** 50 chunks across 12 sources (21 from the PDF brochure, 29 from HTML pages). Minimum chunk size enforced at 250 characters (~62 tokens) to filter cover-page and contact-info fragments.

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` from the `sentence-transformers` library, producing 384-dimensional vectors. Runs locally — no API key, no rate limits, no usage cost. ChromaDB stores the vectors on disk with cosine similarity (`hnsw:space: cosine`) so re-runs do not require re-embedding.

**Why this model fits this corpus:** FASO documents use plain, formal English with consistent terminology. The model handles the semantic gap between student phrasing and official document language — a student asking "How do I get free money for college?" retrieves chunks about grants and scholarships even though neither phrasing appears in the documents. Its 256-token context window comfortably fits query strings, and inference on a MacBook M-series chip takes under 100ms per query.

**Production tradeoff reflection:**

If deploying this system for real SJSU students with no cost constraint, I would evaluate two alternatives:

1. **`text-embedding-3-large` (OpenAI)** — longer effective context window, stronger performance on domain-specific financial and legal terminology (eligibility conditions, income thresholds). The tradeoff is API dependency, latency, and cost per embedding. For a system that re-indexes infrequently but serves many queries, cost is manageable, but an API outage would bring down the entire retrieval layer.

2. **`paraphrase-multilingual-MiniLM-L12-v2`** — SJSU's student population includes many students whose primary language is Spanish, Vietnamese, Tagalog, or Mandarin. Queries in those languages would retrieve nothing useful with a monolingual model. A multilingual model adds retrieval support for those students at a modest accuracy cost for English queries. For a campus-serving tool, that equity tradeoff is worth it.

The key tension in model choice for this domain is context length vs. local operation. FASO eligibility rules are dense and cross-referential — a longer context window would allow larger chunks that keep eligibility criteria together. But a locally-hosted model eliminates the single point of failure that an API dependency creates.

---

## Grounded Generation

**LLM:** `llama-3.3-70b-versatile` via Groq API (`temperature=0.1`, `max_tokens=512`)

**System prompt grounding instruction:**

The system prompt uses six layered constraints to prevent the LLM from answering beyond the retrieved context:

```
You are a financial aid assistant for San José State University (SJSU).

Use ONLY the context documents provided below to answer the student's question.
Do not add any information from your own knowledge — every statement in your
answer must be directly traceable to the provided context.

If the context does not contain enough information to answer the question,
respond with exactly: "I don't have enough information on that in the provided documents."
Do not guess, speculate, or fill in gaps from general knowledge.

When the context contains specific details (dollar amounts, deadlines, GPA thresholds,
program names), include them — accuracy on those details matters to students.
Keep your answer concise and direct: 3–6 sentences.
```

The six constraints are: (1) "ONLY the context documents", (2) "Do not add any information from your own knowledge", (3) "every statement must be directly traceable", (4) a fixed fallback phrase when context is insufficient, (5) "Do not guess, speculate, or fill in gaps", and (6) a low temperature setting (0.1) that reduces creative generation. The fixed fallback phrase ("I don't have enough information on that in the provided documents.") makes it easy to detect out-of-scope responses programmatically in tests.

**How source attribution is surfaced in the response:**

Sources are built **programmatically from chunk metadata**, not from the LLM's output. After generation, `ask()` iterates over the retrieved chunk list, deduplicates source names using `dict.fromkeys` (preserving retrieval rank order), and returns them as a separate `sources` and `urls` list alongside the answer. The LLM cannot fabricate, omit, or reorder sources — attribution is guaranteed by the pipeline regardless of what the model writes. In the Gradio UI, sources appear in a separate read-only text box beneath the answer, each with its URL so students can verify directly.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What is the priority deadline to apply for financial aid at SJSU? | March 2nd each year for both FAFSA and the California Dream Act application | "The priority filing deadline is March 2, 2025. All requested documents must be received by June 27, 2025, for maximum funding consideration." Top source distance: 0.25 | Relevant | Accurate |
| 2 | How much can I receive from the SJSU Spartan Scholarship, and when is the deadline? | Awards range from $250 to $4,000 per year; deadline is May 1st unless otherwise stated | "The Spartan Scholarship ranges from $250 to $4,000 per year. The deadline to apply is May 1, 2025, unless otherwise stated." Top source distance: 0.20 | Relevant | Accurate |
| 3 | Am I eligible for financial aid as an undocumented student at SJSU? | Yes — via California Dream Act (not FAFSA); eligible for Cal Grant, EOP grants, and campus scholarships | "You may be eligible for scholarships that do not require a SSN. You may still be eligible for state aid through CADAA." Also stated (confusingly): "you must be a citizen or permanent resident" — a general federal eligibility note that contradicts the point. Cal Grant not named. Top distance: 0.31 | Partially relevant — correct source in top 5 (rank 4) but generic FASO welcome page ranked first | Partially accurate |
| 4 | What happens if I drop units after my financial aid is disbursed? | Students must complete the Student Information Update form; failure may result in required repayment | "I don't have enough information on that in the provided documents." Top source distance: 0.42 | Off-target — no indexed source covers this policy | Inaccurate |
| 5 | What is the EOP grant and who qualifies for it at SJSU? | Low-income, first-gen undergrads admitted via EOP; FAFSA/Dream Act by Jan 31 | "The EOP grant serves low-income and educationally disadvantaged undergrads. Eligibility: accepted by EOP, SAI ≤ $2,500, enrolled in 6+ units. Award: $1,400/year ($700/semester)." Top distance: 0.37 | Relevant | Accurate |

---

## Failure Case Analysis

**Question that failed:** *"What happens if I drop units after my financial aid is disbursed?"*

**What the system returned:** `"I don't have enough information on that in the provided documents."` — with the closest chunk at a distance of 0.42 (weak match). The system correctly refused to fabricate an answer, but the correct response should have described the Student Information Update form and potential repayment requirements.

**Root cause — missing source coverage:**

The seven_steps page (Source 3) is the closest indexed document to this topic. Its four chunks cover Steps 1–7 of the application and disbursement process. Chunk 3 ends with a reference to an "Enrollment Requirements page" — a hyperlink — but contains only the link text, not the content of that linked page. The actual policy on what students must do when they drop below full-time enrollment, including the Student Information Update form and the conditions under which repayment is triggered, lives on a separate FASO page that was never added to the source list.

This is a **source coverage gap**, not a chunking or embedding failure. The embedding model correctly ranked the seven_steps chunks highest (0.42–0.56) because they are the closest semantic match in the corpus to "drop units" and "disbursed" — but none of those chunks contain the specific policy. The system's "I don't have enough information" response is actually the correct behavior given what was indexed; the failure occurred upstream, in the document collection stage, when the Enrollment Requirements page was not identified as a necessary source.

**What would fix it:** Add `https://www.sjsu.edu/faso/process/enrollment-requirements.php` (or the equivalent FASO page covering enrollment changes and repayment) as Source 13. After re-running `ingest.py` and `embed.py`, the unit-drop policy would be indexed and the query would retrieve it at a strong distance (likely below 0.3). This demonstrates a key property of RAG systems: generation quality is bounded by retrieval, and retrieval is bounded by what was indexed.

---

## Spec Reflection

**One way the spec helped during implementation:**

The Chunking Strategy section of planning.md specified splitting HTML by h2/h3 heading tags before falling back to paragraph boundaries or character windows. This directly shaped how the cleaner and chunker were written: during HTML cleaning, heading tags are replaced with `## heading` plain-text markers (so they survive tag stripping), and the chunker splits on those markers first. Without this plan written in advance, a simpler approach — splitting on character count alone — would have cut across section boundaries and merged, for example, the Cal Grant eligibility rules with the Pell Grant repayment terms in a single chunk. The spec's reasoning (each FASO heading marks a new aid topic) matched the actual document structure exactly, making the implementation straightforward to justify rather than arbitrary.

**One way the implementation diverged from the spec, and why:**

The spec listed 10 sources and designated Source 9 as the SJSU financial aid fraud-avoidance PDF. At collection time, that PDF URL returned HTTP 404 — the document had been removed from the SJSU server. Rather than leaving a hole in the source list, Source 9 was replaced with the FASO Verification page, which covers an equally critical student topic (what to do when selected for verification). Two additional sources (Loans, Work-Study) were added later when the initial chunk count of 48 fell below the 50-chunk floor identified during inspection — the planning.md had not specified a minimum count, and the actual FASO pages turned out to produce fewer chunks per source than anticipated because they are relatively short official pages rather than long-form guides. The final system uses 12 sources instead of the planned 10.

---

## AI Usage

**Instance 1 — Implementing the ingestion and chunking pipeline**

- *What I gave the AI:* The full Documents section (all 10 URLs, noting which were HTML and which were PDFs), the Chunking Strategy section describing semantic splits at h2/h3 boundaries for HTML and bold section headers for PDFs, and the pipeline diagram from planning.md.
- *What it produced:* A complete `ingest.py` with four stages (fetch, raw extract, clean, chunk), a `clean_html()` function that removes boilerplate by class/id pattern matching, a `chunk_text()` function that splits on `## heading` markers for HTML and a regex-based header detector for PDF, and a sliding-window fallback.
- *What I changed or overrode:* The generated code had two bugs that caused the process to be killed with exit code 137 (SIGKILL / OOM). First, `_char_window_split()` had an infinite loop: when the sliding window reached the end of the text, setting `start = end - overlap` pulled `start` backward, causing the while loop to re-enter and fill memory. Fixed by adding `if end >= len(text): break`. Second, calling `tag.decompose()` inside a `soup.find_all(True)` loop detached child tags mid-iteration, setting their `.attrs` to `None` on the next call. Fixed by collecting all boilerplate tags into a list first and decomposing in a second pass. I also replaced the dead Source 9 PDF URL and raised the minimum chunk size from 80 to 250 characters after inspecting PDF cover-page fragments that were being included in the index.

**Instance 2 — Implementing grounded generation and the system prompt**

- *What I gave the AI:* The Retrieval Approach section of planning.md (embedding model, top-k=5, cosine similarity), the pipeline diagram, the chunk schema from `all_chunks.json`, and a requirement that source attribution be programmatically guaranteed rather than left to the LLM.
- *What it produced:* `query.py` with a `retrieve()` function loading the ChromaDB collection, an `ask()` function calling the Groq API, a system prompt instructing the model to use "only the provided context," and source attribution built from chunk metadata. It also produced `app.py` with a Gradio Blocks interface wired to `ask()`.
- *What I changed or overrode:* The initial system prompt was two sentences — "Answer using only the provided context. If you don't know, say so." Running Q4 (drop units after disbursement) returned a plausible-sounding hallucination about repayment policies. I tightened the system prompt to six explicit constraints: "ONLY the context", "not from your own knowledge", "every statement must be traceable", a fixed fallback phrase, "Do not guess or speculate", and temperature set to 0.1. After tightening, Q4 correctly returned the exact fallback phrase. I also verified that sources are built from metadata after generation (not from the LLM's output) — this was in the generated code but I confirmed it by checking that removing source names from the prompt context did not affect the source list in the response.
