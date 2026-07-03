# slide-maker：把论文、代码和文档，变成能直接开讲的原生 PPTX

<p align="center">
  <a href="README.md"><strong>English</strong></a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <img alt="Codex" src="https://img.shields.io/badge/Codex-supported-111827">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-supported-5b5bd6">
  <img alt="Output: editable PPTX" src="https://img.shields.io/badge/output-native_editable_PPTX-0f766e">
</p>

> 在 Codex 或 Claude Code 里聊几句，它先读懂你的材料，再交给你一份真正的 PowerPoint：每个文本、形状、图表都能点开就改，讲稿写在备注里，要点是原生的点击渐显。

<p align="center">
  <a href="https://dong845.github.io/slides_maker/"><strong>在线预览</strong></a> ·
  <a href="#最快的感受方式下载一份成品"><strong>下载成品</strong></a> ·
  <a href="#模板库"><strong>模板库</strong></a> ·
  <a href="#slide-maker-不一样在哪"><strong>不一样在哪</strong></a> ·
  <a href="#它是怎么干活的"><strong>工作流程</strong></a> ·
  <a href="#快速开始"><strong>快速开始</strong></a> ·
  <a href="#遇到问题"><strong>遇到问题</strong></a>
</p>

## 最快的感受方式：下载一份成品

**[下载「组会 / 论文汇报」这份 .pptx](templates/decks/zh/transformer-talk/template.pptx?raw=1)，在 PowerPoint 里打开。** 这是一份 15 页的《Attention Is All You Need》论文精读：论文原图直接裁自 PDF，注意力公式是可编辑的原生文本，BLEU 对比是双击就能改数字的原生图表，每页备注里有完整讲稿，放映时要点逐条渐显。

