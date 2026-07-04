# slide-maker：把论文、代码库、文档——或只是一个主题——变成能直接开讲的原生 PPTX

<p align="center">
  <a href="README.md"><strong>English</strong></a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <img alt="Codex" src="https://img.shields.io/badge/Codex-supported-111827">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-supported-5b5bd6">
  <img alt="Output: editable PPTX" src="https://img.shields.io/badge/output-native_editable_PPTX-0f766e">
</p>

<p align="center"><sub><a href="https://addsum.top/"><strong>增和科技 Addsum</strong></a> 出品 · 免费开源</sub></p>

> 在 Codex 或 Claude Code 里聊几句。一支各司其职的专门 **agent 团队**先读懂你的材料——**没有材料就先联网调研**——规划、生成，并在你看到之前交给独立评审过一遍。你拿到的是一份真正的 PowerPoint：每个文本、形状、图表都能点开就改，讲稿写在备注里，要点是原生的点击渐显。

<p align="center">
  <a href="https://addsumtech.github.io/slides_maker/"><strong>在线预览</strong></a> ·
  <a href="#最诚实的检验打开文件而不是截图"><strong>打开真实文件</strong></a> ·
  <a href="#模板库"><strong>模板库</strong></a> ·
  <a href="#slide-maker-不一样在哪"><strong>不一样在哪</strong></a> ·
  <a href="#它是怎么干活的"><strong>工作流程</strong></a> ·
  <a href="#快速开始"><strong>快速开始</strong></a> ·
  <a href="#遇到问题"><strong>遇到问题</strong></a>
</p>

## 最诚实的检验：打开文件，而不是截图

任何 AI PPT 工具，截图都好看——真正的问题是你拿回什么。所以打开一份，点两下：

- **[论文 / 组会 deck ↓](templates/decks/zh/transformer-talk/template.pptx?raw=1)**——一份 15 页的《Attention Is All You Need》精读。双击 BLEU 图表改数字；点进注意力公式，像改文字一样直接编辑；打开 **视图 ▸ 备注** 看完整讲稿；按放映，看要点逐条渐显。每张图都直接裁自论文 PDF。
- **[视觉 / 文化 deck ↓](templates/decks/zh/chengdu/template.pptx?raw=1)**——一整套生成式视觉：封面、分隔页、内页是同一套系统，看看能力的另一端。

