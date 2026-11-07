# 设计强度对照 · Phase 1（测量）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用同一批素材跑出"基准 / v4.2.0 / 现在版"三组 deck，再用盲评、自动指标和过程记录回答两个问题：现在版的设计能力有没有比老版本退化，离基准差在哪。

**Architecture:**
- 一个随 skill 发布的指标脚本 `design_benchmark.py`（Phase 3 会在它上面加基准快照对比）。
- 两个仓库内的开发工具：素材抽取、盲评配对。
- 实跑和盲评由本会话派 Sonnet subagent 执行。
- 所有产物落在 `~/Desktop/slide-maker-设计对照-2026-11-07/`。

**Tech Stack:** Python 3（python-pptx、Pillow），现有 `lint_deck.py` / `composition_probe.py` / `render_deck.py`，LibreOffice 渲染。

**Spec:** `docs/superpowers/specs/2026-11-07-design-strength-baseline-design.md`

## Global Constraints

- 不花付费 API；实跑和盲评只用 Sonnet subagent。
- 不用用户自己的 deck；不写 `~/.claude/slide-templates`；每个实跑设独立的 `SLIDE_MAKER_REGISTRY`。
- 素材**不含任何设计信息**：不给颜色、字体、版式，不给 profile.md 的设计段。原图照给。
- 三组条件对齐：都不出图，都用当前渲染管线重新渲染，每份 1 次。
- 只 commit 到本地，暂存时点名路径；不推送。
- 新脚本要过 `check_inventory`、`check_tests_wired`、`check_doc_commands`（文档里的命令一律写 `python3`）。
- 结论只报几对之间一致的方向；单对差异不下结论。

## Review Focus

1. **基准 pptx 的形状没有 deckkit 标签。** 指标只能依赖几何和 lint 的统计，不能依赖组件名。Task 1 的测试用一份无标签 pptx 覆盖这一点。
2. **竖版 3:4 或不同画布尺寸。** 指标按画布比例归一化，结果不能因为尺寸不同而失真。Task 1 用 7.5×10in 的 pptx 测一次。
3. **抽取时混进设计信息。** 例如把 `profile.md` 的设计段、或文本框里的颜色说明带进素材。Task 2 断言输出里没有 `#RRGGBB` 和字体名。
4. **盲评泄露来源。** 文件名、页脚上的 "slide-maker · 示例模板"、v4/v6 字样都可能暴露来源。Task 4 断言配对文件名不含来源，评审提示里写明"忽略页脚品牌字样"。
5. **实跑没交付或中途失败。** 缺这一份就只能少比一对。Task 5 记录每份的状态，报告里如实写明缺了哪份，不能拿空结果当"没差距"。

---

### Task 1: `design_benchmark.py` 指标

**Files:**
- Create: `skills/slide-maker/scripts/design_benchmark.py`
- Test: `skills/slide-maker/tests/test_design_benchmark.py`
- Modify: `skills/slide-maker/references/file-inventory.md`（加一行），`.github/workflows/ci.yml`（core job 加一步跑该测试）

**Interfaces:**
- Produces:
  - `metrics(pptx_path: str, render_dir: str | None = None) -> dict`，键固定为：
    - `slides`；
    - `type_drama`、`size_tokens`、`avg_occupancy`：取自 lint 的 deck stats；
    - `skeleton_same_share`：内页两两 `composition_probe.divergence < SAME_COMPOSITION(0.07)` 的对数占比；
    - `skeleton_mean_div`；
    - `card_dominance: bool`、`envelope_monoculture: bool`：lint 的 stats 警告里是否出现；
    - `picture_slides`：带图页的占比；
    - `chart_slides`；
    - `standout`：各页 `max_pt` 的最大值 ÷ 各页 `max_pt` 的中位数。
  - CLI：
    - `python3 scripts/design_benchmark.py <deck.pptx> [--renders DIR] [--json OUT]`
    - `python3 scripts/design_benchmark.py --compare a.json b.json ...`：把多份指标并排打印成表。

- [ ] **Step 1: 写失败测试**，在 tests 里用 deckkit 现场造 deck：
  - `test_repetitive_deck_scores_high_same_share`：6 页同一骨架（标题 + 3 张等宽卡片）→ `skeleton_same_share >= 0.8`；
  - `test_varied_deck_scores_low_same_share`：6 页不同骨架（满版大字、左右分栏、图表、表格、三栏、居中引言）→ `skeleton_same_share <= 0.3`；
  - `test_untagged_pptx`：用纯 python-pptx 造、不经 deckkit 的 deck 也能出全部键；
  - `test_portrait_canvas`：7.5×10in 的 deck 能跑，`skeleton_same_share` 在 0–1 之间；
  - `test_compare_prints_table`：`--compare` 输出含每个文件名和 `type_drama` 列。
