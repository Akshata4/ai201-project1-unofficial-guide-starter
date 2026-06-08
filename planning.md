# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | SJSU FASO – Main Financial Aid Page | Overview of all aid types: grants, loans, scholarships, work-study; includes deadlines and application links | https://www.sjsu.edu/faso/ |
| 2 | SJSU FASO – Types of Aid | Detailed breakdown of every aid category available to SJSU students | https://www.sjsu.edu/faso/types-of-aid/ |
| 3 | SJSU FASO – Seven Steps to Financial Aid | Step-by-step guide to the full FAFSA/Dream Act application and disbursement process at SJSU | https://www.sjsu.edu/faso/process/seven-steps.php |
| 4 | SJSU FASO – Scholarships Page | Campus, department, and private scholarship options with eligibility details and tips | https://www.sjsu.edu/faso/types-of-aid/scholarships/index.php |
| 5 | SJSU FASO – Scholarship External Resources | Curated list of external scholarship databases (Fastweb, Bold.org, CollegeBoard, etc.) | https://www.sjsu.edu/faso/types-of-aid/scholarships/scholarship-resources.php |
| 6 | SJSU FASO – EOP Grant | Details on the Educational Opportunity Program grant for low-income and first-gen students | https://www.sjsu.edu/faso/types-of-aid/grants/eop-grant.php |
| 7 | SJSU Financial Aid Brochure 2025–26 (PDF) | Comprehensive printable guide covering all aid types, Cal Grant, Pell, deadlines, and verification | https://www.sjsu.edu/enrollmentmanagement/docs/fall2025/FinancialAid2025-26.pdf |
| 8 | SJSU AS – Associated Students Scholarships | A.S.-administered scholarships for continuing SJSU students including leadership and advocacy awards | https://www.sjsu.edu/as/departments/government/scholarships.php |
| 9 | SJSU FASO – Financial Aid Fraud Avoidance (PDF) | Official handout warning students about scams and fraudulent aid offers | https://www.sjsu.edu/faso/docs/Avoid_Financial_Aid_Fraud.pdf |
| 10 | SJSU UndocuSpartan – Financial Aid Resources | Financial aid options specifically for undocumented and AB 540 students at SJSU | https://www.sjsu.edu/undocuspartan/paying-for-college/fin-aid-resources.php |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
