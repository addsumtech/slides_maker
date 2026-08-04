# slide-maker：把论文、代码库、文档，甚至只是一个主题，变成能直接开讲的原生 PPTX

<p align="center">
  <a href="README.md"><strong>English</strong></a>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <img alt="Codex" src="https://img.shields.io/badge/Codex-supported-111827">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude_Code-supported-5b5bd6">
  <img alt="Output: editable PPTX" src="https://img.shields.io/badge/output-native_editable_PPTX-0f766e">
  <a href="https://skillhub.cloud.tencent.com/skills/slides-maker"><img alt="腾讯 SkillHub" src="https://img.shields.io/badge/%E8%85%BE%E8%AE%AF_SkillHub-%E7%AB%8B%E5%8D%B3%E8%8E%B7%E5%8F%96-2f6feb"></a>
  <a href="https://xiaping.coze.com/skill/c0136d99-50d0-4f05-909a-f78fa4be7104"><img alt="Coze" src="https://img.shields.io/badge/Coze-%E7%AB%8B%E5%8D%B3%E8%8E%B7%E5%8F%96-6653f5"></a>
</p>

<p align="center">
  <a href="https://clawhub.ai/dong845/skills/slide-maker"><img alt="ClawHub" src="docs/badges/clawhub_cn.svg"></a>
  <a href="https://chatgpt.com/g/g-6a5b41f0a33881918be69e8b10f8b4ff-slide-maker-gpt"><img alt="ChatGPT GPT 商店" src="https://img.shields.io/badge/GPT_Store-slide--maker_(addsum_studio)-10a37f"></a>
</p>

<p align="center"><sub><a href="https://addsum.top/cn/"><strong>增和科技 Addsum</strong></a> 出品 · 免费开源</sub></p>

> **一个会读你真实材料、绝不编造数字、输出真正可编辑的原生 PowerPoint、并且要等独立评审点头才交付的 AI 做 PPT 工具。**

