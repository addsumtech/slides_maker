# slide-maker: editable presentations from your own material

<p align="center">
  <a href="README_CN.md"><strong>简体中文</strong></a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <img alt="Codex" src="https://img.shields.io/badge/Codex-supported-111827">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-supported-5b5bd6">
  <img alt="Output: editable PPTX" src="https://img.shields.io/badge/output-native_editable_PPTX-0f766e">
  <a href="https://skillhub.cloud.tencent.com/skills/slides-maker"><img alt="Tencent SkillHub" src="https://img.shields.io/badge/Tencent_SkillHub-get_it-2f6feb"></a>
</p>

<p align="center">
  <a href="https://clawhub.ai/dong845/skills/slide-maker"><img alt="ClawHub" src="docs/badges/clawhub.svg"></a>
  <!-- vl:vl-badge --><a href="https://slides.addsum.top/#languages"><img alt="Templates: 30" src="https://img.shields.io/badge/templates-30-c2410c"></a><!-- /vl -->
</p>

<p align="center"><sub>Free and open source, built by <a href="https://addsum.top/"><strong>Addsum</strong></a></sub></p>

slide-maker is an open-source skill for Codex and Claude Code. Give it a paper, repository, document or topic. It plans the content, designs the slides and generates a `.pptx` you can edit in PowerPoint, along with the build script.

Choose a built-in template or bring a reference deck. Confirm the outline and design before the build, then view the rendered slides and choose the level of independent review.

<p align="center">
  <a href="https://slides.addsum.top/#intro"><strong>Intro video</strong></a> ·
  <a href="#template-library"><strong>Templates</strong></a> ·
  <a href="#features-and-deliverables"><strong>Features</strong></a> ·
  <a href="#how-it-works"><strong>How it works</strong></a> ·
  <a href="#quick-start"><strong>Quick start</strong></a> ·
  <a href="#troubleshooting"><strong>Troubleshooting</strong></a>
</p>

## Template library

The skill includes <!-- vl:count-all -->thirty<!-- /vl --> templates. Each has two palettes and seven page types: cover, section, image with text, points, quote, data and closing. Typography, charts and layouts share the same design, with pages adapted to your content.

<!-- vl:count-image-cap -->Four<!-- /vl --> templates use images: **Editorial magazine (editorial), Soft organic (soft) and Collage scrapbook (collage)** arrange your photos; **Watercolour storybook (storybook)** works with a series of illustrations. The other <!-- vl:count-drawn -->twenty-six<!-- /vl --> templates use editable native shapes and need no pictures.

Twelve selected styles are shown below. Click a sample to preview all page types and both palettes.

<!-- vl:vl-gallery -->
<table>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-editorial"><img src="skills/slide-maker/assets/vl/samples/editorial.jpg" alt="editorial template sample pages"></a><br/>
      <sub><strong>Editorial magazine</strong><br/>Photo layouts<br/>
      <a href="https://slides.addsum.top/#vl-editorial">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-poster"><img src="skills/slide-maker/assets/vl/samples/poster.jpg" alt="poster template sample pages"></a><br/>
      <sub><strong>Type poster</strong><br/>launch, manifesto, opinion<br/>
      <a href="https://slides.addsum.top/#vl-poster">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-ink"><img src="skills/slide-maker/assets/vl/samples/ink.jpg" alt="ink template sample pages"></a><br/>
      <sub><strong>Ink wash</strong><br/>culture, history, craft<br/>
      <a href="https://slides.addsum.top/#vl-ink">Preview all pages</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-comic"><img src="skills/slide-maker/assets/vl/samples/comic.jpg" alt="comic template sample pages"></a><br/>
      <sub><strong>Comic panels</strong><br/>storytelling, user journey, explainer<br/>
      <a href="https://slides.addsum.top/#vl-comic">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-vinyl"><img src="skills/slide-maker/assets/vl/samples/vinyl.jpg" alt="vinyl template sample pages"></a><br/>
      <sub><strong>Vinyl record</strong><br/>music, podcast, culture<br/>
      <a href="https://slides.addsum.top/#vl-vinyl">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-stainedglass"><img src="skills/slide-maker/assets/vl/samples/stainedglass.jpg" alt="stainedglass template sample pages"></a><br/>
      <sub><strong>Stained glass</strong><br/>heritage, culture, celebrations<br/>
      <a href="https://slides.addsum.top/#vl-stainedglass">Preview all pages</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-wayfinding"><img src="skills/slide-maker/assets/vl/samples/wayfinding.jpg" alt="wayfinding template sample pages"></a><br/>
      <sub><strong>Wayfinding</strong><br/>roadmap, process, onboarding<br/>
      <a href="https://slides.addsum.top/#vl-wayfinding">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-chalkboard"><img src="skills/slide-maker/assets/vl/samples/chalkboard.jpg" alt="chalkboard template sample pages"></a><br/>
      <sub><strong>Chalkboard</strong><br/>lesson, class, training<br/>
      <a href="https://slides.addsum.top/#vl-chalkboard">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-recipe"><img src="skills/slide-maker/assets/vl/samples/recipe.jpg" alt="recipe template sample pages"></a><br/>
      <sub><strong>Recipe card</strong><br/>food, cooking, recipes<br/>
      <a href="https://slides.addsum.top/#vl-recipe">Preview all pages</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-circuit"><img src="skills/slide-maker/assets/vl/samples/circuit.jpg" alt="circuit template sample pages"></a><br/>
      <sub><strong>Circuit board</strong><br/>hardware, IoT, embedded systems<br/>
      <a href="https://slides.addsum.top/#vl-circuit">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-storybook"><img src="skills/slide-maker/assets/vl/samples/storybook.jpg" alt="storybook template sample pages"></a><br/>
      <sub><strong>Watercolour storybook</strong><br/>Illustrated storytelling<br/>
      <a href="https://slides.addsum.top/#vl-storybook">Preview all pages</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/#vl-scoreboard"><img src="skills/slide-maker/assets/vl/samples/scoreboard.jpg" alt="scoreboard template sample pages"></a><br/>
      <sub><strong>Scoreboard</strong><br/>sports, competition, team results<br/>
      <a href="https://slides.addsum.top/#vl-scoreboard">Preview all pages</a></sub>
    </td>
  </tr>