想先在浏览器里翻？**[在线翻页看全部 16 套](https://addsumtech.github.io/slides_maker/)。** 但判断一个 AI PPT 工具，别看它的画廊——看它交给你的文件：打开它，点哪都能改。

---

## 模板库

八个方向，中英各一套。每套都是带真实内容的完整示例 deck，不是空占位。

<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/transformer-talk"><img src="docs/assets/screenshots/preview_transformer-talk.png" alt="组会 / 论文汇报模板预览"></a><br/>
      <sub><strong>组会 / 论文汇报</strong><br/>论文精读、组会、方法综述、实验结果汇报<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/transformer-talk">在线翻页</a> · <a href="templates/decks/zh/transformer-talk/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/nvidia-overview"><img src="docs/assets/screenshots/preview_nvidia-overview.png" alt="公司 / 产品介绍模板预览"></a><br/>
      <sub><strong>公司 / 产品介绍</strong><br/>公司介绍、产品矩阵、客户沟通、融资介绍<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/nvidia-overview">在线翻页</a> · <a href="templates/decks/zh/nvidia-overview/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/nl-job-market-2026"><img src="docs/assets/screenshots/preview_nl-job-market-2026.png" alt="数据 / 市场分析模板预览"></a><br/>
      <sub><strong>数据 / 市场分析</strong><br/>行业研究、趋势解读、结构化汇报<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/nl-job-market-2026">在线翻页</a> · <a href="templates/decks/zh/nl-job-market-2026/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/solo-company-talk"><img src="docs/assets/screenshots/preview_solo-company-talk.png" alt="AI 趋势 / 个人演讲模板预览"></a><br/>
      <sub><strong>AI 趋势 / 个人演讲</strong><br/>趋势解读、个人表达、创业分享<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/solo-company-talk">在线翻页</a> · <a href="templates/decks/zh/solo-company-talk/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/kids-ai-explainer"><img src="docs/assets/screenshots/preview_kids-ai-explainer.png" alt="课程 / 知识分享模板预览"></a><br/>
      <sub><strong>课程 / 知识分享</strong><br/>课程讲解、读书分享、培训材料<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/kids-ai-explainer">在线翻页</a> · <a href="templates/decks/zh/kids-ai-explainer/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/chengdu"><img src="docs/assets/screenshots/preview_chengdu.png" alt="视觉叙事 / 文化介绍模板预览"></a><br/>
      <sub><strong>视觉叙事 / 文化介绍</strong><br/>城市、文化、活动、品牌故事<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/chengdu">在线翻页</a> · <a href="templates/decks/zh/chengdu/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/standup-history"><img src="docs/assets/screenshots/preview_standup-history.png" alt="历史 / 演变叙事模板预览"></a><br/>
      <sub><strong>历史 / 演变叙事</strong><br/>历史脉络、行业演进、时间线故事<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/standup-history">在线翻页</a> · <a href="templates/decks/zh/standup-history/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/michael-jackson-king-of-pop"><img src="docs/assets/screenshots/preview_michael-jackson-king-of-pop.png" alt="人物 / 品牌故事模板预览"></a><br/>
      <sub><strong>人物 / 品牌故事</strong><br/>名人传记、品牌档案、文化回顾<br/>
      <a href="https://addsumtech.github.io/slides_maker/viewer.html?deck=zh/michael-jackson-king-of-pop">在线翻页</a> · <a href="templates/decks/zh/michael-jackson-king-of-pop/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
  </tr>
</table>

<p align="center"><sub>英文版在 <a href="templates/decks/">templates/decks/en/</a>，预览见 <a href="README.md">English README</a>。</sub></p>

---

## 模板怎么用

模板库在仓库的 `templates/decks/` 下，中文在 `zh/`，英文在 `en/`。两种用法：

**用法一：直接指路（最简单）。** 把模板路径写进需求：

```text
用 slide-maker，参考 templates/decks/zh/nvidia-overview/template.pptx 的风格，
按我的 product.md 做一份产品介绍。
```

它会解析这份模板的版式和视觉系统，套用到你的内容上。

**用法二：注册成常驻模板。** 把常用的模板复制到本机模板注册表，之后每次做 PPT 它都会自动列为可选项：

```bash
# Claude Code 用户
cp -r templates/decks/zh/nvidia-overview ~/.claude/slide-templates/nvidia-overview

# Codex 用户
cp -r templates/decks/zh/nvidia-overview ~/.codex/slide-templates/nvidia-overview
```

做中文 deck 用 `zh/` 的模板，英文 deck 用 `en/` 的，两套的版式一致，文案语言不同。


---

## slide-maker 不一样在哪

市面上的 AI PPT 工具大致分四类，slide-maker 只做最后一类：

| 类型 | 输出 | 在 PowerPoint 里能逐元素编辑吗 |
| --- | --- | :---: |
| 模板填空 | 固定模板里塞内容 | 部分能，受模板限制 |
| 图片式 | 每页一张大图打包成 PPTX | 不能，每页是一张图 |
| HTML 网页式 | 浏览器里的幻灯片 | 不是 PPTX |
| **原生可编辑（slide-maker）** | **真实文本框、形状、原生图表** | **能，点哪改哪** |

### 一支各司其职的 agent 小团队——分工不同，立场也不同

slide-maker 不是一个 prompt 包办一切，而是一组各有专职的 **agent**，每个只做一件事，并刻意保持独立——不让同一个「人」既搭 deck 又给它打分：

- **content-planner（内容规划）**——牵头的策划兼设计。它做了别人没做的通读，决定每页讲什么、哪张图或图表放哪、deck 的节奏、以及动画到底值不值得用。因为整份 deck 从一个脑子里流出来，它是一个连贯的论证，而不是一堆散页。
- **critic（评审）**——一个没参与搭建的独立评审。它对着**渲染出来的**页面按演讲目的挑毛病——版式挤压、对比度不足、数字和原文对不上——统统打回重修。正因为它对草稿没有立场，才够诚实。
- **arbiter（仲裁）**——高风险 deck 里的第二道独立复核：动手改之前先确认评审提的问题是真的，让循环修的是真问题，而不是噪声。
- **asset-prep（素材准备）**——一个构建期执行者，在你确认结构稿之后**并行**把计划里的素材（裁图、公式图、示意图）做出来——不做任何设计决策——所以再大的 deck 也生成得快。

分工本身就是关键：建设性的规划者提议，独立的评审者裁决。这就是为什么你拿到的 deck，已经过了一轮你自己不必再跑的评审。

在这个基础上，它还有四件多数工具不做的事：

- **先读懂，再动手。** 论文从第一页读到最后一页，代码库先跑通 README，**什么材料都没有时先联网调研主题**。每个数字、每张图对回来源，先给你一份结构稿确认，方向对了才开始画页面。它不会把摘要复制到第一页就完事。
- **交付前先过评审。** 生成后它把每一页渲染成图片，交给独立的评审 agent 挑毛病：版式挤压、对比度不足、数字和原文对不上，都会被打回重修。评审点头了才交给你。
- **能编辑的不只是文字。** 数据图优先做成原生 PPT 图表，双击改数字；公式是可编辑的原生数学文本，不是截图；论文里的图直接从 PDF 裁原图，不重画。
- **讲稿和动画一起给。** 演讲型 deck 逐页备注里有完整讲稿，要点做成 PowerPoint 原生的点击渐显。拿到手就能开讲，不用再单独写稿。

还有一条对反复改版的人最重要：每份 deck 由一个构建脚本生成，脚本和成品放在一起。想换重点、换页数、换模板，说一句话重出一版，不用一页页手工返工。

一句实话：它不承诺一步出完美成品。它承诺把最费时间的部分干掉，读材料、定结构、排版、画图、写讲稿，然后给你一份真正能继续改的文件。剩下的打磨是你的，这也正是输出原生 PPTX 的意义。

---

## 它是怎么干活的

1. **问清楚。** 给谁看、讲多久、现场讲还是发出去自读、要什么风格。你用短句回答就行，没想好就说「你定」。什么材料都没有？给个主题，它会先联网调研再动手。
2. **读材料（或联网调研）。** 论文、文档、代码库通读，图表从 PDF 里裁原图，关键数字逐条核对，没有来源的数字不上页面。只有一个主题时，它先联网调研截至当下的最新信息，再据此工作。
3. **content-planner 出结构稿。** 规划 agent 把通读的结果变成逐页方案：每页讲什么、放什么图、哪里配动画、整体怎么走。先给你确认——这是改方向最便宜的时刻。
4. **生成 PPTX。** 版面由代码保证，构建时和渲染后各过一遍自动版式检查，文字溢出、元素遮挡、字体异常都会被拦下。
5. **独立评审，修到点头。** 渲染图交给评审 agent（高风险 deck 再加一个 arbiter 复核），按演讲场景的标准挑毛病，修完复查，通过才交付到 `~/Downloads/<deck-name>/`。
6. **用自然语言微调。** 还不完美？在对话里说一句就行——「第 7 页改成图表」「删掉引言」「配色暖一点」「压到 10 页」「备注短一点」——它会用同一份脚本干净重出一版。不用手工挪框，一直改到满意为止。

**成本说明：** 工具免费，唯一开销是你自己的 AI 用量。读材料、定结构、生成这段很便宜；贵的是独立评审环节，且按场合分档：内部快速 deck 走轻量单检，会议级 deck 的多评审面板可能消耗几十万 token。随时可以说「轻量评审」或「跳过评审」，用打磨换成本。

---

## 快速开始

<p align="center">
  <img src="docs/assets/quickstart_zh.png" alt="快速开始：装一次、敲 /slide-maker、读材料或联网调研、确认结构稿、生成加独立评审、拿到 pptx 再微调">
</p>

### 第一步：安装

需要 **Python 3.9+**、**LibreOffice**（渲染页面预览做自动版式检查），以及**任一 SVG 栅格化器**给图标用（librsvg、cairosvg 或任意 Chrome 系浏览器）。

| 系统 | LibreOffice | 图标栅格化 |
| --- | --- | --- |
| macOS | `brew install --cask libreoffice` | `brew install librsvg` |
| Linux | `sudo apt install libreoffice` | `sudo apt install librsvg2-bin` |
| Windows | `winget install TheDocumentFoundation.LibreOffice` | 装好 Chrome 或 Edge（无头调用） |

**Windows 说明：** 流水线是跨平台 Python，CI 在 Linux 上跑，日常开发在 macOS。遇到 Windows 特有问题，下方的 `check_env.py` 会指出缺什么；欢迎带报错开 issue。

```bash
git clone https://github.com/addsumtech/slides_maker.git
cd slides_maker
python3 -m pip install -r requirements.txt
python3 scripts/install_skill.py --target both
```

只用一个工具的话，把 `both` 换成 `codex` 或 `claude`。不确定缺什么？[检查命令](#遇到问题)会直接打印修复方法。

### 第二步：唤起技能，逐题回答——最推荐的方式

最稳、最好的结果，来自**唤起技能并逐题回答它的简短访谈**：

```text
/slide-maker
```

访谈会展开成一个可点选的标签页问卷（主题 · 模板 · 用途受众 · 风格语言）：方向键切换、回车选择，每题都带现成选项，主题那页甚至会根据你近期的项目猜出候选。**逐题回答，正是让 deck 变成「你的」而不是通用款的关键**——受众、时长、现场还是自读、密度、语言、观感，都会影响方案。短句回答就行，**「你定」永远是合法答案**——但让它「问」，好过让它「猜」。

**赶时间？一句话开场也行——但请把它当捷径，而不是最佳路径：**

```text
用 slide-maker 按 paper.pdf 做一份 PPT。
```

它直接从你的文件开始、跳过主题问题，很方便——但每一个你没回答的问题，都会变成它必须替你做的假设，所以之后你通常要花更多时间微调。**deck 重要时，就把访谈答完。**（Codex 里没有斜杠命令，同样的问题以纯文字出现，功能完整支持，只是要打字；Claude Code 的点选体验更顺。）

无论哪种开场，之后都是一段简短对话，不是写 prompt 考试：

```text
它：开工前问几件事：模板用哪套？给谁看、讲多久、现场还是自读？
    素材只有这份 PDF 吗？中文还是英文，图多字少还是均衡？

你：给导师和组会同学，12 分钟现场讲。只有 paper.pdf。
    中文，图多字少，风格你定。

它：（读完论文）结构稿来了：15 页。第 4 页整页放论文 Figure 1，
    结果页做成能改数字的原生图表……你确认方向，我就开始生成。
```

还有两点值得知道：

- 回**「先给我几个风格方向」**，能拿到渲染好的风格候选挑一个，再开始正式生成。
- 材料放进当前项目，或在请求里写完整路径。**什么材料都没有？** 给个主题就行，它先联网调研，再和你对结构。

其他开场方式：

```text
用 slide-maker 按这个代码仓库做一份技术汇报。
```

```text
我有参考 PPT：/path/ref.pptx。参考它的视觉风格，不要它的内容，用 paper.pdf 重新做一份中文汇报。
```

### 可选：AI 生图

需要封面图、页面配图或整套生成式视觉时，在对话里说「需要 AI 生图」。生图走两条路，任选其一：有 Codex 订阅就免 key 直接用它的图片生成；没有的话配一个 OpenAI API key 走 API 也一样。两样都没有也不影响主流程，照常生成可编辑 PPTX。

---

## 适合什么场景

科研汇报是主场，因为它会解析论文里的问题、方法、结果、图表、表格和公式。但只要材料需要被讲清楚——或者你手里只有一个主题、还没有材料——它都能先给你一版能开讲、能继续改的 PPT。

| 你手里有 | 可以先做成 |
| --- | --- |
| 论文、实验结果、论文图表 | 组会与论文精读、会议口头报告、海报、开题、答辩、实验结果汇报 |
| 代码仓库、README、技术文档 | 组会、代码仓库讲解、技术架构、阶段进展、工程复盘 |
| 课程材料、产品资料、市场数据 | 课程分享、产品介绍、市场分析、方案说明 |
| 什么都没有——只有一个主题 | 给它一个主题；agent 团队联网调研截至当下的最新信息，和你对好结构，再从零把 deck 做出来 |
| 参考 PPT | 换主题、换内容、重新组织表达——用它的观感，你的材料 |

---

## 遇到问题

生成 PPT 或渲染预览报错时，按你的环境跑检查命令，多数问题是 Python 依赖或 LibreOffice 没装好：

```bash
# Codex
python3 ~/.codex/skills/slide-maker/scripts/check_env.py

# Claude Code
python3 ~/.claude/skills/slide-maker/scripts/check_env.py
```

缺什么它会直接打印修复命令。依赖装完还报错，欢迎开 issue，带上报错输出。

---

## 开源协议

[MIT](LICENSE)
