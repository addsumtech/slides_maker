# slide-maker：把论文、代码库、文档，甚至只是一个主题，变成能直接开讲的原生 PPTX

<p align="center">
  <a href="README.md"><strong>English</strong></a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <img alt="Codex" src="https://img.shields.io/badge/Codex-supported-111827">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-supported-5b5bd6">
  <img alt="Output: editable PPTX" src="https://img.shields.io/badge/output-native_editable_PPTX-0f766e">
</p>

<p align="center"><sub><a href="https://addsum.top/cn/"><strong>增和科技 Addsum</strong></a> 出品 · 免费开源</sub></p>

> **一个会读你真实材料、绝不编造数字、输出真正可编辑的原生 PowerPoint、并且要等独立评审点头才交付的 AI 做 PPT 工具。**

在 Codex 或 Claude Code 里聊几句。它不是一句 prompt 瞎猜幻灯片:一支各司其职的 **agent 团队**先读懂你的论文 / 代码 / 文档(没有材料就先联网调研),规划故事线,围绕它设计每一页,生成一份真正的 `.pptx`,再交给独立评审过一遍,才交到你手上。

多数 AI-PPT 工具都在拼"几秒出漂亮 PPT"。slide-maker 优化的是——当这份 deck 是**你要拿去讲、要负责**的时候——真正重要的四件事:

- 🔍 **读你的材料,而不是编造。** 每个数字、每张图都溯源到你的材料;绝不为了填满一页瞎编一个统计数(这是所有"把主题铺开"类工具的通病——某流行助手把真实的 *12%* 印成了 *43%*)。
- ✏️ **一份真 PowerPoint,不是截图。** 每个文本框、形状、原生图表、公式都是点开就改的对象——**没有任何**东西被压成图片(很多"导出 PPTX"的工具,会悄悄把三分之一的页面变成改不动的图)。
- 🧑‍⚖️ **交付前先过审。** 不可协商的 actor-critic 闭环:一个**独立**评审去挑毛病——版式挤压、对比度不足、数字和原文对不上——再打回修正。不是作者模型给自己批卷。
- 🎨 **围绕你的内容设计,任意语言。** 一页页现场编排——匹配你的模板或现设计一套干净的——研究报告、答辩、产品 pitch 皆可。不是把你的文字倒进现成版式。