</table>
<!-- /vl -->

<p align="center"><a href="https://slides.addsum.top/#languages"><strong>Browse all <!-- vl:count-all -->thirty<!-- /vl --> templates</strong></a></p>

### Using a template

Choose a style in the [online library](https://slides.addsum.top/#languages), copy its prompt, and add your material, audience and slide count. For example:

```text
Use slide-maker with the Herbarium (herbarium) template and its light palette. Turn notes.md into an 8-slide biology lesson for middle-school students.
```

If you are unsure which style to use, ask for recommendations based on your topic. You can also supply a school or company PPTX as a reference for typography, colours and layout.

## Features and deliverables

| Feature | What you receive |
| --- | --- |
| Editable PPTX | Text boxes, native shapes and native charts you can change in PowerPoint. Photos, illustrations and cropped paper figures remain images. |
| Equations and data | Editable math text where possible; two-dimensional layouts such as fractions and matrices may be rendered as images. Data charts use native chart objects where suitable, so you can change their values. |
| Notes and animation | Presentation decks include per-slide speaker notes. Click builds are optional; static slides are supported. |
| Previews and build script | PPTX, PDF, browser preview and build script, delivered to `~/Downloads/<deck-name>/` by default. The same script supports later revisions. |
| Brand and preferences | Extract a brand kit from guidelines, a logo, an existing deck or specified colours, then confirm and save it for reuse. Recurring design preferences can be stored in a text file you can inspect, edit or delete. Your current request takes priority. |
| Version history | Keep build versions, compare changes and restore a whole deck or selected slides. |
| Canvas sizes | 16:9, 4:3, 1:1, rednote 3:4 cards, 9:16 portrait and A4, with layouts recomposed for each format. |

Key figures are checked against their sources, and paper figures are cropped from the original where possible. With only a topic, the skill researches it online before planning the slides. Before a formal presentation, confirm that the key data and conclusions match your intent.

## How it works

1. Define the task. Agree on the topic, material, audience, duration, slide count and style. You can delegate design choices; material assumptions are stated before the build.
2. Read the material. Extract text, figures, data and equations, keeping track of sources. Supported inputs include papers, repositories, Word, Excel, CSV, images, audio and video.
3. Confirm the plan. Review the slide-by-slide outline, then the typography, palette, layouts and animation. Without an existing template, you can compare design directions first.
4. Build and check. Generate the PPTX, render its pages and check file structure, overflow, overlaps and fonts.
5. View and review. See the first render, then choose the review tier. Independent reviewers check content and design; revisions are checked before delivery.
6. Revise in conversation. Ask for changes such as “turn slide 7 into a chart,” “make it 10 slides” or “shorten the notes.” The deck is rebuilt from its original script.

### Review and usage

The skill is free. Running it uses your AI subscription or API credits. Slide count, source length, image generation and review effort affect usage and elapsed time.

| `review:` | Scope |
| --- | --- |
| `fast` (default) | One round covering content and design, checking about five key claims. |
| `standard` | Separate content and design reviewers, up to two rounds, checking about ten key claims. |
| `thorough` | A fuller panel with cross-checks where required, up to three rounds, checking all key claims. Suited to defenses, pitches and other high-stakes talks. |
| `none` | Your explicit choice after viewing the render: skip independent review, including its source re-check. |

Long decks are reviewed by section as well as for overall coherence. Delegating the choice runs at least `fast`; it never skips review automatically.

## Quick start

### 1. Install runtime dependencies

You need **Python 3.9+**, **LibreOffice** to render previews, and librsvg, cairosvg or a Chrome-family browser to rasterize SVG icons.

| OS | LibreOffice | SVG icons |
| --- | --- | --- |
| macOS | `brew install --cask libreoffice` | `brew install librsvg` |
| Linux | `sudo apt install libreoffice` | `sudo apt install librsvg2-bin` |
| Windows | `winget install TheDocumentFoundation.LibreOffice` | Install Chrome or Edge |

Windows has less test coverage. Use the [environment check](#troubleshooting) if dependencies fail.

### 2. Install the skill

Clone the repository, install its Python packages and register the skill for Codex and Claude Code:

```bash
git clone --depth 1 https://github.com/addsumtech/slides_maker.git
cd slides_maker
python3 -m pip install -r skills/slide-maker/requirements.txt
python3 skills/slide-maker/scripts/install_skill.py --target both
```

Replace `both` with `codex` or `claude` if you use only one tool.

You can also install the skill with [`npx skills`](https://github.com/vercel-labs/skills):

```bash
npx skills add addsumtech/slides_maker
```

It prompts for the tool and installation scope. Add `-g` for a global install, `-a claude-code` or `-a codex` to select a tool, and `-y` to skip confirmation. This does not install runtime dependencies. After installation, ask your assistant to run the skill's `scripts/check_env.py` and follow its instructions to install missing Python packages and system tools.

Claude Code also supports plugin installation:

```text
/plugin marketplace add addsumtech/slides_maker
/plugin install slide-maker@slides-maker
```

The same runtime dependencies apply. Other distribution options: [Tencent SkillHub](https://skillhub.cloud.tencent.com/skills/slides-maker) and [ClawHub](https://clawhub.ai/dong845/skills/slide-maker). OpenClaw users can follow the ClawHub installation instructions.

### 3. Create a presentation

In Claude Code, enter `/slide-maker`. In Codex, ask for the skill in your request. Put your sources in the current project or supply a full path:

```text
Use slide-maker to turn paper.pdf into an English lab-meeting presentation for my advisor and labmates. A 12-minute live talk, about 15 slides, visual and concise. Show me the outline and design directions first.
```

It asks for details that affect the plan, such as a reference template, language, content density and animation. Short answers are enough; say “you decide” to delegate a choice. You can also start from a repository:

```text
Use slide-maker to introduce this codebase to new teammates, focusing on the architecture and main workflows.
```

With a reference deck, say whether to reuse only its design or also its content:

```text
Use the typography, colours and layouts in /path/ref.pptx as a reference. Build a new English presentation using the content of paper.pdf.
```

### Updates and optional images

When a newer version is available, slide-maker asks before updating. It stays quiet when current or offline. Remote version information is cached for 24 hours; local changes are checked each time. To disable version notifications, set `export SLIDE_MAKER_NO_VERSION_CHECK=1`.

Ask for image generation when you need a cover or illustrations. Use the image-generation tool available in your Codex environment, or configure an OpenAI API key. Image generation is optional; native text, shapes and charts do not depend on it.

## Use cases

| Source | Presentation |
| --- | --- |
| Papers, experiment results and figures | Lab meetings, paper readings, conference talks, proposals, defenses, academic posters |
| Repositories, README files, technical docs | Architecture introductions, progress updates, code walkthroughs, engineering reviews |
| Course material, product docs, market data | Lessons, product introductions, market analyses, proposals |
| A topic | A presentation planned from online research |
| A reference PPTX | New content using an existing design as a reference |
| Content for other formats | rednote cards, portrait covers, square cards, A4 one-pagers |

## Troubleshooting

If generation or rendering fails, run the check for your installation:

```bash
# Codex
python3 ~/.codex/skills/slide-maker/scripts/check_env.py

# Claude Code
python3 ~/.claude/skills/slide-maker/scripts/check_env.py
```

It lists missing dependencies and repair commands. For a plugin or project-local installation, ask your assistant to locate and run the skill's `scripts/check_env.py`.

For build errors, fonts, rendering and image sourcing, see [Troubleshooting & FAQ](skills/slide-maker/references/troubleshooting-faq.md). If the problem persists, open an [issue](https://github.com/addsumtech/slides_maker/issues) with the error output.

## Security and license

See [SECURITY.md](SECURITY.md) for reporting security issues. The project uses the [MIT license](LICENSE).
