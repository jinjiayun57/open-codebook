# Deploying the OpenCodebook demo to Hugging Face Spaces

This directory is a self-contained Gradio app meant to run as a
Hugging Face Space. Follow the steps below to deploy it.

## 1. Create a new Space

On https://huggingface.co/new-space, fill in:

- **Owner**: your HF account or organisation
- **Space name**: `opencodebook-demo` (or anything you prefer)
- **License**: `mit`
- **SDK**: **Gradio**
- **SDK version**: Spaces will read this from `README.md`
  (`sdk_version: "4.44.0"`)
- **Hardware**: free CPU tier is enough — inference happens on the HF
  Inference API, not inside the Space.
- **Visibility**: public is fine; private works too.

Create the Space. It will be created as a dedicated Git repo, e.g.
`https://huggingface.co/spaces/<you>/opencodebook-demo`.

## 2. Add the required Space secret

In the Space, open **Settings → Variables and secrets** and add:

| Type    | Name        | Value                                    |
|---------|-------------|------------------------------------------|
| Secret  | `HF_TOKEN`  | A token from https://huggingface.co/settings/tokens (read scope is enough) |

The app also reads these optional environment variables if you want to
override defaults:

| Name                              | Default                        | Purpose                              |
|-----------------------------------|--------------------------------|--------------------------------------|
| `OPENCODEBOOK_DEMO_MODEL`         | `Qwen/Qwen2.5-7B-Instruct`     | Model id for serverless inference.   |
| `OPENCODEBOOK_DEMO_MAX_TOKENS`    | `512`                          | Max tokens per response.             |
| `OPENCODEBOOK_DEMO_TEMPERATURE`   | `0.0`                          | Sampling temperature.                |

If the default model is unavailable (serverless availability changes
over time), try one of:
- `meta-llama/Meta-Llama-3.1-8B-Instruct`
- `mistralai/Mistral-7B-Instruct-v0.3`
- `HuggingFaceH4/zephyr-7b-beta`

## 3. Push the `demo/` contents to the Space

From the project root of OpenCodebook:

```bash
# Clone the new Space repo once
git clone https://huggingface.co/spaces/<you>/opencodebook-demo /tmp/opencodebook-space

# Copy the demo contents in
cp -R demo/. /tmp/opencodebook-space/

# Commit and push
cd /tmp/opencodebook-space
git add .
git commit -m "Initial OpenCodebook demo"
git push
```

Spaces will build automatically. Expect a 1–2 minute first build while
dependencies install. Subsequent pushes rebuild incrementally.

## 4. Alternative: link a GitHub repo

If you want GitHub as the source of truth, you can either:

- **Mirror workflow.** Keep `demo/` in your OpenCodebook GitHub repo and
  run a small GitHub Actions job that pushes the folder to the Space on
  every change to `demo/**`.
- **Subtree push.** Use `git subtree push --prefix=demo space main` from
  the GitHub repo.

## 5. Smoke-test once deployed

- Open the Space URL.
- In **Try it**, paste `"Inflation macht alles unbezahlbar."` with
  *GLES MIP pilot (codebook_v2)* selected and click **Code this text**.
  Expect a structured output with `issue_domain: economy` and
  a valid `review_flag` value.
- In **Examples**, click any **Try this →**; the *Try it* tab should
  populate and activate.
- In **Pilot results**, confirm the agreement table and the distribution
  plot both render.
- In **Upload your codebook**, upload either YAML under
  `codebooks/` to confirm the upload flow works.

## 6. Messaging on the Space

The project's core message is *local, privacy-aware, researcher-defined
coding*. The hosted demo is a deliberately limited experience: small
model, hosted inference, latency dependent on HF's free tier. The Space
`README.md` already contains a disclaimer; don't remove it without
adding equivalent language elsewhere, since that's what lets the demo
coexist with the project's production-is-local framing.

## Troubleshooting

| Symptom                                            | Likely cause                                        |
|----------------------------------------------------|-----------------------------------------------------|
| "Hugging Face token not configured" in the UI      | `HF_TOKEN` not set as a Space secret.               |
| "Model is not available through the serverless..." | Chosen model currently has no serverless provider — override `OPENCODEBOOK_DEMO_MODEL`. |
| "rate limit hit"                                   | Free tier ceiling — wait or use Examples tab.       |
| "Model output could not be parsed..."              | Very small models sometimes drift from JSON — retry, or pick a larger instruct model. |