在 Codex 或 Claude Code 里聊几句就行，也可以**零安装**，直接在 ChatGPT 里用 [slide-maker (addsum studio)](https://chatgpt.com/g/g-6a5b41f0a33881918be69e8b10f8b4ff-slide-maker-gpt)。它不是一句 prompt 瞎猜幻灯片：一支各司其职的 **agent 团队**先读懂你的论文、代码、文档（没有材料就先联网调研），规划故事线，围绕它设计每一页，生成一份真正的 `.pptx`，再交给独立评审过一遍，才交到你手上。

多数 AI-PPT 工具都在拼「几秒出漂亮 PPT」。但当这份 deck 是**你要拿去讲、要负责**的东西时，真正重要的是另外四件事，slide-maker 做的就是这四件：

- 🔍 **读你的材料，不编造。** 每个数字、每张图都能溯源到你的材料；绝不为了填满一页瞎编一个统计数字（这是所有「把主题铺开」类工具的通病，某个流行助手就把真实的 **12%** 印成了 **43%**）。
- ✏️ **一份真 PowerPoint，不是截图。** 每个文本框、形状、原生图表、公式都是点开就能改的对象，**没有任何**东西被压成图片（很多号称「导出 PPTX」的工具，会悄悄把三分之一的页面变成改不动的图）。
- 🧑‍⚖️ **交付前先过审。** 一道不能跳过的 actor-critic 闭环：由一个**独立**评审去挑毛病，版式挤压、对比度不足、数字和原文对不上，挑出来就打回重修。不是作者模型给自己批卷。
- 🎨 **围绕你的内容设计，任意语言、任意画布。** 每一页都是现场编排出来的，你有模板就匹配你的模板，没有就现设计一套干净的，研究报告、答辩、产品 pitch 都行，不是把你的文字倒进现成版式。而且不止 16:9：同一套技能可以重排成 4:3、方形 1:1、小红书 3:4 图文卡、9:16 竖版封面、A4 打印一页纸，每种画布都有自己的安全区和排版逻辑。

原生可编辑 PPTX 如今已是基本盘（不少工具都能做）。稀缺的是**可编辑、溯源不编造、审校过、每份 deck 单独设计**这四件事同时成立，而且都落在一份归你所有的文件里。也把话说在前面：它没有零配置云端、没有分享链接、没有动态网页背景，它交付的是一个**本地生成的文件**，能在真的 PowerPoint 和 Keynote 里干净打开、继续编辑。详见[不一样在哪](#slide-maker-不一样在哪)。

<p align="center">
  <a href="https://slides.addsum.top/cn/"><strong>视频介绍</strong></a> ·
  <a href="#模板库"><strong>模板库</strong></a> ·
  <a href="#slide-maker-不一样在哪"><strong>不一样在哪</strong></a> ·
  <a href="#它是怎么干活的"><strong>工作流程</strong></a> ·
  <a href="#快速开始"><strong>快速开始</strong></a> ·
  <a href="#遇到问题"><strong>遇到问题</strong></a>
</p>


## 模板库

十二个方向，中英各一套。每套都是带真实内容的完整示例 deck，不是空占位。

<table>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/quarterly-review"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_quarterly-review.png" alt="季度复盘 / 经营汇报模板预览"></a><br/>
      <sub><strong>季度复盘 / 经营汇报</strong><br/>季度复盘、经营汇报、数据看板、管理层沟通<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/quarterly-review">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/quarterly-review/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/chengdu"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_chengdu.png" alt="视觉叙事 / 文化介绍模板预览"></a><br/>
      <sub><strong>视觉叙事 / 文化介绍</strong><br/>城市、文化、活动、品牌故事<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/chengdu">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/chengdu/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/transformer-talk"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_transformer-talk.png" alt="组会 / 论文汇报模板预览"></a><br/>
      <sub><strong>组会 / 论文汇报</strong><br/>论文精读、组会、方法综述、实验结果汇报<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/transformer-talk">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/transformer-talk/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/product-launch"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_product-launch.png" alt="新品发布 / 产品上线模板预览"></a><br/>
      <sub><strong>新品发布 / 产品上线</strong><br/>发布会、新品介绍、产品上线沟通<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/product-launch">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/product-launch/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nvidia-overview"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_nvidia-overview.png" alt="公司 / 产品介绍模板预览"></a><br/>
      <sub><strong>公司 / 产品介绍</strong><br/>公司介绍、产品矩阵、客户沟通、融资介绍<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nvidia-overview">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/nvidia-overview/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/standup-history"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_standup-history.png" alt="历史 / 演变叙事模板预览"></a><br/>
      <sub><strong>历史 / 演变叙事</strong><br/>历史脉络、行业演进、时间线故事<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/standup-history">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/standup-history/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/startup-pitch"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_startup-pitch.png" alt="融资路演 / BP 模板预览"></a><br/>
      <sub><strong>融资路演 / BP</strong><br/>种子轮路演、投资人沟通、创业 BP<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/startup-pitch">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/startup-pitch/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/michael-jackson-king-of-pop"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_michael-jackson-king-of-pop.png" alt="人物 / 品牌故事模板预览"></a><br/>
      <sub><strong>人物 / 品牌故事</strong><br/>名人传记、品牌档案、文化回顾<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/michael-jackson-king-of-pop">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/michael-jackson-king-of-pop/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nl-job-market-2026"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_nl-job-market-2026.png" alt="数据 / 市场分析模板预览"></a><br/>
      <sub><strong>数据 / 市场分析</strong><br/>行业研究、趋势解读、结构化分析<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/nl-job-market-2026">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/nl-job-market-2026/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/corporate-training"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_corporate-training.png" alt="企业内训 / 工作坊模板预览"></a><br/>
      <sub><strong>企业内训 / 工作坊</strong><br/>内训课件、工作坊、技能培训、练习引导<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/corporate-training">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/corporate-training/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/solo-company-talk"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_solo-company-talk.png" alt="AI 趋势 / 个人演讲模板预览"></a><br/>
      <sub><strong>AI 趋势 / 个人演讲</strong><br/>趋势解读、个人表达、创业分享<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/solo-company-talk">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/solo-company-talk/template.pptx">下载 .pptx</a></sub>
    </td>
    <td align="center" width="33%">
      <a href="https://slides.addsum.top/viewer.html?deck=zh/kids-ai-explainer"><img src="https://slides.addsum.top/docs/assets/screenshots/preview_kids-ai-explainer.png" alt="课程 / 知识分享模板预览"></a><br/>
      <sub><strong>课程 / 知识分享</strong><br/>课程讲解、读书分享、培训材料<br/>
      <a href="https://slides.addsum.top/viewer.html?deck=zh/kids-ai-explainer">在线翻页</a> · <a href="https://slides.addsum.top/templates/decks/zh/kids-ai-explainer/template.pptx">下载 .pptx</a></sub>
    </td>
  </tr>
</table>

<p align="center"><sub>英文版在 <a href="https://github.com/addsumtech/slides_maker-site/tree/main/templates/decks/en">templates/decks/en/</a>，预览见 <a href="README.md">English README</a>。</sub></p>

---

## 模板怎么用

模板库在独立仓库 [slides_maker-site](https://github.com/addsumtech/slides_maker-site) 的 `templates/decks/` 下，中文在 `zh/`，英文在 `en/`。先克隆一份到本地：

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

两套的版式一致，文案语言不同。


---

## slide-maker 不一样在哪

市面上的 AI PPT 工具大致分四类，slide-maker 只做最后一类：

| 类型 | 输出 | 在 PowerPoint 里能逐元素编辑吗 |
| --- | --- | :---: |
| 模板填空 | 固定模板里塞内容 | 部分能，受模板限制 |
| 图片式 | 每页一张大图打包成 PPTX | 不能，每页是一张图 |
| HTML 网页式 | 浏览器里的幻灯片 | 不是 PPTX |
| **原生可编辑（slide-maker）** | **真实文本框、形状、原生图表** | **能，点哪改哪** |

这张表说的是**格式**。现在已经有几个新工具也能输出原生可编辑 PPTX，所以「可编辑」本身不再是区分点。真正让 slide-maker 不一样的是**它拿这个格式做了什么**：读你的真实材料、拒绝编造；交付前先过独立评审；每一页围绕你的内容编排，而不是把文字倒进模板。下面就按这三件事依次展开。

### 一支各司其职的 agent 小团队：分工不同，立场也不同

slide-maker 不是一个 prompt 包办一切，而是一组各有专职的 **agent**，每个只做一件事，而且刻意分开，不让同一个「人」既搭 deck 又给它打分：

- **content-planner（内容规划）**：牵头的主编。它把材料真正通读一遍，决定每页**讲什么**：记忆点、证据、整份 deck 的起承转合。每个数字都要能溯源，另有一道覆盖检查，保证材料里的关键点不会被悄悄弄丢，要么上页面，要么明确标注「有意割舍」。整条故事线出自同一个脑子，所以是一条连贯的论证，不是一堆散页拼起来。
- **slide-design（美术总监）**：另一个独立的脑子，负责已经定稿的故事**长什么样**：每页的视觉形式、配色（一种颜色在整份 deck 里只表达一个含义）、字体、节奏、图标，以及哪一页的点击渐显才真正值得做。它先对着内容在白纸上构想，再去翻组件库，所以出来的是「被设计过」，不是「套模板」。
- **critic（评审）**：一个没参与搭建的独立评审。它对着**渲染出来的**页面从两个角度挑毛病，一是内容忠实度（数字和原文对不上、关键点丢失），二是设计（版式挤压、对比度不足、合规但死板），挑出来的一律打回重修。正因为它对这份草稿没有立场，才够诚实。
- **arbiter（仲裁）**：重要场合的 deck 会加这道独立的二次复核：动手改之前，先确认评审挑出来的是真毛病、要改的是真问题，不是在改噪声。
- **asset-prep（素材准备）**：构建期的执行工。你确认设计方案之后，它**并行**把计划里的素材（裁图、公式图、生成插画、图标）做出来，不做任何设计决策，所以再大的 deck 也出得快。

分工本身就是设计：规划者只管提方案，评审者只管挑毛病。所以 deck 到你手上时，已经替你过完了一轮评审。

在这个基础上，它还有三件多数工具不做的事：

- **先读懂，再动手。** 论文从第一页读到最后一页，代码库先跑通 README，**什么材料都没有时先联网调研主题**。每个数字、每张图都对回来源，先给你一份结构稿确认，方向对了才开始画页面。它不会把摘要复制到第一页就完事。
- **能编辑的不只是文字。** 数据图优先做成原生 PPT 图表，双击就能改数字；公式默认是可编辑的原生数学文本，不是截图，只有分式、矩阵这类二维排版才退回成渲染图；论文里的图直接从 PDF 裁原图，不重画。
- **讲稿一定给，动画你说了算。** 演讲型 deck 每页备注里都有完整讲稿，拿到手就能直接开讲。点击渐显（一拍一拍地放出内容）是访谈里会问你的一项，不是默认塞给你的：你说要纯翻页，交付的就是静态 deck，那是**正确结果，不是少了功能**。真要动画时，它自己判断哪几页值得做，并且把那几页**整页排完**，不会动一半留一半。

还有一条对反复改版的人最重要：每份 deck 由一个构建脚本生成，脚本和成品放在一起。想换重点、换页数、换模板，说一句话重出一版，不用一页页手工返工。

而且它会**越用越像你的**。当你在好几份 deck 上把同一个偏好朝同一个方向反复调整（数据要鲜亮、边框要克制、不要模板味的卡片、公式要排版化），它会把这些记成一份可携带的口味档案：一个放在注册表根目录、归你所有的纯文本文件，可以逐行查看、修改、删除。之后做 deck 会把它当默认值读进来，你就不用一遍遍重教。它给的只是一个起点，当下这份 deck 你说的话永远优先；全新用户那边则是一张白纸，不预设任何风格。

一句实话：它不承诺一步出完美成品。它承诺把最费时间的部分干掉，读材料、定结构、排版、画图、写讲稿，然后给你一份真正能继续改的文件。剩下的打磨是你的，这也正是输出原生 PPTX 的意义。

---

## 它是怎么干活的

1. **问清楚。** 给谁看、讲多久、现场讲还是发出去自读、要什么风格。你用短句回答就行，没想好就说「你定」，它会自己选一个稳妥的答案，并**在动手前先贴出来**，选错了你扫一眼就能否决，不用等它做完一版再重来（只有主题、素材这类只有你知道的信息才必须问你）。
2. **读材料（或联网调研）。** 论文、文档、代码库，还有 Word、Excel、CSV、图片、视频、音频，以及按目的取舍的整本书，都照原样读进来，一律先做精确提取，绝不从像素里猜数字：图表从 PDF 里裁原图，关键数字逐条核对，没有来源的数字不上页面。手里只有一个主题时，它先联网调研最新信息，再动手。
3. **先确认故事，再确认观感，都在对话里完成。** content-planner 先贴一张紧凑的逐页表（每页讲什么、靠哪张图、整体怎么走）；你确认故事之后，美术总监再用同样的方式贴出设计方案（观感、配色、每页形式、动效）。两次确认都很快，而且正好卡在改方向最便宜的两个时刻，全程不用打开任何计划文件。
4. **生成 PPTX。** 版面由代码保证，构建时和渲染后各过一遍自动版式检查，文字溢出、元素遮挡、字体异常都会被拦下。
5. **独立评审，修到点头。** 渲染图交给评审 agent（重要场合再加一道 arbiter 复核），按演讲场景的标准挑毛病，修完复查，通过才交付到 `~/Downloads/<deck-name>/`。PDF 和浏览器预览不在每次构建时生成，只在交付时才出，因为 deck 还在改的时候，它们一生成就过期。另外**必须有一份记录证明评审确实跑过，才放行**：会跳过检查的模型，和会写「我检查过了」的模型，是同一个。
6. **用自然语言微调。** 还不完美？在对话里说一句就行：「第 7 页改成图表」「删掉引言」「配色暖一点」「压到 10 页」「备注短一点」，它会用同一份脚本干净重出一版。不用自己进 PPT 里逐页拖框调版式，一直改到满意为止。

**成本说明：** 工具免费，唯一开销是你自己的 AI 用量。读材料、定结构、生成这几步都很便宜，**贵的是独立评审这一环**，所以它做成了访谈里一个词就能定的档位：

| `review:` | 跑什么 | 实测量级 |
| --- | --- | --- |
| `fast` | 1 名通才评审、1 轮、前 5 条关键声明查证 | ~6 个 subagent · ~25 万 token |
| `standard`（默认） | 2 名单镜头评审（内容 + 设计）、2 轮、前 10 条 | ~12 · ~60 万 |
| `thorough` | 多评审面板 + 仲裁复核、3 轮、全部声明 | ~32 · ~200 万 |

默认档位**由你的用途推导**，所以什么都不说永远是安全的：组会、周报走 `standard`，答辩、路演走 `thorough`。**只有 `fast` 必须你主动开口才会用**，因为压到一名评审、一轮，是真的会漏东西，它不会替你做这个选择。

**任何档位都不会取消独立评审**，也都不会动构建期和渲染期的版式检查、交付前的 preflight 检查、来源核查关卡。档位能调的只有轮数、评审面板的人数、查证抽样的条数，**不包括「这份 deck 由谁来判」**。（上面的数字实测自一份 12 页、来源全部来自联网调研的 deck，2026 年 7 月，请当量级看，会随模型和 deck 规模浮动。）

---

## 快速开始

<p align="center">
  <img src="https://slides.addsum.top/docs/assets/quickstart_zh.png" alt="快速开始：装一次、敲 /slide-maker、读材料或联网调研、确认结构稿、生成加独立评审、拿到 pptx 再微调">
</p>

### 第一步：安装

> **⚡ 什么都不想装？直接在 ChatGPT 里用 [slide-maker (addsum studio)](https://chatgpt.com/g/g-6a5b41f0a33881918be69e8b10f8b4ff-slide-maker-gpt)。**
> 它继承了本技能的能力，去 **GPT 商店**搜「slide-maker (addsum studio)」就能开始做幻灯片，零配置；想要完整体验，还是走下面的本地安装。
>
> **更喜欢从市场一键获取？slide-maker 也已上架
> [腾讯 SkillHub](https://skillhub.cloud.tencent.com/skills/slides-maker)、
> [Coze](https://xiaping.coze.com/skill/c0136d99-50d0-4f05-909a-f78fa4be7104) 和
> [ClawHub](https://clawhub.ai/dong845/skills/slide-maker)，其中 ClawHub 那份可以直接装进
> [OpenClaw](https://openclaw.ai)，所以 OpenClaw 用户一样能用 slide-maker。**
> 按对应页面的说明获取即可，然后回来装下面的运行依赖（无论哪种装法都需要）。

slide-maker 依赖三样系统工具：**Python 3.9+**、**LibreOffice**（渲染页面预览，用来做自动版式检查），以及一个给图标用的 **SVG 栅格化器**（librsvg、cairosvg，或任意 Chrome 系浏览器都行）。按你的系统装：

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

它会先问你装到哪个 agent、哪个范围。技能在仓库的 `skills/slide-maker/` 下，模板库和演示站放在独立仓库 [slides_maker-site](https://github.com/addsumtech/slides_maker-site)，主仓库没有大文件，所以装起来又小又快。加 `-g` 装到全局（所有项目），加 `-a claude-code`（或 `-a codex`）跳过 agent 选择，加 `-y` 全程免确认。上面那几个运行依赖照样要装：LibreOffice、一个 SVG 栅格化器，以及 `python3 -m pip install -r skills/slide-maker/requirements.txt`。

**用 Claude Code 的话，也可以把它当插件装**，之后用普通插件命令就能更新：

```text
/plugin marketplace add addsumtech/slides_maker
/plugin install slide-maker@slides-maker
```

装的是同一个技能，只是交给 Claude Code 的插件系统管理，而不是复制到你的技能目录。上面那几个运行依赖照样需要。

### 保持更新

slide-maker 会在问你任何问题之前先查一次版本，**已经是最新就什么都不说**。发现有新版时，它既不会自己偷偷更新，也不会只提一嘴就过去，而是在最开头问你一次：

- **yes**：先更新，再用新版本开工。
- **no**：用现在装的版本。做到一半时选这个是对的，一份 deck 前半段和后半段由两个版本造出来，比整份都用旧版更糟。
- **other**：你本地有自己的改动。它会把哪些是你改的、哪些是新版带来的摆给你看，自己不替你做决定。

远端版本信息缓存 24 小时，但**你本地有没有未提交的改动，每次都重新检测，从不用缓存**。因为这一项直接决定要不要覆盖你的文件：如果它信了一天前那句「你的工作区是干净的」，而你今天刚好改过技能里的文件，更新就会把你的改动冲掉。断网时它保持安静，不碍事。

怎么更新取决于你当初怎么装的：

```bash
npx skills add addsumtech/slides_maker            # 一行命令装的：重跑同一条命令
git -C /path/to/slides_maker pull --ff-only       # clone 下来的仓库
```

当插件装的？插件系统会替你更新，这也是推荐那条路的主要理由。

不想被提醒：`export SLIDE_MAKER_NO_VERSION_CHECK=1`。

### 第二步：敲 /slide-maker，逐题回答（最推荐）

效果最稳的方式，是**把它的简短访谈逐题答完**：

```text
/slide-maker
```

访谈会展开成一个可点选的标签页问卷（主题 · 模板 · 用途受众 · 风格语言）：方向键切换、回车选择，每题都带现成选项。评审档位跟着「用途受众」一起问，因为默认档位就是从用途推导出来的。它也认得老用户：你存过的模板、做过的主题会合并成一个「用我之前的」选项，放在通用选项旁边，选中才展开清单。**一题一题答完，正是让 deck 变成「你的」而不是通用款的关键**：受众、时长、现场讲还是发出去自读、密度、语言、观感，还有你要它审得多严，都会影响方案。短句回答就行，**「你定」永远是合法答案**。

**赶时间？一句话开场也行，但这是抄近路，不是最佳走法：**

```text
用 slide-maker 按 paper.pdf 做一份 PPT。
```

它直接从你的文件开始，跳过主题那一问，确实方便。但每一个你没回答的问题，都会变成它必须替你做的假设，之后你通常要花更多时间微调回来。**deck 重要的话，就把访谈答完。**（Codex 里没有斜杠命令，同样这些问题会以纯文字出现，功能一样完整，只是要自己打字；Claude Code 的点选体验更顺手。）

无论哪种开场，之后都是一段简短对话，不是写 prompt 考试：

```text
它：开工前问几件事：模板用哪套？给谁看、讲多久、现场还是自读？
    素材只有这份 PDF 吗？中文还是英文，图多字少还是均衡？

你：给导师和组会同学，12 分钟现场讲。只有 paper.pdf。
    中文，图多字少，风格你定。

它：（读完论文）结构稿来了：15 页。第 4 页整页放论文 Figure 1，
    结果页做成能改数字的原生图表……你确认方向，我就开始生成。
```

- **风格由你先挑，不用开口要。** 当它从零给你设计（你自己没有模板）时，会把**四个风格方向渲染出来**，给你一个浏览器链接，等你选完再动手。四个里**至少有一个是为你这个主题原创的**，不是从预设里挑的；另外有一道自动检查会挡掉「四个方向其实是同一件事换四种配色」，所以那是真的让你选，不是走过场。
- 材料放进当前项目，或在请求里写完整路径。**什么材料都没有？** 给个主题就行，它先联网调研，再和你对结构。

其他开场方式：

```text
用 slide-maker 按这个代码仓库做一份技术汇报。
```

```text
我有参考 PPT：/path/ref.pptx。参考它的视觉风格，不要它的内容，用 paper.pdf 重新做一份中文汇报。
```

### 可选：AI 生图

需要封面图、页面配图，或者整套 AI 生成的视觉时，在对话里说一句「需要 AI 生图」。生图有两条路，任选其一：有 Codex 订阅就免 key 直接用它的图片生成；没有的话，配一个 OpenAI API key 走 API 也一样。两样都没有也不影响主流程，照常生成可编辑 PPTX。

---

## 适合什么场景

科研汇报是主场，因为它会解析论文里的问题、方法、结果、图表、表格和公式。但只要你手里有一份需要讲清楚的材料（或者只有一个主题、还没材料），它都能先给你一版能开讲、能继续改的 PPT。

| 你手里有 | 可以先做成 |
| --- | --- |
| 论文、实验结果、论文图表 | 组会与论文精读、会议口头报告、海报、开题、答辩、实验结果汇报 |
| 代码仓库、README、技术文档 | 组会、代码仓库讲解、技术架构、阶段进展、工程复盘 |
| 课程材料、产品资料、市场数据 | 课程分享、产品介绍、市场分析、方案说明 |
| 什么都没有，只有一个主题 | 给它一个主题；agent 团队联网调研最新信息，和你对好结构，再从零做出整份 deck |
| 参考 PPT | 换主题、换内容、重新组织表达：用它的观感，你的材料 |
| 想让同一个故事走出 16:9 | 小红书 3:4 图文卡、方形 1:1、9:16 竖版封面、4:3 会场版、A4 打印一页纸，同一套视觉和组件按画布重排，自动避开平台 UI 安全区 |

---

## 遇到问题

生成 PPT 或渲染预览报错时，按你的环境跑检查命令，多数问题是 Python 依赖或 LibreOffice 没装好：

```bash
# Codex
python3 ~/.codex/skills/slide-maker/scripts/check_env.py

# Claude Code
python3 ~/.claude/skills/slide-maker/scripts/check_env.py
```

缺什么它会直接打印修复命令。

环境之外的问题，比如构建报错、lint 各类提示的白话解释和修法、渲染失败、图片来源、中文排版，都有一个专门的「症状 → 原因 → 修法」排障 FAQ 页：[**Troubleshooting & FAQ**](skills/slide-maker/references/troubleshooting-faq.md)（lint 没通过时，输出末尾也会提示这个页面）。页面里没覆盖到的，欢迎开 issue，带上报错输出。

---

## 安全

本仓库不存放、也不硬编码任何凭证。CI 每次 push 都会扫描，工作树**和全部历史**一起扫，而且是按凭证的**形态**（长度加熵）来扫，不是按前缀。如果有扫描器在这里报出 `sk-` 密钥，它命中的是 CSS 类名（`sk-body`、`sk-split`、`sk-rail`，`sk-` 是 skeleton 骨架的缩写）。[**SECURITY.md**](SECURITY.md) 里写了十秒确认的方法，以及真有问题时怎么报给我们。

---

## 开源协议

[MIT](LICENSE)
