# slide-maker: turn papers, code, and documents into a native PPTX you can present

<p align="center">
  <a href="README_CN.md"><strong>简体中文</strong></a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <img alt="Codex" src="https://img.shields.io/badge/Codex-supported-111827">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-supported-5b5bd6">
  <img alt="Output: editable PPTX" src="https://img.shields.io/badge/output-native_editable_PPTX-0f766e">
</p>

> Chat with it in Codex or Claude Code. It reads your material first, then hands you a real PowerPoint: every text box, shape, and chart is click-to-edit, the script lives in speaker notes, and bullet reveals are native click builds.

<p align="center">
  <a href="https://addsumtech.github.io/slides_maker/"><strong>Live demo</strong></a> ·
  <a href="#the-fastest-way-to-judge-it-download-a-deck"><strong>Download a deck</strong></a> ·
  <a href="#template-gallery"><strong>Templates</strong></a> ·
  <a href="#what-makes-slide-maker-different"><strong>What's different</strong></a> ·
  <a href="#how-it-works"><strong>How it works</strong></a> ·
  <a href="#quick-start"><strong>Quick start</strong></a> ·
  <a href="#troubleshooting"><strong>Troubleshooting</strong></a>
</p>

## The fastest way to judge it: download a deck

**[Download the "Lab Meeting / Paper Talk" .pptx](templates/decks/en/transformer-talk/template.pptx?raw=1) and open it in PowerPoint.** It is a 15-slide reading of "Attention Is All You Need": the paper's figures are cropped straight from the PDF, the attention formula is editable native math text, the BLEU comparison is a native chart you can double-click and re-number, every slide carries a full spoken script in its notes, and bullets reveal click by click in presentation mode.

