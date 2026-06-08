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
| 1 | SJSU Academic Catalog 2024–25 (PDF) | Full course descriptions, degree requirements, and academic policies | https://catalog.sjsu.edu/mime/media/17/7463/2024-2025+Academic+Catalog_1.pdf |
| 2 | Rate My Professors – SJSU | Student reviews of professors across all departments | https://www.ratemyprofessors.com/school/881 |
| 3 | SJSU Career Center – Job/Internship Search Guide | Official guide on networking, career fairs, Handshake, and LinkedIn for SJSU students | https://careercenter.sjsu.edu/resources/job-internship-search-guide/ |
| 4 | SJSU Career Center – Internship Journey (PDF) | Step-by-step internship guide published by the SJSU Career Center | https://www.sjsu.edu/hspm/docs/internship_journey.pdf |
| 5 | SJSU Financial Aid Brochure 2025–26 (PDF) | FAFSA, Cal Grant, scholarships, and financial aid types available to SJSU students | https://www.sjsu.edu/enrollmentmanagement/docs/fall2025/FinancialAid2025-26.pdf |
| 6 | SJSU AS SmartPass & Transportation Overview | VTA SmartPass, biking, regional transit discounts, and commute options for students | https://www.sjsu.edu/as/departments/transportation-solutions/smartpass-overview/index.php |
| 7 | SJSU AS Student Commute Guide (PDF) | Transit, parking, biking, and rideshare options around campus | https://www.sjsu.edu/as/docs/ts/Commute_Resc_Guides/studentcommuteguidenolyft.pdf |
| 8 | SJSU Recognized Student Orgs (RSO List) | Full directory of ~450 active clubs, Greek life, and student organizations | https://www.sjsu.edu/getinvolved/student-orgs/index.php |
| 9 | SJSU Student Wellness Center | Mental health, counseling (CAPS), health services, and well-being resources | https://www.sjsu.edu/wellness/ |
| 10 | Spartan Eats – Campus Dining | Official campus dining provider info, locations, meal plans, and dining options | https://www.sjsu.edu/fabs/services/commercial/food.php |

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
