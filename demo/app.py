"""Gradio Space app for the OpenCodebook demo.

Four tabs:
  1. Try it            — type text, pick a codebook, see structured coding.
  2. Examples          — one-click public samples that populate Tab 1.
  3. Pilot results     — GLES MIP pilot agreement numbers and charts.
  4. Upload codebook   — upload a YAML codebook, validate, and code text with it.

The model backend is the Hugging Face serverless Inference API.
See ``DEPLOY.md`` for Space configuration.
"""

from __future__ import annotations

import json
from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.graph_objects as go
from gradio_client import utils as gradio_client_utils
from plotly.subplots import make_subplots

from codebook_utils import (
    get_coded_fields,
    load_codebook,
    load_codebook_from_text,
    summarize_codebook,
)
from inference import (
    DEFAULT_MODEL,
    InferenceError,
    MissingTokenError,
    code_text,
)


def _patch_gradio_client_bool_schema() -> None:
    """Work around Gradio issue #11722 for boolean JSON schema fragments."""
    original_get_type = gradio_client_utils.get_type

    def patched_get_type(schema):
        if isinstance(schema, bool):
            return "boolean"
        return original_get_type(schema)

    gradio_client_utils.get_type = patched_get_type


_patch_gradio_client_bool_schema()


# --- Assets ----------------------------------------------------------------

ASSETS = Path(__file__).resolve().parent / "assets"

BUILTIN_CODEBOOKS: dict[str, Path] = {
    "GLES MIP pilot (codebook_v1)": ASSETS / "codebooks" / "gles_mip_v1.yaml",
    "Demo codebook": ASSETS / "codebooks" / "demo_codebook.yaml",
}
DEFAULT_CODEBOOK_LABEL = "GLES MIP pilot (codebook_v1)"

LOADED_CODEBOOKS: dict[str, dict] = {
    label: load_codebook(path) for label, path in BUILTIN_CODEBOOKS.items()
}

EXAMPLES_PATH = ASSETS / "examples" / "sample_texts.json"
EXAMPLES: list[dict] = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))

AGREEMENT_CSV = ASSETS / "pilot" / "agreement_summary.csv"
AGREEMENT_META = ASSETS / "pilot" / "agreement_metadata.json"
DISAGREEMENTS_CSV = ASSETS / "pilot" / "agreement_disagreements.csv"


# --- Rendering helpers -----------------------------------------------------

REVIEW_FLAG_FIELD = "review_flag"


def _badge(label: str, value: str, tone: str = "neutral") -> str:
    tones = {
        "neutral": ("#e5e7eb", "#1f2937"),
        "ok": ("#d1fae5", "#065f46"),
        "warn": ("#fef3c7", "#92400e"),
        "alert": ("#fee2e2", "#991b1b"),
        "info": ("#dbeafe", "#1e40af"),
    }
    bg, fg = tones.get(tone, tones["neutral"])
    return (
        "<span style=\"display:inline-block;margin:4px 6px 4px 0;"
        f"padding:4px 10px;border-radius:999px;background:{bg};"
        f"color:{fg};font-size:0.9em;line-height:1.2;"
        "border:1px solid #00000010;\">"
        f"<strong style=\"font-weight:700;color:{fg};\">{label}</strong>"
        f"<span style=\"margin-left:6px;color:{fg};\">{value}</span></span>"
    )


def render_coded_badges(coded: dict) -> str:
    if not coded:
        return ""
    parts: list[str] = []
    review_value = coded.get(REVIEW_FLAG_FIELD)
    if review_value is True:
        parts.append(_badge("review_flag", "TRUE — review recommended", "alert"))
    elif review_value is False:
        parts.append(_badge("review_flag", "false", "ok"))

    for key, value in coded.items():
        if key == REVIEW_FLAG_FIELD:
            continue
        tone = "info"
        if isinstance(value, bool):
            tone = "warn" if value else "neutral"
        parts.append(_badge(key, str(value), tone))

    return "<div style=\"line-height:1.8;\">" + "".join(parts) + "</div>"


