#!/usr/bin/env python3
"""
app.py — Gradio web interface for the SJSU Financial Aid RAG system

Run:  python app.py
Then open http://localhost:7860 in your browser.

The interface calls ask() from query.py, which runs the full RAG pipeline:
  student question  →  retrieve top-5 chunks  →  Groq LLM  →  grounded answer
"""

import gradio as gr
from query import ask   # the full RAG pipeline lives here

# ── example questions for the demo ────────────────────────────────────────────
EXAMPLES = [
    "What is the priority deadline to apply for financial aid at SJSU?",
    "Am I eligible for financial aid as an undocumented student at SJSU?",
    "What is the EOP grant and who qualifies for it?",
    "How much can I receive from the SJSU Spartan Scholarship, and when is the deadline?",
    "What happens if I drop units after my financial aid is disbursed?",
]


def handle_query(question: str):
    """Called by Gradio when the user clicks Ask or presses Enter."""
    if not question.strip():
        return "Please enter a question.", ""

    result = ask(question)

    # Format sources as a readable list with URLs
    source_lines = []
    for name, url in zip(result["sources"], result["urls"]):
        source_lines.append(f"• {name}\n  {url}")
    sources_text = "\n\n".join(source_lines) if source_lines else "No sources found."

    return result["answer"], sources_text


# ── Gradio UI ──────────────────────────────────────────────────────────────────
with gr.Blocks(title="SJSU Financial Aid Assistant", theme=gr.themes.Soft()) as demo:

    gr.Markdown(
        """
        # SJSU Financial Aid Assistant
        Ask any question about financial aid, scholarships, grants, loans, or work-study at San José State University.
        Answers are grounded in official SJSU documents — no hallucinated information.
        """
    )

    with gr.Row():
        with gr.Column(scale=3):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. What is the priority deadline to apply for financial aid?",
                lines=2,
            )
        with gr.Column(scale=1):
            ask_btn = gr.Button("Ask", variant="primary", size="lg")

    answer_box = gr.Textbox(
        label="Answer",
        lines=8,
        interactive=False,
    )

    sources_box = gr.Textbox(
        label="Retrieved from these SJSU documents",
        lines=5,
        interactive=False,
    )

    gr.Examples(
        examples=EXAMPLES,
        inputs=question_box,
        label="Try one of these questions",
    )

    gr.Markdown(
        "_Answers are based only on the documents indexed by this system. "
        "For official information, always verify with the "
        "[SJSU Financial Aid Office](https://www.sjsu.edu/faso/)._"
    )

    # wire up the button and Enter key to the same handler
    ask_btn.click(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )
    question_box.submit(
        fn=handle_query,
        inputs=question_box,
        outputs=[answer_box, sources_box],
    )


if __name__ == "__main__":
    demo.launch()