- [ ] **Step 2:** 跑 `python3 skills/slide-maker/tests/test_design_benchmark.py`，预期 FAIL（模块不存在）。
- [ ] **Step 3: 实现。**
  - lint 统计：子进程调 `lint_deck.py --json`，读 `deck` 和 `stats_warnings`，不 import lint 的内部函数。
  - 骨架：用 `composition_probe.signature` + `divergence`，第 1 页（封面）不计入。
  - 文件末尾照例接 `_console.safe_stdio`。
- [ ] **Step 4:** 跑测试，预期全 PASS；再跑 `check_inventory.py`、`check_tests_wired.py`、`check_doc_commands.py`，预期 clean。
- [ ] **Step 5: 校准一遍。** 对 4 份基准（重新渲染后）和 `codexcopy/deck.pptx`（临江）跑一次。预期临江的 `skeleton_same_share` 明显高于 4 份基准。若不是，说明指标是瞎的：记一条 Ruling，并在报告里写出来，不硬调到"看起来对"。
- [ ] **Step 6: Commit** `design_benchmark.py`、测试、file-inventory、ci.yml。

### Task 2: 素材抽取工具

**Files:**
- Create: `scripts/design_bench/extract_material.py`（仓库根 `scripts/` 下的开发工具，不随 skill 发布）
- Test: `scripts/design_bench/test_extract_material.py`

**Interfaces:**
- Produces: `extract(pptx_path: str, profile_md: str, out_dir: str) -> dict`，写出：
  - `素材.md`：按页顺序列出文字，表格转成 markdown 表，图表数据转成表，备注附在页后；页号只作参考，标题写"内容池，页数和结构可自行规划"。
  - `images/imgNN.<ext>`：原图原样导出，同一张图只导一次。
  - `测试材料说明.md`：受众、场合、时长，取自 profile.md 的"适用场景"一节，用正则截取该节，不带其他节。
  - 返回 `{"pages": n, "images": k, "tables": t}`。

- [ ] **Step 1: 写失败测试**，造一份含文字、表格、图表、图片的 pptx 和一份带"适用场景"和设计段的 profile.md：
  - 断言 `素材.md` 含全部文字和表格数字；
  - 断言 `素材.md` 和 `测试材料说明.md` 都不含 `#[0-9A-Fa-f]{6}`、不含 profile 设计段里的句子、不含字体名；
  - 断言图片数正确、重复图只导一次。
- [ ] **Step 2:** 跑测试，预期 FAIL。
- [ ] **Step 3:** 实现。
- [ ] **Step 4:** 跑测试，预期 PASS。对 4 份基准各跑一次，输出到 `~/Desktop/slide-maker-设计对照-2026-11-07/material/<id>/`。人工读一遍每份 `素材.md`，确认没有设计信息、内容完整。
- [ ] **Step 5: Commit** 两个文件。

### Task 3: 准备三组运行环境

不写产品代码，产出是目录和一份记录。

- [ ] **Step 1: 导出老版本。** `git archive v4.2.0 skills/slide-maker | tar -x -C <scratch>/arm-v420/`。确认其中 `SKILL.md` 是 158,589 字节。
- [ ] **Step 2: 现在版。** 用安装副本 `~/.agents/skills/slide-maker/`。先 `diff -rq` 对仓库确认一致，Task 1 的新脚本不影响运行。
- [ ] **Step 3: 重新渲染基准。** 把 4 份基准 `template.pptx` 复制到 `<desktop>/baseline/<id>/`，用当前 `render_deck.py` 渲染。
- [ ] **Step 4: 保存证据。** 把临江副本 `codexcopy/` 复制到 `<desktop>/evidence/linjiang/`，scratchpad 会被清理。
- [ ] **Step 5:** 在 `<desktop>/runs.md` 写下每个运行的目录、registry 路径、skill 路径。

### Task 4: 盲评配对工具

**Files:**
- Create: `scripts/design_bench/make_pairs.py`
- Test: `scripts/design_bench/test_make_pairs.py`

**Interfaces:**
- Produces: `make_pairs(entries: list[dict], out_dir: str, seed: int) -> list[dict]`
  - 输入 entry 是 `{"brief": id, "arm": "baseline|v420|current", "contact": path}`。
  - 对每个 brief 生成两组配对：v420 vs current、current vs baseline。每组两种左右顺序，共 4 张拼图 `pair_<随机8位>.png`，左右各一张 contact sheet，中间留白，标 "A" / "B"。
  - 映射写进 `key.json`。拼图文件名和图上都不含来源。