def render_coded_table(coded: dict) -> pd.DataFrame:
    if not coded:
        return pd.DataFrame(columns=["field", "value"])
    return pd.DataFrame(
        [{"field": k, "value": v} for k, v in coded.items()]
    )


def render_status(message: str, tone: str = "info") -> str:
    if not message:
        return ""
    colors = {
        "info": ("#1e40af", "#dbeafe"),
        "ok": ("#065f46", "#d1fae5"),
        "warn": ("#92400e", "#fef3c7"),
        "error": ("#991b1b", "#fee2e2"),
    }
    fg, bg = colors.get(tone, colors["info"])
    return (
        f"<div style=\"padding:10px 14px;border-radius:8px;background:{bg};"
        f"color:{fg};border:1px solid {fg}22;\">{message}</div>"
    )


# --- Coding handler --------------------------------------------------------


def run_coding(
    text: str,
    codebook: dict,
) -> tuple[pd.DataFrame, str, str, str]:
    """Return (table, badges_html, status_html, diagnostics)."""
    if not text or not text.strip():
        return (
            render_coded_table({}),
            "",
            render_status("Please enter some text to code.", "warn"),
            "",
        )

    try:
        result = code_text(text, codebook)
    except MissingTokenError as exc:
        return (
            render_coded_table({}),
            "",
            render_status(
                "<strong>Hugging Face token not configured.</strong><br>"
                f"{exc}",
                "error",
            ),
            "",
        )
    except InferenceError as exc:
        return (
            render_coded_table({}),
            "",
            render_status(f"Inference failed: {exc}", "error"),
            "",
        )
    except ValueError as exc:
        return (
            render_coded_table({}),
            "",
            render_status(
                f"Model output did not match the codebook schema: {exc}",
                "error",
            ),
            "",
        )
    except Exception as exc:  # noqa: BLE001 - keep UI alive
        return (
            render_coded_table({}),
            "",
            render_status(
                f"Unexpected error ({type(exc).__name__}): {exc}",
                "error",
            ),
            "",
        )

    tone = "warn" if result.coded.get(REVIEW_FLAG_FIELD) is True else "ok"
    status_message = (
        f"Coded with <code>{result.model}</code> "
        f"(attempts: {result.attempts}, prompt: {result.prompt_chars} chars)."
    )
    diagnostics = (
        f"Model: {result.model}\nAttempts: {result.attempts}\n"
        f"Prompt length: {result.prompt_chars} chars\n\n"
        f"Raw model response:\n{result.raw_response}"
    )
    return (
        render_coded_table(result.coded),
        render_coded_badges(result.coded),
        render_status(status_message, tone),
        diagnostics,
    )


# --- Pilot results figures -------------------------------------------------