Prefer the browser first? [Flip through all 16 decks online](https://addsumtech.github.io/slides_maker/). But don't judge an AI slide tool by its marketing screenshots alone: open the file it produces and click around.

---

## Template gallery

Eight directions, one set in English and one in Chinese. Each is a complete example deck with real content, not empty placeholders.

<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/transformer-talk"><img src="docs/assets/screenshots/preview_en_transformer-talk.png" alt="Lab Meeting / Paper Talk template preview"></a><br/>
      <sub><strong>Lab Meeting / Paper Talk</strong><br/>paper reading, lab meeting, method overview, experiment report<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/transformer-talk">Flip online</a> · <a href="templates/decks/en/transformer-talk/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/nvidia-overview"><img src="docs/assets/screenshots/preview_en_nvidia-overview.png" alt="Company / Product Intro template preview"></a><br/>
      <sub><strong>Company / Product Intro</strong><br/>company overview, product matrix, customer communication, fundraising intro<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/nvidia-overview">Flip online</a> · <a href="templates/decks/en/nvidia-overview/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/nl-job-market-2026"><img src="docs/assets/screenshots/preview_en_nl-job-market-2026.png" alt="Data / Market Analysis template preview"></a><br/>
      <sub><strong>Data / Market Analysis</strong><br/>industry research, trend explanation, structured analysis<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/nl-job-market-2026">Flip online</a> · <a href="templates/decks/en/nl-job-market-2026/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/solo-company-talk"><img src="docs/assets/screenshots/preview_en_solo-company-talk.png" alt="AI Trends / Solo Talk template preview"></a><br/>
      <sub><strong>AI Trends / Solo Talk</strong><br/>trend talk, personal presentation, startup story<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/solo-company-talk">Flip online</a> · <a href="templates/decks/en/solo-company-talk/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/kids-ai-explainer"><img src="docs/assets/screenshots/preview_en_kids-ai-explainer.png" alt="Teaching / Knowledge Sharing template preview"></a><br/>
      <sub><strong>Teaching / Knowledge Sharing</strong><br/>class explanation, reading share, training material<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/kids-ai-explainer">Flip online</a> · <a href="templates/decks/en/kids-ai-explainer/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/chengdu"><img src="docs/assets/screenshots/preview_en_chengdu.png" alt="Visual Storytelling / Culture template preview"></a><br/>
      <sub><strong>Visual Storytelling / Culture</strong><br/>city, culture, event, brand story<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/chengdu">Flip online</a> · <a href="templates/decks/en/chengdu/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/standup-history"><img src="docs/assets/screenshots/preview_en_standup-history.png" alt="History / Evolution Narrative template preview"></a><br/>
      <sub><strong>History / Evolution Narrative</strong><br/>historical arc, industry evolution, timeline story<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/standup-history">Flip online</a> · <a href="templates/decks/en/standup-history/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/michael-jackson-king-of-pop"><img src="docs/assets/screenshots/preview_en_michael-jackson-king-of-pop.png" alt="Biography / Brand Story template preview"></a><br/>
      <sub><strong>Biography / Brand Story</strong><br/>public figure, brand archive, cultural retrospective<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=en/michael-jackson-king-of-pop">Flip online</a> · <a href="templates/decks/en/michael-jackson-king-of-pop/template.pptx?raw=1">Download .pptx</a></sub>
    </td>
  </tr>
</table>

<p align="center"><sub>Chinese versions live in <a href="templates/decks/">templates/decks/zh/</a>, previewed in the <a href="README_CN.md">Chinese README</a>.</sub></p>

---

## How to use the templates

The gallery lives in `templates/decks/`, English under `en/`, Chinese under `zh/`. Two ways to use them:

**Option 1: point at it (simplest).** Put the template path in your request:

```text
Use slide-maker. Follow the style of templates/decks/en/nvidia-overview/template.pptx
and build a product intro from my product.md.
```

It parses the template's layout and visual system, then applies them to your content.

**Option 2: register it for repeated use.** Copy a template you like into the local template registry, and slide-maker will list it as an option every time:

```bash
# Claude Code users
cp -r templates/decks/en/nvidia-overview ~/.claude/slide-templates/nvidia-overview

# Codex users
cp -r templates/decks/en/nvidia-overview ~/.codex/slide-templates/nvidia-overview
```

Use `en/` templates for English decks and `zh/` for Chinese ones. The layouts match; only the copy language differs.


---

## What makes slide-maker different

AI presentation tools roughly fall into four categories. slide-maker only does the last one:

| Category | Output | Editable element by element in PowerPoint? |
| --- | --- | :---: |
| Template fill-in | Content poured into a fixed template | Partially, limited by the template |
| Image-based | One big picture per slide, packed into PPTX | No, each slide is a picture |
| HTML presentation | Slides in a browser | Not a PPTX |
| **Native editable (slide-maker)** | **Real text boxes, shapes, native charts** | **Yes, click anything and edit** |

On top of that, it does four things most tools skip:

- **It reads before it draws.** A paper gets read end to end, a repo starts from its README. Every number and figure is traced back to the source, and you confirm a structure draft before any slide is drawn. It will not paste the abstract onto slide one and call it a day.
- **It gets reviewed before you see it.** After generation, every slide is rendered to an image and handed to an independent critic agent. Cramped layout, weak contrast, numbers that don't match the source: all get sent back for fixes. You receive the deck only after the critic signs off.
- **More than text stays editable.** Data charts are built as native PowerPoint charts you can double-click and re-number. Formulas are editable native math text, not screenshots. Paper figures are cropped from the PDF as-is, never redrawn.
- **Script and motion come included.** Presentation decks carry a full per-slide script in speaker notes, and bullets are native PowerPoint click builds. You can walk on stage with it.

One more thing that matters if you iterate a lot: every deck is generated by a build script that ships next to the file. Change the focus, the slide count, or the template with one sentence, and it regenerates cleanly instead of you reworking slides by hand.

To be plain about it: it does not promise a perfect deck in one shot. It promises to remove the expensive part, reading the material, planning the structure, laying out pages, making figures, writing the script, and to hand you a real file you can keep editing. The polish that remains is yours. That is exactly why the output is native PPTX.

---

## How it works

1. **It asks first.** Who is the audience, how long is the talk, live or self-read, what style. Short answers are enough. Say "you decide" if you are in a hurry.
2. **It reads the material.** Papers, docs, and repos are read in full. Figures are cropped from the PDF, key numbers are verified line by line, and nothing without a source lands on a slide.
3. **It shows you the plan.** What each slide says, which figure goes where, what gets animated. You confirm before it builds. This is the cheapest moment to change direction.
4. **It generates the PPTX.** Layout is guaranteed by code, with automatic layout checks both at build time and on the rendered output. Overflow, overlap, and font problems get caught there.
5. **An independent critic reviews it.** Rendered slides go to a critic agent that judges them against presentation standards. Fixes land, the deck is re-checked, and only then is it delivered to `~/Downloads/<deck-name>/`.

**What it costs:** the tool is free; you pay only your AI usage. The read-plan-build path is cheap; the independent review loop is the expensive part, and it scales with stakes: a quick internal deck gets a light single-pass check, while a conference-grade deck with a multi-critic panel can consume a few hundred thousand tokens. Say "light review" or "skip the critic" any time to trade polish for cost.

---

## Quick start

<p align="center">
  <img src="docs/assets/quickstart_en.png" alt="Quick start: install once, start talking, pick answers, confirm the plan, get the pptx">
</p>

### Step 1: Install

You need **Python 3.9+**, **LibreOffice** (renders slide previews for the automatic layout checks), and **one SVG rasterizer** for icons (librsvg, cairosvg, or any Chrome-family browser).

| OS | LibreOffice | Icon rasterizer |
| --- | --- | --- |
| macOS | `brew install --cask libreoffice` | `brew install librsvg` |
| Linux | `sudo apt install libreoffice` | `sudo apt install librsvg2-bin` |
| Windows | `winget install TheDocumentFoundation.LibreOffice` | Chrome or Edge installed (used headless) |

**Windows note:** the pipeline is cross-platform Python and is exercised in CI on Linux, but day-to-day development happens on macOS. If you hit a Windows-specific issue, `check_env.py` below will name the missing piece; issues with error output are welcome.

```bash
git clone https://github.com/addsumtech/slides_maker.git
cd slides_maker
python3 -m pip install -r requirements.txt
python3 scripts/install_skill.py --target both
```

If you only use one tool, replace `both` with `codex` or `claude`. Not sure what's missing? The [check command](#troubleshooting) prints the exact fix.

### Step 2: Type /slide-maker and just talk

In Claude Code, the cheapest start is zero prompt:

```text
/slide-maker
```

The interview opens instantly as a clickable, tabbed form (Topic · Template · Audience · Style): arrow keys to move, Enter to pick, and every question ships with ready-made options. The topic tab even guesses candidates from your recent projects.

Already have material? One line works too, in Claude Code or Codex, and it skips the topic question:

```text
Use slide-maker to create a PPT from paper.pdf.
```

Either way, what follows is a short conversation, not a prompt-writing exercise:

```text
It:   Before I build: which template? Who is the audience, how long,
      live or self-read? Is this PDF the only source?
      English or Chinese, visual-first or balanced?

You:  For my advisor and labmates, 12 minutes, live. Only paper.pdf.
      English, visual and concise. You pick the look.

It:   (after reading the paper) Here is the plan: 15 slides.
      Slide 4 places the paper's Figure 1 whole; the results page
      becomes a native chart you can re-number...
      Confirm the direction and I will build.
```

Three things to know:

- Short answers are enough, and **"you decide" is always a valid answer**.
- **"Show me a few style directions first"** gets you rendered style candidates to pick from.
- In Codex there is no slash command and the questions arrive as plain text. Fully supported, just less clicking; Claude Code is the smoother ride.

Other ways to open:

```text
Use slide-maker to create a technical presentation from this repository.
```

```text
I have a reference PPT: /path/ref.pptx. Use its visual style only, not its content,
and make a new English deck from paper.pdf.
```

Put your material in the current project, or give a full path in the request. No material at all? Give it a topic; it researches online first, then agrees on a structure with you.

### Optional: AI image generation

If you want a generated cover, page illustrations, or a full generated visual identity, say "use AI image generation" in the chat. Two ways to power it, either works: a Codex subscription uses its built-in image generation with no key, or set an OpenAI API key to go through the API. With neither, slide-maker still produces fully editable PPTX.

---

## Best-fit scenarios

Research talks are the home turf, because it parses the problem, method, results, figures, tables, and equations in a paper. But whenever material needs to be explained clearly, it can give you a first deck you can present and keep editing.

| What you have | What you can make |
| --- | --- |
| Papers, experiment results, paper figures | Paper reading, lab meeting, proposal, defense, experiment report |
| Code repositories, README files, technical docs | Repo walkthrough, architecture talk, progress update, engineering recap |
| Course material, product docs, market data | Class talk, product introduction, market analysis, proposal |
| Reference PPT | New topic, new content, reorganized story |

---

## Troubleshooting

If generation or preview rendering fails, run the check for your environment. Most failures are missing Python dependencies or LibreOffice:

```bash
# Codex
python3 ~/.codex/skills/slide-maker/scripts/check_env.py

# Claude Code
python3 ~/.claude/skills/slide-maker/scripts/check_env.py
```

It prints the exact fix for anything missing. If problems persist after installing dependencies, open an issue with the error output.

---

## License

[MIT](LICENSE)