想先在浏览器里看？[在线翻页看全部 16 套](https://dong845.github.io/slides_maker/)。但判断一个 AI PPT 工具，最终还是打开它生成的文件点两下最诚实。

---

## 模板库

八个方向，中英各一套。每套都是带真实内容的完整示例 deck，不是空占位。

<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/transformer-talk"><img src="docs/assets/screenshots/preview_transformer-talk.png" alt="组会 / 论文汇报模板预览"></a><br/>
      <sub><strong>组会 / 论文汇报</strong><br/>论文精读、组会、方法综述、实验结果汇报<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/transformer-talk">在线翻页</a> · <a href="templates/decks/zh/transformer-talk/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/nvidia-overview"><img src="docs/assets/screenshots/preview_nvidia-overview.png" alt="公司 / 产品介绍模板预览"></a><br/>
      <sub><strong>公司 / 产品介绍</strong><br/>公司介绍、产品矩阵、客户沟通、融资介绍<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/nvidia-overview">在线翻页</a> · <a href="templates/decks/zh/nvidia-overview/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/nl-job-market-2026"><img src="docs/assets/screenshots/preview_nl-job-market-2026.png" alt="数据 / 市场分析模板预览"></a><br/>
      <sub><strong>数据 / 市场分析</strong><br/>行业研究、趋势解读、结构化汇报<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/nl-job-market-2026">在线翻页</a> · <a href="templates/decks/zh/nl-job-market-2026/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/solo-company-talk"><img src="docs/assets/screenshots/preview_solo-company-talk.png" alt="AI 趋势 / 个人演讲模板预览"></a><br/>
      <sub><strong>AI 趋势 / 个人演讲</strong><br/>趋势解读、个人表达、创业分享<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/solo-company-talk">在线翻页</a> · <a href="templates/decks/zh/solo-company-talk/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/kids-ai-explainer"><img src="docs/assets/screenshots/preview_kids-ai-explainer.png" alt="课程 / 知识分享模板预览"></a><br/>
      <sub><strong>课程 / 知识分享</strong><br/>课程讲解、读书分享、培训材料<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/kids-ai-explainer">在线翻页</a> · <a href="templates/decks/zh/kids-ai-explainer/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/chengdu"><img src="docs/assets/screenshots/preview_chengdu.png" alt="视觉叙事 / 文化介绍模板预览"></a><br/>
      <sub><strong>视觉叙事 / 文化介绍</strong><br/>城市、文化、活动、品牌故事<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/chengdu">在线翻页</a> · <a href="templates/decks/zh/chengdu/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/standup-history"><img src="docs/assets/screenshots/preview_standup-history.png" alt="历史 / 演变叙事模板预览"></a><br/>
      <sub><strong>历史 / 演变叙事</strong><br/>历史脉络、行业演进、时间线故事<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/standup-history">在线翻页</a> · <a href="templates/decks/zh/standup-history/template.pptx?raw=1">下载 .pptx</a></sub>
    </td>
    <td align="center" width="50%">
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/michael-jackson-king-of-pop"><img src="docs/assets/screenshots/preview_michael-jackson-king-of-pop.png" alt="人物 / 品牌故事模板预览"></a><br/>
      <sub><strong>人物 / 品牌故事</strong><br/>名人传记、品牌档案、文化回顾<br/>
      <a href="https://dong845.github.io/slides_maker/viewer.html?deck=zh/michael-jackson-king-of-pop">在线翻页</a> · <a href="templates/decks/zh/michael-jackson-king-of-pop/template.pptx?raw=1">下载 .pptx</a></sub>
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

在这个基础上，它还有四件多数工具不做的事：

- **先读懂，再动手。** 论文从第一页读到最后一页，代码库先跑通 README。每个数字、每张图对回原文，先给你一份结构稿确认，方向对了才开始画页面。它不会把摘要复制到第一页就完事。
- **交付前先过评审。** 生成后它把每一页渲染成图片，交给独立的评审 agent 挑毛病：版式挤压、对比度不足、数字和原文对不上，都会被打回重修。评审点头了才交给你。
- **能编辑的不只是文字。** 数据图优先做成原生 PPT 图表，双击改数字；公式是可编辑的原生数学文本，不是截图；论文里的图直接从 PDF 裁原图，不重画。
- **讲稿和动画一起给。** 演讲型 deck 逐页备注里有完整讲稿，要点做成 PowerPoint 原生的点击渐显。拿到手就能开讲，不用再单独写稿。

还有一条对反复改版的人最重要：每份 deck 由一个构建脚本生成，脚本和成品放在一起。想换重点、换页数、换模板，说一句话重出一版，不用一页页手工返工。

一句实话：它不承诺一步出完美成品。它承诺把最费时间的部分干掉，读材料、定结构、排版、画图、写讲稿，然后给你一份真正能继续改的文件。剩下的打磨是你的，这也正是输出原生 PPTX 的意义。

---

## 它是怎么干活的

1. **问清楚。** 给谁看、讲多久、现场讲还是发出去自读、要什么风格。你用短句回答就行，没想好就说「你定」。
2. **读材料。** 论文、文档、代码库通读，图表从 PDF 里裁原图，关键数字逐条核对，没有来源的数字不上页面。
3. **出结构稿。** 每页讲什么、放什么图、哪里配动画，先给你确认。这是改方向最便宜的时刻。
4. **生成 PPTX。** 版面由代码保证，构建时和渲染后各过一遍自动版式检查，文字溢出、元素遮挡、字体异常都会被拦下。
5. **独立评审，修到点头。** 渲染图交给评审 agent，按演讲场景的标准挑毛病，修完复查，通过才交付。成品在 `~/Downloads/<deck-name>/`。

---

## 快速开始

<p align="center">
  <img src="docs/assets/quickstart_zh.png" alt="快速开始：装一次，开聊，点选回答，确认结构稿，拿到 pptx">
</p>

### 第一步：安装

需要 **Python 3.9+** 和 **LibreOffice**（用来渲染页面预览做自动版式检查；macOS 跑 `brew install --cask libreoffice`，Linux 跑 `sudo apt install libreoffice`）。

```bash
git clone https://github.com/dong845/slides_maker.git
cd slides_maker
python3 -m pip install -r requirements.txt
python3 scripts/install_skill.py --target both
```

只用一个工具的话，把 `both` 换成 `codex` 或 `claude`。不确定缺什么？[检查命令](#遇到问题)会直接打印修复方法。

### 第二步：敲 /slide-maker，直接开聊

在 Claude Code 里，成本最低的开场是零 prompt：

```text
/slide-maker
```

访谈立即展开：一个可点选的标签页问卷（主题 · 模板 · 用途受众 · 风格语言），方向键切换、回车选择，每题都带现成选项。主题那页甚至会根据你近期的项目猜出候选。

手里有材料？一句话开场也行（Claude Code 和 Codex 都可以），它会跳过主题直接问剩下的：

```text
用 slide-maker 按 paper.pdf 做一份 PPT。
```

之后就是一段简短对话，不是写 prompt 考试：

```text
它：开工前问几件事：模板用哪套？给谁看、讲多久、现场还是自读？
    素材只有这份 PDF 吗？中文还是英文，图多字少还是均衡？

你：给导师和组会同学，12 分钟现场讲。只有 paper.pdf。
    中文，图多字少，风格你定。

它：（读完论文）结构稿来了：15 页。第 4 页整页放论文 Figure 1，
    结果页做成能改数字的原生图表……你确认方向，我就开始生成。
```

三件事记住就够：

- 短句回答就行，**「你定」永远是合法答案**。
- 回**「先给我几个风格方向」**，能拿到渲染好的风格候选挑一个。
- Codex 没有斜杠命令，问题以纯文字出现，功能完整支持，只是要打字；Claude Code 的点选体验更顺。

其他开场方式：

```text
用 slide-maker 按这个代码仓库做一份技术汇报。
```

```text
我有参考 PPT：/path/ref.pptx。参考它的视觉风格，不要它的内容，用 paper.pdf 重新做一份中文汇报。
```

材料放进当前项目，或在请求里写完整路径。什么材料都没有？给个主题就行，它先联网调研，再和你对结构。

### 可选：AI 生图

需要封面图、页面配图或整套生成式视觉时，在对话里说「需要 AI 生图」。生图走两条路，任选其一：有 Codex 订阅就免 key 直接用它的图片生成；没有的话配一个 OpenAI API key 走 API 也一样。两样都没有也不影响主流程，照常生成可编辑 PPTX。

---

## 适合什么场景

科研汇报是主场，因为它会解析论文里的问题、方法、结果、图表、表格和公式。但只要材料需要被讲清楚，它都能先给你一版能开讲、能继续改的 PPT。

| 你手里有 | 可以先做成 |
| --- | --- |
| 论文、实验结果、论文图表 | 论文精读、组会、开题、答辩、实验结果汇报 |
| 代码仓库、README、技术文档 | 代码仓库讲解、技术架构、阶段进展、工程复盘 |
| 课程材料、产品资料、市场数据 | 课程分享、产品介绍、市场分析、方案说明 |
| 参考 PPT | 换主题、换内容、重新组织表达 |

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