- [ ] **Step 1: 写失败测试**：
  - 2 个 brief → 8 张拼图；
  - 文件名不含 `baseline`、`v420`、`current`、brief id；
  - `key.json` 能还原每张拼图左右的来源；
  - 同一 seed 结果相同。
- [ ] **Step 2:** 跑测试，预期 FAIL。
- [ ] **Step 3:** 实现。contact sheet 缺失时，用 `render/slideNN.png` 拼一张 3 列的。
- [ ] **Step 4:** 跑测试，预期 PASS。
- [ ] **Step 5: Commit。**

### Task 5: 9 个实跑

- [ ] **Step 1: 第一批，5 个并行，后台运行。**
  - 现在版 × 4 份素材。
  - Codex 式 × 1（quarterly-review）：提示里加上"只读 SKILL.md 和 references 文档、不读任何 .py 源码，只执行命令输出里给的下一步"。
- [ ] **Step 2: 第二批。** 第一批结束后，v4.2.0 × 4。
- [ ] **Step 3: 收集。** 每个运行结束后，在 `runs.md` 记下：是否交付 deck.pptx、耗时、写了哪些 waiver。没交付的标"缺"，不重跑，因为每份只跑一次。若 4 份里缺 2 份以上，停下报告。

**每个实跑的提示词模板**（填 `{skill}`、`{material}`、`{out}`、`{registry}`）：

```
You are testing the slide-maker skill. Its SKILL.md is at {skill}/SKILL.md — read it and follow it
as the skill instructs; its scripts are under {skill}/scripts (run them with python3).
Build a deck from the material in {material} (read 测试材料说明.md first: it states the audience,
occasion and length — treat those as the interview answers; this is AUTO mode: do not ask questions,
decide and record your basis as the skill says for auto mode). Use only the images provided; do not
generate images. Work in {out}; deliver {out}/deck.pptx and its render/ folder.
export SLIDE_MAKER_REGISTRY={registry} and SLIDE_MAKER_NO_OPEN=1 before running any script.
Never read or write ~/.claude/slide-templates or any file outside {out}, {material}, {skill}.
If the skill asks for an independent critic and you cannot dispatch one, use the skill's documented
waiver for that. When done, reply with: the deck path, slide count, every waiver you wrote, and the
list of skill files you actually read.
```

### Task 6: 指标与盲评

- [ ] **Step 1: 指标。** 对 12 个 deck（4 基准 + 4 v420 + 4 current）和 Codex 式那份跑 `design_benchmark.py --json`，再 `--compare` 生成 `metrics.md`。
- [ ] **Step 2: 配对。** 用 `make_pairs.py` 生成 16 张拼图（seed 固定，记在 runs.md）。
- [ ] **Step 3: 盲评。** 每张拼图交给一个独立的 Sonnet agent，提示词：

```
Two slide decks, A (left) and B (right), built from the same content. Ignore any footer brand text.
Score each 1–5 on: boldness/novelty · variety of page skeletons · visual hierarchy and a clear
focal page · fit of components and data graphics to the content · craft of details. Give one
sentence of evidence per score, naming slides. Then say which deck is stronger overall, or "tie".
Reply as JSON: {"A": {...}, "B": {...}, "overall": "A|B|tie", "why": "..."}.
Image: {pair_path}
```

- [ ] **Step 4: 还原。** 用 `key.json` 把每张拼图还原到来源，得出每个 brief 每组配对的结论。两种顺序结论一致才算"一致"，不一致算"无结论"。

### Task 7: 原因定位与报告

- [ ] **Step 1: 原因定位。** 对每个实跑记下：
  - 读了哪些设计相关文件、跳过了哪些。以 agent 的回报和 transcript 里实际的 Read 调用为准，transcript 优先。
  - 写了哪些设计相关 waiver。
  - 哪些页退回到卡片或 box。
- [ ] **Step 2: 写报告** `<desktop>/报告.html`，单文件、离线可看：
  - 每个 brief 三张 contact sheet 并排；
  - 指标表；
  - 盲评结论表；
  - 原因清单；
  - 结论：按 spec §4 Phase 1 的分支判定，写"退化"或"没退化但离基准远"，并给出 Phase 2 的修复顺序建议。
  - 写明局限：每份 1 次、基准是打磨版、Codex 式只跑 1 份。
- [ ] **Step 3:** 自己打开报告看一遍：图都显示，数字和 json 一致。然后交给用户，等用户确认再写 Phase 2 计划。
