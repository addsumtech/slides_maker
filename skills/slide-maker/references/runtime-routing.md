# Runtime routing

Choose a profile from **capabilities first**, then use the provider as a default. Do not infer
that a model can run the Codex delivery path merely because it is made by OpenAI.

| Profile | Use when | Workflow |
|---|---|---|
| `codex` | Local Codex has a writable workspace, shell execution, PPTX rendering, and artifact return. | Full Codex adapter and delivery gate. |
| `openai-gpt-bridged` | A GPT Store GPT has Code Interpreter plus an Action/connector that can execute the bundled slide-maker scripts in a workspace and return artifacts. | Full Codex adapter and delivery gate, with `runtime: openai-gpt-bridged` in evidence. |
| `openai-gpt-sandbox` | A GPT Store GPT can write files with Code Interpreter but cannot guarantee LibreOffice/Chrome rendering or run the gate through a bridge. | Use Codex planning, visual-contract and critic packet formats, but label the hand-off `bridge verification pending`; do not claim final delivery-gate pass. |
| `shared` | Kimi, Claude Code, and any runtime without the Codex execution bridge. | Use the original shared slide-maker workflow unchanged. Do not run Codex-only evidence gates or reinterpret advisory component findings. |

## GPT Store setup

For a GPT Store GPT that must ship verified PPTX files, enable **Code Interpreter & Data Analysis**
and configure one Action that exposes a workspace runner. The runner must accept the build script,
assets, evidence and PPTX; run `render_deck.py`, `lint_deck.py`, `component_audit.py`,
`codex_visual_contract.py`, and `codex_delivery_gate.py`; then return the resulting files and logs.
Keep the Action domain scoped to that runner and provide the required privacy-policy URL for a public
GPT. Without this bridge, the GPT can prepare the same plan and files but cannot honestly attest a
final local render or delivery-gate result.

## Paste into GPT Store Instructions

```text
Runtime profile: openai-gpt-bridged only when a slide-maker execution Action is available and returns
the PPTX, rendered PNGs, lint JSON, visual-contract result, component audit, and Codex delivery-gate
result. In that profile, follow the Codex adapter exactly and put runtime: openai-gpt-bridged in the
evidence record. If the Action is unavailable, use profile openai-gpt-sandbox: create the same content
plan, direction preview, visual-contract manifest, and critic packet, but label final bridge verification
pending and never claim a render, independent critic, or gate pass that did not run. Do not use the
Codex adapter in non-OpenAI runtimes; use the shared slide-maker workflow instead.
```