def _parse_distribution(raw: str) -> dict[str, int]:
    if not isinstance(raw, str) or not raw.strip():
        return {}
    out: dict[str, int] = {}
    for chunk in raw.split(";"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        label, count = chunk.split("=", 1)
        try:
            out[label.strip()] = int(count.strip())
        except ValueError:
            continue
    return out


def load_agreement_summary() -> pd.DataFrame:
    df = pd.read_csv(AGREEMENT_CSV)
    display_cols = [
        "variable",
        "measurement_level",
        "agreement_metric",
        "n_compared",
        "n_matches",
        "percent_agreement",
        "kappa",
    ]
    return df[[c for c in display_cols if c in df.columns]]


def build_distribution_figure() -> go.Figure:
    df = pd.read_csv(AGREEMENT_CSV)
    variables = df["variable"].tolist()
    rows = (len(variables) + 1) // 2

    fig = make_subplots(
        rows=rows,
        cols=2,
        subplot_titles=[v.replace("_", " ") for v in variables],
        vertical_spacing=0.16,
        horizontal_spacing=0.12,
    )

    for idx, variable in enumerate(variables):
        row = idx // 2 + 1
        col = idx % 2 + 1
        variable_row = df[df["variable"] == variable].iloc[0]
        model_dist = _parse_distribution(variable_row.get("model_distribution", ""))
        reviewed_dist = _parse_distribution(variable_row.get("reviewed_distribution", ""))
        categories = sorted(set(model_dist) | set(reviewed_dist))
        model_counts = [model_dist.get(cat, 0) for cat in categories]
        reviewed_counts = [reviewed_dist.get(cat, 0) for cat in categories]

        fig.add_trace(
            go.Bar(
                name="model",
                x=categories,
                y=model_counts,
                marker_color="#6366f1",
                showlegend=(idx == 0),
                legendgroup="model",
            ),
            row=row,
            col=col,
        )
        fig.add_trace(
            go.Bar(
                name="reviewer",
                x=categories,
                y=reviewed_counts,
                marker_color="#f97316",
                showlegend=(idx == 0),
                legendgroup="reviewer",
            ),
            row=row,
            col=col,
        )
        fig.update_xaxes(row=row, col=col, tickangle=-30, tickfont={"size": 10})

    fig.update_layout(
        barmode="group",
        height=260 * rows + 120,
        margin={"t": 60, "l": 40, "r": 20, "b": 40},
        legend={"orientation": "h", "y": -0.08},
        title_text="Model vs. reviewer label distribution — GLES MIP pilot (n = 95)",
    )
    return fig


def load_disagreement_highlights(n_per_variable: int = 3) -> pd.DataFrame:
    df = pd.read_csv(DISAGREEMENTS_CSV)
    if df.empty:
        return df
    df["pair"] = df["model_value"].astype(str) + " → " + df["reviewed_value"].astype(str)
    rows = []
    for variable, group in df.groupby("variable"):
        top = (
            group.groupby("pair")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
            .head(n_per_variable)
        )
        top.insert(0, "variable", variable)
        rows.append(top)
    if not rows:
        return df
    return pd.concat(rows, ignore_index=True)[["variable", "pair", "count"]]


# --- Example tab handlers --------------------------------------------------


def use_example(text: str, fits: list[str]):
    """Populate Try it inputs from a chosen example."""
    preferred_label: str | None = None
    if fits:
        for label in BUILTIN_CODEBOOKS:
            if "gles_mip" in label.lower() and "gles_mip_v1" in fits:
                preferred_label = label
                break
            if "demo" in label.lower() and "demo_codebook" in fits:
                preferred_label = label
                break
    return (
        text,
        preferred_label or DEFAULT_CODEBOOK_LABEL,
    )


# --- Upload tab handlers ---------------------------------------------------


def handle_upload(file_path: str | None) -> tuple[str, str, str]:
    """Return (status_html, summary_markdown, codebook_state_json)."""
    if not file_path:
        return (
            render_status("Upload a YAML codebook to validate it.", "info"),
            "",
            "",
        )
    try:
        text = Path(file_path).read_text(encoding="utf-8")
        codebook = load_codebook_from_text(text)
        coded_fields = get_coded_fields(codebook)
        if not coded_fields:
            raise ValueError("Codebook has no 'codes' entries the model should code.")
        summary = summarize_codebook(codebook)
    except Exception as exc:  # noqa: BLE001 - surface to UI
        return (
            render_status(
                f"<strong>Upload rejected.</strong><br>{type(exc).__name__}: {exc}",
                "error",
            ),
            "",
            "",
        )

    details = [
        f"**codebook_name**: `{summary['codebook_name']}`",
        f"**version**: `{summary.get('version') or '—'}`",
        f"**language**: `{summary.get('language') or '—'}`",
        f"**coded fields ({summary['n_coded_fields']})**: "
        + ", ".join(f"`{name}`" for name in summary["coded_field_names"]),
    ]
    if summary["n_derived_fields"]:
        details.append(
            f"**derived fields ({summary['n_derived_fields']})**: "
            + ", ".join(f"`{name}`" for name in summary["derived_field_names"])
        )
    return (
        render_status("Codebook looks valid. Try it below.", "ok"),
        "\n\n".join(details),
        json.dumps(codebook),
    )


def run_coding_with_uploaded(text: str, codebook_state: str):
    if not codebook_state:
        return (
            render_coded_table({}),
            "",
            render_status("Upload a valid codebook first.", "warn"),
            "",
        )
    codebook = json.loads(codebook_state)
    return run_coding(text, codebook)


# --- Built-in coding tab handler ------------------------------------------


def run_coding_with_builtin(text: str, codebook_label: str):
    codebook = LOADED_CODEBOOKS.get(codebook_label)
    if codebook is None:
        return (
            render_coded_table({}),
            "",
            render_status(f"Unknown codebook: {codebook_label!r}.", "error"),
            "",
        )
    return run_coding(text, codebook)


# --- Intro markdown --------------------------------------------------------

INTRO_MARKDOWN = f"""
# OpenCodebook — interactive demo

**OpenCodebook** is an early-stage open-source project for AI-assisted,
codebook-driven coding of social-science and humanities text — a workflow
where a researcher-defined YAML codebook drives structured model output, and
where uncertainty and disagreement stay visible.

This Space is a limited hosted companion to the project. It calls
`{DEFAULT_MODEL}` via the Hugging Face serverless Inference API. The
production OpenCodebook workflow runs locally through Ollama; treat the
responses you see here as an illustration of the workflow, not as a
reproduction of production behaviour.
"""

DISAGREEMENT_INTRO = """
### Where model and reviewer disagreed most

The table below shows the most common (model → reviewer) label pairs per
variable. These are the patterns that most shaped the pilot results — for
example, the model's habit of defaulting to *descriptive* framing when the
reviewer read the response as *evaluative*.
"""


# --- App -------------------------------------------------------------------


def build_app() -> gr.Blocks:
    with gr.Blocks(
        title="OpenCodebook Demo",
        theme=gr.themes.Soft(),
        css="#header { padding-top: 8px; }",
    ) as app:
        gr.Markdown(INTRO_MARKDOWN, elem_id="header")

        with gr.Tabs() as tabs:
            # -------- Tab 1: Try it ------------------------------------
            with gr.Tab("Try it", id="try-it"):
                with gr.Row():
                    with gr.Column(scale=3):
                        codebook_picker = gr.Dropdown(
                            choices=list(BUILTIN_CODEBOOKS.keys()),
                            value=DEFAULT_CODEBOOK_LABEL,
                            label="Codebook",
                            interactive=True,
                        )
                        text_input = gr.Textbox(
                            label="Text to code",
                            placeholder=(
                                "Enter a short response, interview excerpt, "
                                "or policy snippet..."
                            ),
                            lines=6,
                        )
                        code_button = gr.Button("Code this text", variant="primary")
                    with gr.Column(scale=4):
                        status_html = gr.HTML()
                        badges_html = gr.HTML()
                        table_output = gr.Dataframe(
                            headers=["field", "value"],
                            label="Structured coding output",
                            wrap=True,
                            interactive=False,
                        )
                        with gr.Accordion("Model diagnostics", open=False):
                            diagnostics = gr.Code(
                                label="Raw model response",
                                language="json",
                            )

                code_button.click(
                    fn=run_coding_with_builtin,
                    inputs=[text_input, codebook_picker],
                    outputs=[table_output, badges_html, status_html, diagnostics],
                    api_name=False,
                )

            # -------- Tab 2: Examples ---------------------------------
            with gr.Tab("Examples", id="examples"):
                gr.Markdown(
                    "Pick a short public example. "
                    "Clicking **Try this →** populates the *Try it* tab and "
                    "selects a matching codebook."
                )
                for ex in EXAMPLES:
                    with gr.Row():
                        with gr.Column(scale=5):
                            gr.Markdown(
                                f"> {ex['text']}\n\n"
                                f"<span style=\"font-size:0.85em;color:#6b7280;\">"
                                f"<code>{ex['id']}</code> — "
                                f"language `{ex['language']}` — "
                                f"{ex.get('note', '')}</span>",
                            )
                        with gr.Column(scale=1, min_width=140):
                            ex_text_state = gr.State(ex["text"])
                            ex_fits_state = gr.State(ex.get("fits_codebook", []))
                            try_btn = gr.Button("Try this →", size="sm")
                            try_btn.click(
                                fn=use_example,
                                inputs=[ex_text_state, ex_fits_state],
                                outputs=[text_input, codebook_picker],
                                api_name=False,
                            )

            # -------- Tab 3: Pilot results ----------------------------
            with gr.Tab("Pilot results", id="pilot"):
                try:
                    meta = json.loads(AGREEMENT_META.read_text(encoding="utf-8"))
                    n_rows = meta.get("n_review_rows", "?")
                except Exception:
                    n_rows = "?"
                gr.Markdown(
                    f"""
### GLES MIP pilot — model vs. researcher review

The pilot ran `codebook_v1` on 400 sampled GLES MIP responses. A focused
review sample of **{n_rows} rows** (all model-flagged cases plus a
stratified non-flagged audit) was then coded by a human reviewer. The
table below compares model output against reviewer codes on that review
set.

For nominal variables (`issue_domain`, `framing`, `multi_issue`) the
metric is Cohen's κ. For ordinal variables (`specificity`, `ambiguity`)
the metric is weighted κ, which penalises larger rank distances more.

*No GLES text is reproduced in this Space; only derived summary
statistics and label pairs are shown.*
                    """
                )
                gr.Dataframe(
                    value=load_agreement_summary(),
                    label="Per-variable agreement summary",
                    interactive=False,
                    wrap=True,
                )
                gr.Plot(value=build_distribution_figure())
                gr.Markdown(DISAGREEMENT_INTRO)
                gr.Dataframe(
                    value=load_disagreement_highlights(),
                    label="Top disagreement pairs per variable",
                    interactive=False,
                    wrap=True,
                )

            # -------- Tab 4: Upload codebook --------------------------
            with gr.Tab("Upload your codebook", id="upload"):
                gr.Markdown(
                    """
Upload a YAML codebook to try it here. The file needs a top-level `codes:`
list. Each code can have `name`, `description`, `type` (`string` or
`boolean`), `values`, `required`, and optional `categories`/`levels`
blocks for in-prompt guidance. Optional `derived_codes:` rules (with
`set_to_true_if` conditions) are also supported.

See `codebooks/demos/demo_codebook.yaml` and
`codebooks/gles_mip/codebook_v1.yaml` in the repository for reference
shapes.
                    """
                )
                upload_input = gr.File(
                    label="YAML codebook",
                    file_types=[".yaml", ".yml"],
                    type="filepath",
                )
                upload_status = gr.HTML()
                upload_summary = gr.Markdown()
                uploaded_state = gr.State("")

                upload_input.change(
                    fn=handle_upload,
                    inputs=[upload_input],
                    outputs=[upload_status, upload_summary, uploaded_state],
                    api_name=False,
                )

                gr.Markdown("---\n### Code text with this codebook")
                upload_text_input = gr.Textbox(
                    label="Text to code",
                    placeholder=(
                        "Enter text that fits the uploaded codebook..."
                    ),
                    lines=5,
                )
                upload_code_button = gr.Button(
                    "Code with uploaded codebook", variant="primary"
                )
                upload_status_out = gr.HTML()
                upload_badges = gr.HTML()
                upload_table = gr.Dataframe(
                    headers=["field", "value"],
                    label="Structured coding output",
                    wrap=True,
                    interactive=False,
                )
                with gr.Accordion("Model diagnostics", open=False):
                    upload_diag = gr.Code(
                        label="Raw model response", language="json"
                    )

                upload_code_button.click(
                    fn=run_coding_with_uploaded,
                    inputs=[upload_text_input, uploaded_state],
                    outputs=[
                        upload_table,
                        upload_badges,
                        upload_status_out,
                        upload_diag,
                    ],
                    api_name=False,
                )

        gr.Markdown(
            """
---
<small>
<strong>OpenCodebook</strong> — AI-assisted, codebook-driven coding of SSH
text. This Space is an illustrative demo; production workflow runs
locally. GLES data is not republished; only derived summary statistics
and label pairs are shown.
</small>
            """
        )

    return app


app = build_app()


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, show_api=False)