<sub>原生可编辑 PPTX 如今已是基本盘(不少工具都能做)。稀缺的是**可编辑 + 溯源不编造 + 审校过 + 每 deck 定制**——四者合一,在一份归你所有的文件里。诚实的边界:没有零配置云端、没有分享链接、没有动态网页背景——它做的是一个**本地生成的文件**,能在真 PowerPoint/Keynote 里干净打开、编辑。详见[不一样在哪](#slide-maker-不一样在哪)。</sub>

<p align="center">
  <a href="https://slides.addsum.top/cn/"><strong>视频介绍</strong></a> ·
  <a href="#模板库"><strong>模板库</strong></a> ·
  <a href="#slide-maker-不一样在哪"><strong>不一样在哪</strong></a> ·
  <a href="#它是怎么干活的"><strong>工作流程</strong></a> ·
  <a href="#快速开始"><strong>快速开始</strong></a> ·
  <a href="#遇到问题"><strong>遇到问题</strong></a>
</p>


## 模板库

八个方向，中英各一套。每套都是带真实内容的完整示例 deck，不是空占位。

<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/transformer-talk"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_transformer-talk.png" alt="组会 / 论文汇报模板预览"></a><br/>
      <sub><strong>组会 / 论文汇报</strong><br/>论文精读、组会、方法综述、实验结果汇报<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/transformer-talk">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/transformer-talk/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nvidia-overview"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_nvidia-overview.png" alt="公司 / 产品介绍模板预览"></a><br/>
      <sub><strong>公司 / 产品介绍</strong><br/>公司介绍、产品矩阵、客户沟通、融资介绍<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nvidia-overview">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/nvidia-overview/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nl-job-market-2026"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_nl-job-market-2026.png" alt="数据 / 市场分析模板预览"></a><br/>
      <sub><strong>数据 / 市场分析</strong><br/>行业研究、趋势解读、结构化汇报<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nl-job-market-2026">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/nl-job-market-2026/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/solo-company-talk"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_solo-company-talk.png" alt="AI 趋势 / 个人演讲模板预览"></a><br/>
      <sub><strong>AI 趋势 / 个人演讲</strong><br/>趋势解读、个人表达、创业分享<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/solo-company-talk">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/solo-company-talk/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/kids-ai-explainer"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_kids-ai-explainer.png" alt="课程 / 知识分享模板预览"></a><br/>
      <sub><strong>课程 / 知识分享</strong><br/>课程讲解、读书分享、培训材料<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/kids-ai-explainer">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/kids-ai-explainer/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/chengdu"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_chengdu.png" alt="视觉叙事 / 文化介绍模板预览"></a><br/>
      <sub><strong>视觉叙事 / 文化介绍</strong><br/>城市、文化、活动、品牌故事<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/chengdu">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/chengdu/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/standup-history"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_standup-history.png" alt="历史 / 演变叙事模板预览"></a><br/>
      <sub><strong>历史 / 演变叙事</strong><br/>历史脉络、行业演进、时间线故事<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/standup-history">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/standup-history/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/michael-jackson-king-of-pop"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_michael-jackson-king-of-pop.png" alt="人物 / 品牌故事模板预览"></a><br/>
      <sub><strong>人物 / 品牌故事</strong><br/>名人传记、品牌档案、文化回顾<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/michael-jackson-king-of-pop">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/michael-jackson-king-of-pop/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
</table>

<p align="center"><sub>英文版在 <a href="https://github.com/addsumtech/slides_maker-site/tree/main/templates/decks/en">templates/decks/en/</a>，预览见 <a href="README.md">English README</a>。</sub></p>

---

## 模板怎么用

模板库在独立仓库 [slides_maker-site](https://github.com/addsumtech/slides_maker-site) 的 `templates/decks/` 下，中文在 `zh/`，英文在 `en/`。先取一次：

```bash
git clone --depth 1 https://github.com/addsumtech/slides_maker-site.git
```

两种用法：

**用法一：直接指路（最简单）。** 把模板路径写进需求：

```text
用 slide-maker，参考 slides_maker-site/templates/decks/zh/nvidia-overview/template.pptx 的风格，
按我的 product.md 做一份产品介绍。
```

它会解析这份模板的版式和视觉系统，套用到你的内容上。

**用法二：注册成常驻模板。** 把常用的模板复制到本机模板注册表，之后每次做 PPT 它都会自动列为可选项：

```bash
# Claude Code 用户
cp -r slides_maker-site/templates/decks/zh/nvidia-overview ~/.claude/slide-templates/nvidia-overview

# Codex 用户
cp -r slides_maker-site/templates/decks/zh/nvidia-overview ~/.codex/slide-templates/nvidia-overview
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

这张表说的是**格式**。如今已有若干新工具也能输出原生可编辑 PPTX——所以"可编辑"本身不再是区分点。真正让 slide-maker 与众不同的是**它拿这个格式做了什么**:读你的真实材料、拒绝编造;交付前先过独立评审;每一页围绕你的内容编排,而不是把文字倒进模板。本节接下来就讲这三件,依次展开。

### 一支各司其职的 agent 小团队：分工不同，立场也不同

slide-maker 不是一个 prompt 包办一切，而是一组各有专职的 **agent**，每个只做一件事，并刻意保持独立，不让同一个「人」既搭 deck 又给它打分：

- **content-planner（内容规划）**：牵头的主编。它负责把材料真正通读一遍，决定每页**讲什么**——记忆点、证据、叙事弧线——每个数字都溯源，并有一道覆盖门保证材料里的关键点不会被悄悄弄丢（要么上页面，要么明确标注「有意割舍」）。整条故事线出自同一个脑子，所以是一条连贯的论证，而不是一堆散页。
- **slide-design（美术总监）**：另一个独立的脑子，决定批准后的故事**长什么样**——每页的视觉形式、配色（一种颜色全 deck 只表达一个含义）、字体、节奏、图标、以及点击渐显放在哪才真正值得。它先从内容出发在白纸上构想，再去打开组件库，所以出来的是「被设计过」，而不是「套模板」。
- **critic（评审）**：一个没参与搭建的独立评审。它对着**渲染出来的**页面从两个镜头挑毛病——内容忠实度（数字和原文对不上、关键点丢失）和设计（版式挤压、对比度不足、合规但死板），统统打回重修。正因为它对草稿没有立场，才够诚实。
- **arbiter（仲裁）**：重要场合的 deck 会加这道二次复核：动手改之前，先确认评审挑的毛病是真毛病，修的是真问题，而不是噪声。
- **asset-prep（素材准备）**：构建期的执行工。你确认设计方案之后，它**并行**把计划里的素材（裁图、公式图、生成插画、图标）做出来，不做任何设计决策，所以再大的 deck 也出得快。

分工本身就是设计：规划者只管提方案，评审者只管挑毛病。所以 deck 到你手上时，已经替你过完了一轮评审。

在这个基础上，它还有四件多数工具不做的事：

- **先读懂，再动手。** 论文从第一页读到最后一页，代码库先跑通 README，**什么材料都没有时先联网调研主题**。每个数字、每张图对回来源，先给你一份结构稿确认，方向对了才开始画页面。它不会把摘要复制到第一页就完事。
- **交付前先过评审。** 生成后它把每一页渲染成图片，交给独立的评审 agent 挑毛病：版式挤压、对比度不足、数字和原文对不上，都会被打回重修。评审点头了才交给你。
- **能编辑的不只是文字。** 数据图优先做成原生 PPT 图表，双击改数字；公式默认是可编辑的原生数学文本，不是截图（仅分式、矩阵等二维排版回退为渲染图）；论文里的图直接从 PDF 裁原图，不重画。
- **讲稿和动画一起给。** 演讲型 deck 逐页备注里有完整讲稿，要点做成 PowerPoint 原生的点击渐显。拿到手就能开讲，不用再单独写稿。

还有一条对反复改版的人最重要：每份 deck 由一个构建脚本生成，脚本和成品放在一起。想换重点、换页数、换模板，说一句话重出一版，不用一页页手工返工。

而且它会**越用越像你的**。当你在多个 deck 上把同一个偏好朝同一方向反复调整——数据鲜亮、边框克制、不要模板味的卡片、公式排版化——它会把这记成一份便携的口味档案：一个放在注册表根、归你所有的纯文本文件，可逐行查看、编辑、删除。之后的 deck 把它当默认读取,你就不用一遍遍重教。它**只做播种**——当下这个 deck 你说的话永远优先——全新用户则是一张白纸,不预设任何风格。

一句实话：它不承诺一步出完美成品。它承诺把最费时间的部分干掉，读材料、定结构、排版、画图、写讲稿，然后给你一份真正能继续改的文件。剩下的打磨是你的，这也正是输出原生 PPTX 的意义。

---

## 它是怎么干活的

1. **问清楚。** 给谁看、讲多久、现场讲还是发出去自读、要什么风格。你用短句回答就行，没想好就说「你定」——它会自己选出稳妥的答案并**在动手前先贴出来**，选错了你扫一眼就能否决，不用等一版重建（只有主题、素材这类只有你知道的信息仍然要问）。什么材料都没有？给个主题，它会先联网调研再动手。
2. **读材料（或联网调研）。** 论文、文档、代码库通读，图表从 PDF 里裁原图，关键数字逐条核对，没有来源的数字不上页面。只有一个主题时，它先联网调研最新信息，再动手。
3. **先确认故事，再确认观感——都在对话里。** content-planner 先贴一张紧凑的逐页表（每页讲什么、靠哪张图、整体怎么走）；你确认故事后，美术总监再以同样方式贴出设计方案（观感、配色、每页形式、动效）。两次快速确认，正好落在改方向最便宜的两个时刻——不用打开任何计划文件。
4. **生成 PPTX。** 版面由代码保证，构建时和渲染后各过一遍自动版式检查，文字溢出、元素遮挡、字体异常都会被拦下。
5. **独立评审，修到点头。** 渲染图交给评审 agent（重要场合再加一道 arbiter 复核），按演讲场景的标准挑毛病，修完复查，通过才交付到 `~/Downloads/<deck-name>/`。
6. **用自然语言微调。** 还不完美？在对话里说一句就行：「第 7 页改成图表」「删掉引言」「配色暖一点」「压到 10 页」「备注短一点」，它会用同一份脚本干净重出一版。不用自己进 PPT 里逐页拖框调版式，一直改到满意为止。

**成本说明：** 工具免费，唯一开销是你自己的 AI 用量。读材料、定结构、生成这段很便宜；贵的是独立评审环节，且按场合分档：内部快速 deck 走轻量单检，会议级 deck 的多评审面板可能消耗几十万 token。随时可以说「轻量评审」，用打磨换成本——独立评审这道关不会取消，只会做轻。

---

## 快速开始

<p align="center">
  <img src="https://slides.addsum.top/docs/assets/quickstart_zh.png" alt="快速开始：装一次、敲 /slide-maker、读材料或联网调研、确认结构稿、生成加独立评审、拿到 pptx 再微调">
</p>

### 第一步：安装

slide-maker 依赖三样系统工具：**Python 3.9+**、**LibreOffice**（渲染页面预览做自动版式检查），以及**任一 SVG 栅格化器**给图标用（librsvg、cairosvg 或任意 Chrome 系浏览器）。按你的系统装：

| 系统 | LibreOffice | 图标栅格化 |
| --- | --- | --- |
| macOS | `brew install --cask libreoffice` | `brew install librsvg` |
| Linux | `sudo apt install libreoffice` | `sudo apt install librsvg2-bin` |
| Windows | `winget install TheDocumentFoundation.LibreOffice` | 装好 Chrome 或 Edge（无头调用） |

（Windows 一样能用，只是我们测得少；真碰到环境问题，先跑下面的 `check_env.py` 自查，搞不定就带报错开 issue。）

**这些系统依赖就位后，再把 slide-maker 本体装进来。** 下面这四行会克隆仓库、装好它的 Python 包、并注册成技能：

```bash
git clone --depth 1 https://github.com/addsumtech/slides_maker.git
cd slides_maker
python3 -m pip install -r skills/slide-maker/requirements.txt
python3 skills/slide-maker/scripts/install_skill.py --target both
```

只用一个工具的话，把 `both` 换成 `codex` 或 `claude`。不确定缺什么？[检查命令](#遇到问题)会直接打印修复方法。

**想一行搞定？用 [`npx skills`](https://github.com/vercel-labs/skills) 只装技能本体**（免克隆，约 1.1 MB）：

```bash
npx skills add addsumtech/slides_maker
```

它会先问装到哪个 agent、哪个范围。技能位于仓库的 `skills/slide-maker/` 下，而画廊和演示站在独立仓库 [slides_maker-site](https://github.com/addsumtech/slides_maker-site)，主仓库没有大文件，所以安装小而快。加 `-g` 装到全局（所有项目），加 `-a claude-code`（或 `-a codex`）跳过 agent 选择，加 `-y` 全程免确认。仍需上面的运行依赖：LibreOffice、一个 SVG 栅格化器，以及 `python3 -m pip install -r skills/slide-maker/requirements.txt`。

**用 Claude Code 的话，也可以把它当插件装**，之后用普通插件命令就能更新：

```text
/plugin marketplace add addsumtech/slides_maker
/plugin install slide-maker@slides-maker
```

装的是同一个技能，只是交给 Claude Code 的插件系统管理，而不是复制到你的技能目录。上面那几个运行依赖照样需要。

### 第二步：敲 /slide-maker，逐题回答（最推荐）

效果最稳的方式，是**把它的简短访谈逐题答完**：

```text
/slide-maker
```

访谈会展开成一个可点选的标签页问卷（主题 · 模板 · 用途受众 · 风格语言）：方向键切换、回车选择，每题都带现成选项。它也认得老用户：你存过的模板、做过的主题会收敛成一个「用我之前的」选项放在通用选项旁边，选中才展开清单。**逐题回答，正是让 deck 变成「你的」而不是通用款的关键**：受众、时长、现场还是自读、密度、语言、观感，都会影响方案。短句回答就行，**「你定」永远是合法答案**。

**赶时间？一句话开场也行，但请把它当捷径，而不是最佳路径：**

```text
用 slide-maker 按 paper.pdf 做一份 PPT。
```

它直接从你的文件开始、跳过主题那一问，很方便。但每一个你没回答的问题，都会变成它必须替你做的假设，所以之后你通常要花更多时间微调。**deck 重要时，就把访谈答完。**（Codex 里没有斜杠命令，同样的问题以纯文字出现，功能完整支持，只是要打字；Claude Code 的点选体验更顺。）

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

- 回一句 **「先给我几个风格方向」**，就能拿到几个渲染好的风格候选，挑一个再正式生成。
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

科研汇报是主场，因为它会解析论文里的问题、方法、结果、图表、表格和公式。但只要材料需要被讲清楚（或者你手里只有一个主题、还没有材料），它都能先给你一版能开讲、能继续改的 PPT。

| 你手里有 | 可以先做成 |
| --- | --- |
| 论文、实验结果、论文图表 | 组会与论文精读、会议口头报告、海报、开题、答辩、实验结果汇报 |
| 代码仓库、README、技术文档 | 组会、代码仓库讲解、技术架构、阶段进展、工程复盘 |
| 课程材料、产品资料、市场数据 | 课程分享、产品介绍、市场分析、方案说明 |
| 什么都没有，只有一个主题 | 给它一个主题；agent 团队联网调研最新信息，和你对好结构，再从零做出整份 deck |
| 参考 PPT | 换主题、换内容、重新组织表达：用它的观感，你的材料 |

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

## Star 趋势

<p align="center">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/addsumtech/slides_maker/main/docs/assets/star_history_dark.png" />
      <img alt="addsumtech/slides_maker 的 Star 趋势" src="https://raw.githubusercontent.com/addsumtech/slides_maker/main/docs/assets/star_history.png" width="720" />
  </picture>
</p>

---

## 开源协议

[MIT](LICENSE)
