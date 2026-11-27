#!/usr/bin/env python3
"""A registry of DECK PURPOSES — and the content each genre is not finished without.

🔴 WHY THIS EXISTS. `references/design-by-purpose.md` carries nine purposes, each a prose recipe
(Type · Palette · Density · Layout · Icons · Signature). Measured by grep, NOTHING consumed it: a
purpose entry could be ignored line by line and no gate would know, so every per-purpose rule in
that file was advisory by construction. And four genres with the hardest conventions were absent
from the list entirely — a grant proposal, a progress/guidance committee, a journal club, and a
clinical case presentation. The last three are among the most common decks an academic makes.

The mechanism is deliberately the SAME ONE `formats.py` already uses for surfaces: a registry
declares the sections a genre cannot be finished without, and `check_purpose.py` looks for them in
the built deck. That precedent exists because of a real finding — "a poster in the billboard style
that reads best is also the style that drops the two things a passer-by cannot reconstruct" — and
the finding generalises: the shape of a genre is exactly what an author under time pressure drops.

🔴 WHAT THIS CHECK IS, AND IS NOT. It asks "does this deck NAME the thing", not "does it do it
well". A deck can name its risks in two words and pass; judging whether the mitigation is credible
is the critic's job and always will be. The cheap catch is the one worth having: a grant deck with
no feasibility slide and a committee deck with no ask are not weak decks, they are decks missing a
section their audience is required to score.

Synonyms are multilingual on purpose — a Chinese deck names the same section in Chinese, and a check that
only knows English would fire on every one of them.

    python3 scripts/purposes.py --list
    python3 scripts/purposes.py --brief "<purpose name or the user's words>"   # the genre's playbook
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Purpose:
    name: str
    label: str
    note: str
    # (section label, (term, term, …)) — the deck must NAME each section somewhere
    required_sections: tuple = field(default_factory=tuple)
    # words in the user's recorded purpose/goal that bind a deck to this entry
    binds_on: tuple = field(default_factory=tuple)
    # the one fidelity rule this genre carries beyond the universal never-invent floor
    fidelity: str = ""
    # 🔴 THE PLAYBOOK — what someone who makes this kind of deck for a living knows, in the order a
    # planner needs it. `--brief` prints it, and `deck_gates.py picks --set purpose=…` prints it the
    # moment the genre is recorded, so every runtime (Claude Code, Codex, a plain CLI) has it in
    # context while planning — a rule that lives only in a reference file is a rule the run never
    # opened (measured 2026-11-19). Sources are named so a reader can check the convention.
    arc: tuple = field(default_factory=tuple)        # the beats, in order
    rules: tuple = field(default_factory=tuple)      # content rules specific to this genre
    design: tuple = field(default_factory=tuple)     # design conventions, WITHIN the chosen look
    pitfalls: tuple = field(default_factory=tuple)   # what the critic will look for
    sources: tuple = field(default_factory=tuple)


PURPOSES = (
    Purpose(
        "grant", "Grant proposal / funding pitch",
        "ERC · NWO · NIH · Horizon — the highest-stakes deck an academic makes, and the one with "
        "the most rigid conventions, because reviewers score against named criteria.",
        # 🔴 No bare "proposal": a business proposal, a project proposal and a marriage proposal
        # are not this genre, and `recorded_purpose` also reads the AUDIENCE BRIEF, so a loose term
        # binds far more decks than the purpose row alone would.
        # 🔴 No bare "grant", "funding" or 基金 either (real run, 2026-10-29): an annual review
        # whose material listed 社区基金会 — a community foundation, as an INCOME SOURCE — bound
        # here and was asked for feasibility and risk sections. "a grant from X", "funding came
        # from donors", 慈善基金会 are things a deck MENTIONS; the genre is APPLYING for one. Bare
        # "grant" also matched inside "immigrant". `match` is a substring test, so every term
        # below names the act of applying or pitching, not the money.
        binds_on=("grant proposal", "research proposal", "grant application", "grant pitch",
                  "grant renewal", "grant interview", "grant panel", "funding proposal",
                  "funding application", "funding pitch", "funding request", "apply for funding",
                  "applying for funding", "apply for a grant", "applying for a grant",
                  "fellowship application", "fellowship interview", "erc ", "nwo", "nih ",
                  "horizon europe",
                  "基金申请", "申请基金", "基金项目申请", "申请国家自然科学基金", "国家自然科学基金申请",
                  "国自然申请", "国自然本子", "基金本子", "基金标书", "基金答辩",
                  "课题申请", "项目申请", "经费申请"),
        required_sections=(
            ("aims", ("aim", "aims", "objective", "objectives", "research question", "goal of this",
                      "what i propose", "目标", "研究目标", "科学问题")),
            ("feasibility", ("feasib", "track record", "preliminary", "pilot data", "why me",
                             "why now", "capability", "expertise", "可行性", "前期", "预研")),
            ("risk", ("risk", "risks", "mitigation", "contingency", "fallback", "what could go "
                      "wrong", "风险", "应对", "备选")),
        ),
        fidelity="Preliminary data is the section most often overstated. A pilot is a pilot: say n, "
                 "say it is preliminary, and never let a promising trend read as an established "
                 "result — a reviewer who catches one inflated claim discounts the rest.",
    ),
    Purpose(
        "committee", "Progress / guidance committee meeting",
        "A PhD guidance committee, a thesis advisory board, a stage-gate review. It differs from a "
        "lab meeting in exactly one way, and it is the way that matters: the room has to DECIDE "
        "something — is this on track, does the book hold together, what should be scoped down.",
        # 🔴 No bare "committee" or "advisory": an INVESTMENT committee, an ETHICS committee and a
        # steering committee are different genres with different required content, and binding them
        # here would fire a three-section list at the wrong deck — which is how a check teaches
        # people to ignore it. The qualifier is what makes the binding a claim rather than a guess.
        binds_on=("guidance committee", "advisory committee", "thesis committee",
                  "doctoral committee", "supervisory committee", "committee meeting",
                  "progress review", "annual review", "progress meeting", "stage gate", "go/no-go",
                  "指导委员会", "中期考核", "年度考核", "开题", "进展汇报"),
        required_sections=(
            ("progress", ("progress", "since last", "this year", "past year", "completed",
                          "published", "achieved", "进展", "已完成", "去年")),
            ("plan", ("plan", "next", "remaining", "timeline", "roadmap", "schedule", "ahead",
                      "计划", "下一步", "时间线", "剩余")),
            # no bare "input": "input data" is not an ask, and the rest already cover it
            ("ask", ("the ask", "advice", "guidance", "decision", "question", "feedback",
                     "recommend", "建议", "决策", "请教", "问题")),
        ),
        fidelity="What is NOT done yet must read as not done. A committee's value is advice on open "
                 "work, and a hypothesis promoted to a result removes the very thing they are "
                 "there to help with (`content.open_ledger` is the artifact for this).",
    ),
    Purpose(
        "journal_club", "Journal club / presenting someone else's paper",
        "You are presenting work you did not do. Extremely common, and it carries a fidelity risk "
        "the universal never-invent rule does not cover: not fabrication, but MISATTRIBUTION — "
        "stating their result more strongly than they did, or blurring their claims with your "
        "critique until the audience cannot tell which is which.",
        binds_on=("journal club", "paper presentation", "reading group", "present a paper",
                  "discuss the paper", "文献汇报", "文献阅读", "组会读论文", "论文分享", "读书会"),
        required_sections=(
            ("attribution", ("attribution", "et al", "authors", "published in", "doi", "arxiv",
                             "reference", "citation", "source", "作者", "发表于", "文献")),
            ("critique", ("limitation", "limitations", "weakness", "critique", "caveat",
                          "my take", "assessment", "concerns", "局限", "不足", "评价", "批评")),
        ),
        fidelity="Keep THEIR claim and YOUR reading visually separable — attribute on the slide "
                 "that carries the result, not only on the title. An audience that cannot tell "
                 "which is which will remember your critique as the paper's own conclusion.",
    ),
    Purpose(
        "clinical_case", "Clinical case presentation / tumour board / M&M",
        "A fixed clinical narrative — presentation, investigations, management, outcome. The "
        "structure is not a style choice: colleagues are being asked to judge a decision, and they "
        "cannot do that without the information that was available when it was made.",
        # 🔴 No bare "morbidity"/"mortality", 病例 or 多学科: a hospital's annual report says
        # "mortality fell", "收治病例 3000 例", "多学科合作" — content, not a case presentation.
        binds_on=("case presentation", "clinical case", "tumour board", "tumor board", "mdt",
                  "morbidity and mortality", "m&m", "grand round", "病例汇报", "病例讨论",
                  "病例分享", "病例报告", "疑难病例", "多学科会诊", "多学科讨论", "查房"),
        required_sections=(
            ("presentation", ("history", "presented", "presentation", "symptom", "chief complaint",
                              "病史", "主诉", "现病史")),
            ("investigations", ("imaging", "investigation", "workup", "work-up", "laboratory",
                                "labs", "biopsy", "scan", "ct", "mri", "检查", "影像", "化验")),
            ("management", ("management", "treatment", "plan", "intervention", "therapy",
                            "operation", "治疗", "处理", "方案")),
            ("outcome", ("outcome", "follow-up", "follow up", "learning point", "take-home",
                         "what we learned", "转归", "随访", "经验", "教训")),
        ),
        fidelity="🔴 DE-IDENTIFICATION IS LOAD-BEARING HERE, not a nicety — this is the genre "
                 "PRE-FLIGHT 5's burned-in-identifier check exists for. Name, MRN, accession, date "
                 "of birth, study date and institution on any scan, read on all four edges and in "
                 "every overlay strip. Get a de-identified export; never crop or blur and ship.",
    ),

    Purpose(
        "defense", "Thesis defense",
        "An expert committee that will probe. The three sections below are what a defense is "
        "SCORED on: what you contributed, what you know is wrong with it, and what comes next. A "
        "defense that names no limitations reads as one that has not found them yet.",
        binds_on=("thesis defense", "phd defense", "doctoral defense", "viva", "dissertation "
                  "defense", "promotie", "答辩", "博士答辩", "论文答辩"),
        required_sections=(
            ("contributions", ("contribution", "contributions", "we propose", "this thesis",
                               "novelty", "我们提出", "贡献", "创新")),
            ("limitations", ("limitation", "limitations", "caveat", "weakness", "threats to "
                             "validity", "局限", "不足")),
            ("future work", ("future work", "future directions", "next steps", "outlook",
                             "further research", "未来工作", "展望", "后续")),
        ),
        fidelity="Own the limitations before the committee finds them. A limitation you raised is "
                 "evidence of judgement; the same one raised from the floor is a gap.",
        arc=("Thesis statement and the contributions, early",
             "Context: the gap the thesis fills",
             "Each contribution, keyed to its research question (RQ1, RQ2 …): question → method → result",
             "Synthesis: what the contributions add up to",
             "Limitations — raised by you, before the committee does",
             "Future work",
             "Backup slides after the closing slide, for the questions you predict from each member's research"),
        rules=("Keep the main talk short; detail lives in backup slides you can jump to.",
               "Number the research questions (RQ1, RQ2 …) and reuse the same labels on the result slides.",
               "Predict the committee's questions from their research interests and prepare a backup for each.",
               "Every result slide states its claim as a sentence (assertion-evidence); graphs over tables for findings."),
        design=("Assertion–evidence: a sentence headline, at most two lines, over the figure that proves it.",
                "Slide numbers on every slide, so a committee member can point at one.",
                "A chapter progress marker; no decorative transitions or animations.",
                "Same internal layout for every contribution block — the repetition is the signpost (house rule)."),
        pitfalls=("An 80-slide stack skipped through at speed.", "No limitations slide.",
                  "Bullet slides or tables where the evidence should be a figure."),
        sources=("Alley, assertion–evidence (Penn State)", "CMU library defense guide", "Columbia (Schulzrinne) defense hints",
                 "Valdosta State dissertation-defense guide (limitations, RQ labels)", "MSVU defense preparation"),
    ),
    Purpose(
        "conference_talk", "Academic conference talk",
        "10-20 minutes, an audience who did not read the paper and will not remember three things. "
        "The contribution and the evidence for it are the talk; everything else is context.",
        binds_on=("conference talk", "conference presentation", "miccai", "ismrm", "cvpr", "neurips",
                  "oral presentation", "spotlight talk", "会议报告", "大会报告", "口头报告"),
        required_sections=(
            ("contribution", ("contribution", "we propose", "our method", "this work", "novelty",
                              "我们提出", "本文", "贡献")),
            ("evidence", ("evidence", "result", "results", "evaluation", "experiment", "we evaluate",
                          "benchmark", "结果", "实验", "评估")),
            ("limitations", ("limitation", "limitations", "caveat", "does not", "fails when",
                             "局限", "不足")),
        ),
        fidelity="A conference audience cannot check you in the room, which is exactly why the "
                 "limitation slide matters. State the regime where the method does NOT hold.",
        arc=("Title + the contribution in one sentence (no outline slide)",
             "The problem and why it matters to THIS audience",
             "The key idea — intuition before formalism",
             "Method: just enough to trust the result",
             "Evidence: the main result first, written on the slide, then what supports it",
             "Limitations: where it does not hold",
             "Contributions slide last — left up during questions",
             "Backup slides: details from the paper"),
        rules=("One main idea done well beats everything done superficially; cut the first draft hard.",
               "About a slide a minute is an upper bound, not a target.",
               "The key result is written on its slide (title or callout), not only spoken or left in the notes.",
               "Every symbol in an on-slide equation is defined on that slide; an equation appears only when it carries the headline.",
               "Cite a borrowed figure or claim on the slide where it appears."),
        design=("Assertion–evidence: a sentence headline (≤ 2 lines) over visual evidence, minimal bullets.",
                "Paper figures redrawn for the room: thicker lines, bigger points, figure text at body size.",
                "Slide numbers on every slide, so questions can point at one.",
                "Builds very sparingly — only for a punchline or a staged process."),
        pitfalls=("All-bullet slides.", "Too many slides, then rushing the result.",
                  "Equations or figure text no one can read from the room."),
        sources=("Alley, assertion–evidence (Penn State; UNM checklist)", "Peyton Jones, How to give a good research talk",
                 "Ernst, giving a technical talk", "Naegle, ten simple rules for effective presentation slides (PLOS)"),
    ),
    Purpose(
        "job_talk", "Academic job talk / faculty interview",
        "A hiring committee is deciding whether to bet five years on you. They are scoring a "
        "TRAJECTORY, not a paper: what you have done, what you will do with their resources, and "
        "why you specifically.",
        binds_on=("job talk", "faculty interview", "faculty position", "tenure track",
                  "interview seminar", "求职报告", "教职面试"),
        required_sections=(
            ("track record", ("track record", "published", "my work", "i have", "prior work", "to date",
                              "已发表", "我的工作", "过往")),
            ("research plan", ("research plan", "next five years", "future programme", "my lab",
                               "will pursue", "agenda", "研究计划", "未来五年")),
            ("fit", ("fit", "why here", "collaborat", "your department", "this institute",
                     "适合", "合作", "为什么是这里")),
        ),
        fidelity="The plan is judged on feasibility, not ambition. A five-year programme with no "
                 "named first project reads as a wish; say what starts in month one.",
    ),
    Purpose(
        "exec_readout", "Company / stakeholder / investor readout",
        "A room that must DECIDE and has less time than you think. Minto applies literally: the "
        "answer first, the number that supports it, and the risk you are asking them to accept.",
        binds_on=("stakeholder readout", "investor readout", "board readout", "exec readout",
                  "executive readout", "steering committee", "quarterly review", "board meeting",
                  "business case", "decision deck", "approval request", "proposal to leadership",
                  "proposal to management", "投资人汇报", "董事会", "管理层汇报",
                  "季度汇报", "立项", "决策汇报", "方案评审", "高层汇报"),
        required_sections=(
            ("the ask", ("we recommend", "the ask", "decision", "approve", "we propose", "request",
                         "建议", "决策", "请批准")),
            ("the number", ("the number", "revenue", "cost", "roi", "budget", "headcount", "%", "growth",
                            "impact", "收入", "成本", "预算", "指标")),
            ("the risk", ("risk", "risks", "mitigation", "downside", "what could go wrong",
                          "assumption", "风险", "假设", "下行")),
        ),
        fidelity="A readout that names no downside is read as a sales pitch, and the first "
                 "question will be the one you left out. Name the assumption the number rests on.",
        arc=("The answer: the recommendation and the decision you ask for (SCQA opening)",
             "Why: the supporting arguments, mutually exclusive and together complete — one slide each",
             "The number(s) that carry the case, with the assumption each rests on",
             "Options considered, and why this one",
             "The risk you ask them to accept, and its mitigation",
             "The ask restated + next steps and dates",
             "Appendix: backup for each question you expect"),
        rules=("Action titles: every title is a full-sentence takeaway, and the titles read in order ARE the argument "
               "(draft the titles alone first and fix the logic before designing — consulting practice).",
               "One exhibit per claim; the exhibit proves its title and nothing more.",
               "Quantify the stakes in the room's terms (money, time, risk) and name the assumption.",
               "At most two bullet levels: nothing critical may sit in a sub-bullet.",
               "A pre-read sent before the meeting is a self-read document (delivery = self-read), not a talk deck."),
        design=("Units on every chart ('$M'), the same scale on charts compared across slides, numbers rounded to what the decision needs.",
                "One highlight colour for the bar or line the title is about; everything else neutral.",
                "Direct labels instead of a legend; label the start, the key points and the end.",
                "Restraint and white space; the consulting / editorial presets fit, but the deck's chosen look wins."),
        pitfalls=("The critical finding buried in nested bullets.", "No downside named.",
                  "Charts without units, or compared charts on different scales.", "Statistics with no stakes attached."),
        sources=("Minto, The Pyramid Principle / SCQA", "Umbrex, design principles for consulting charts",
                 "Storytelling with Data, horizontal logic", "Duarte on pre-reads", "Tufte on the Columbia slides"),
    ),

    Purpose(
        "research_meeting", "Research meeting with a supervisor / lab group",
        "A working session with an expert audience, held often. Its two sections come straight out "
        "of this skill's own recipe for it — 'what changed since last time' framing, and an open "
        "questions slide — because a working session with neither is a report, and nobody called a "
        "meeting to receive a report.",
        binds_on=("lab meeting", "group meeting", "supervisor meeting", "research meeting",
                  "weekly meeting", "one-on-one", "组会", "小组会", "例会", "和导师"),
        required_sections=(
            ("what changed", ("since last", "what changed", "this week", "progress", "update",
                              "new result", "上次之后", "本周", "进展", "新结果")),
            ("open questions", ("open question", "question", "stuck", "blocker", "not sure",
                                "need help", "where i am stuck", "问题", "卡住", "不确定", "请教")),
        ),
        fidelity="A working session is where an unfinished result is USEFUL. Rounding a shaky "
                 "number up for the supervisor is the one audience where it costs you directly — "
                 "they will build advice on it.",
    ),
    Purpose(
        "work_status", "Work status update to a manager / team",
        "Decision- and outcome-oriented, for a reader who is busy. Its sections are this skill's "
        "own recipe: lead with the RESULT, and make every takeaway a decision or an ask.",
        binds_on=("status update", "status report", "weekly update", "project update",
                  "sprint review", "team update", "project review", "progress update", "status meeting",
                  "weekly report", "monthly report", "工作汇报", "周报", "月报", "项目汇报", "工作总结",
                  "年终总结", "季度总结", "述职", "进度汇报"),
        required_sections=(
            ("outcome", ("outcome", "result", "results", "delivered", "shipped", "completed",
                         "achieved", "成果", "结果", "已完成", "交付")),
            ("the ask", ("decision", "we need", "the ask", "approve", "request", "blocked on",
                         "recommend", "决策", "需要", "请批准", "建议")),
            ("risks", ("risk", "risks", "blocker", "blockers", "blocked", "issue", "issues", "at risk",
                       "delay", "风险", "阻塞", "问题", "延期")),
        ),
        fidelity="A status update with no ask is a report the reader did not need. If nothing is "
                 "wanted from them, say that explicitly rather than leaving them to guess.",
        arc=("Headline: overall status + the one thing you need from them (bottom line up front)",
             "Status by dimension (scope · schedule · budget · quality …): red / amber / green, trend, and a legend saying what each colour means",
             "Done since last update — outcomes, not activity",
             "Risks (might happen) and issues (happening now) — each with owner, impact, next action and due date",
             "Decisions needed — options, your recommendation, and what happens if no one decides",
             "Plan for the next period — milestones with baseline and forecast dates",
             "Appendix: detail and backup"),
        rules=("Lead with the ask; it is why the meeting exists (bottom line up front).",
               "Every red or amber item states its cause, the corrective action and the date it is expected back to green.",
               "Keep risks and issues apart; every one has an owner and a due date.",
               "Outcomes over activity: 'shipped X, latency down 20%', not 'worked on X' (house rule).",
               "A 'data as of <date>' line on every slide that carries numbers, and the same number matches on every slide (house rule)."),
        design=("A status board: scorecards / RAG chips per dimension, with a one-line legend per colour on the page.",
                "Every RAG chip carries its colour as a word or letter (R / A / G) so it reads in greyscale and to colour-blind readers; red-amber-green is used ONLY for status.",
                "A milestone strip showing baseline vs forecast date; slipped items marked.",
                "A predictable grid, one slide per workstream; the detail goes to the appendix."),
        pitfalls=("An activity dump that buries the signal.", "The decision deferred because the ask was buried.",
                  "RAG colours with no legend, or colour as the only signal.", "Stale or conflicting numbers."),
        sources=("UK IPA delivery-confidence guide (status by dimension, defined colours)", "PMI, risks vs issues",
                 "plainlanguage.gov / AR 25-50 (bottom line up front)", "Harrin, Rebel's Guide to PM (RAG legend, back-to-green date)"),
    ),
    Purpose(
        "product_pitch", "Sales pitch / product pitch / launch",
        "Selling a product to prospects, customers or users. Two sections come from this skill's "
        "own recipe: a crisp one-line POSITIONING ('X for Y who want Z'), and benefits rather than "
        "features.",
        binds_on=("product pitch", "sales deck", "product demo", "customer presentation",
                  "product launch", "go-to-market", "sales pitch", "sales presentation", "customer pitch",
                  "pitch to a customer", "pitch to a client", "launch event", "产品介绍", "产品发布",
                  "销售材料", "客户演示", "销售", "推介", "售前", "发布会"),
        required_sections=(
            # 🔴 no "is a": it is not a positioning phrase, it is English. It matched "This is a
            # summary" and made this whole section vacuous.
            ("positioning", ("for teams who", "for people who", "positioning", "we help",
                             "designed for", "built for", "helps you", "定位", "面向", "帮助"))
            ,
            ("benefits", ("benefit", "benefits", "you can", "saves", "so that", "value",
                          "outcome for you", "收益", "价值", "你可以")),
            ("proof", ("proof", "case study", "customer", "customers", "testimonial", "trusted by",
                       "results", "案例", "客户", "实证", "口碑")),
            ("next step", ("next step", "next steps", "get started", "contact", "book a demo", "free trial",
                           "call to action", "下一步", "联系", "试用", "预约")),
        ),
        fidelity="Benefits, not features — and a benefit is a claim. Every number on a pitch slide "
                 "is one a customer may hold you to; an unverifiable one is not persuasion, it is "
                 "an unpaid debt.",
        arc=("The shift: a big, undeniable change in the customer's world (not your product)",
             "The stakes: who wins and who loses as that change plays out",
             "The promised land: the customer's better future — not your features",
             "Capabilities as obstacle-removers: each feature tied to one obstacle on the way there",
             "Proof: a customer comparable to this one, before → after on a metric over a stated period",
             "Next step: one concrete ask with an owner and a date",
             "Launch event / keynote variant: what is ↔ what could be, rule of three, one planned surprise moment"),
        rules=("Lead with their problem and the change in their world; 'about us' is at most one slide, after the shift.",
               "Benefits over features; a feature earns its slide by removing a named obstacle.",
               "Every number carries its unit, its period and a comparison the audience relates to.",
               "Logos, names and quotes only with permission; every quote attributed with name, role and company.",
               "One call to action, on the last slide — no second one elsewhere."),
        design=("This skill's house register for a pitch is brand-led and bold — full-bleed imagery for the shift and "
                "the stakes, big headline claims (house style, not a sourced rule).",
                "Real product screenshots and logos only — cropped to the one thing that matters, never mock UI.",
                "One idea per slide; headlines short enough to tweet."),
        pitfalls=("Opening with 'about us'.", "A feature list.", "Numbers with no unit, period or comparison.",
                  "A generic deck not tailored to this customer."),
        sources=("Andy Raskin, the strategic narrative (via secondary summary)", "Duarte (what is / what could be, the CTA)",
                 "Gallo on Jobs's keynotes", "Gong, sales presentation research (vendor)"),
    ),
    Purpose(
        "teaching", "Teaching / lecture",
        "The goal is understanding and retention for a mixed or novice audience. This skill's own "
        "recipe already names the three: an objectives slide up front, a 'concept → example' "
        "spine, and a recap at the end — which is also what every instructional-design framework "
        "asks for, and what a lecture assembled under time pressure drops first.",
        # 🔴 No bare "course", "class" or "workshop": "of course", "world-class", "classification"
        # and "we ran 12 workshops this year" are not lectures (`match` is a substring test).
        # 培训 / "training workshop" belong to `training` (adults learning a job task); bare "lesson" is
        # not here because "lessons learned" is a retrospective, not a lecture.
        binds_on=("lecture", "teaching", "tutorial", "a course on", "a course for", "a class on",
                  "a class for", "classroom", "teaching workshop", "hands-on workshop", "workshop session",
                  "a lesson on", "a lesson for", "lesson plan", "k-12", "k12", "primary school",
                  "elementary school", "middle school", "high school", "secondary school", "for my students",
                  "undergraduate course", "讲课", "教学", "授课", "课程", "课件", "上课", "公开课", "说课",
                  "微课", "教案", "数学课", "语文课", "英语课", "物理课", "化学课", "生物课", "历史课",
                  "地理课", "科学课", "思政课", "班会"),
        required_sections=(
            ("objectives", ("objective", "objectives", "learning goal", "by the end", "you will "
                            "be able", "what you will learn", "目标", "学习目标", "本节")),
            # bare "case" is not a teaching signal ("in case", "use case", "showcase"); the
            # distinctive words already carry it
            ("worked example", ("example", "worked example", "let us", "walk through", "case study",
                                "demo", "例子", "示例", "演练")),
            ("recap", ("recap", "summary", "to summarise", "to summarize", "key points",
                       "takeaway", "小结", "总结", "要点")),
            # no bare "question": "Questions?" closes every deck and checks nothing
            ("check for understanding", ("check for understanding", "check your understanding", "quiz",
                                         "try it", "your turn", "practice", "exercise", "predict", "pop quiz",
                                         "exit ticket", "think-pair-share", "练一练", "想一想", "随堂练习",
                                         "小测", "练习", "思考题", "测一测", "抢答")),
        ),
        fidelity="A novice cannot tell a simplification from a claim. Say when you are "
                 "simplifying — 'this is roughly true, the exact version is…' — or the "
                 "simplification is what they will carry away as fact.",
        arc=("Hook: a question, puzzle, surprising fact or everyday situation the lesson will answer",
             "Objectives: a few 'by the end you can …' statements with learner verbs (explain · compute · compare), not topics",
             "Recall what they already know + define the terms the lesson needs (pre-training)",
             "Small steps, repeated: one new idea → example → check for understanding",
             "Worked example → guided practice → independent practice (fade the steps: full example, then one with gaps, then theirs)",
             "The misconception, head-on: show the tempting wrong answer and why it is wrong",
             "Recap + exit ticket: the key points and one question that tests an objective"),
        rules=("One new idea per slide; a slide with two is two slides.",
               "Every check asks the learner to DO something — choose, predict, compute, explain — and the answer "
               "is revealed with why the wrong options are wrong. 'Any questions?' is not a check.",
               "A check for understanding every few content slides, not only at the end.",
               "Discuss first, then reveal: every check and activity slide SHOWS its answer on the slide, on the click "
               "after the room has committed (anim.Build — check_question(build=…) or the answers drawn in a "
               "Build.step). This is part of the lesson, not decoration, so it holds even when the user declined "
               "animation — then the answer goes on the next slide. An answer that lives only in the speaker notes "
               "never reaches the students.",
               "A worked example lists its givens with units BEFORE substituting (m = 50 kg, g = 10 N/kg, S = 0.04 m²), "
               "then substitutes with units — a student who sees only the slide can redo it.",
               "Concrete before abstract: an everyday example or picture first, the definition second.",
               "Set the register by AGE BAND (ask it): younger readers — fewer words, larger type, everyday words, a "
               "character or story; university — precise terms defined on first use, derivations as builds, sources "
               "cited; adult / professional — why it matters to their work first, case-based. No sourced pt figure "
               "exists for K-12: hold the 18pt body floor and go up for the primary grades.",
               "Interesting through substance, not decoration: a mystery to solve, a real stake, a surprising result, a "
               "story, a 'which would you choose?' vote."),
        design=("Signal where they are: a lesson progress strip, or the objective's own number heading its pages.",
                "Build complex diagrams step by step (anim.Build) in the order you explain them; one highlight at a time.",
                "Checks get their own recognisable look across the deck — deckkit.check_question (choose / predict, "
                "answer revealed on click) and deckkit.prompt_card (think-pair-share, try it, discuss) — so learners "
                "know 'now it is my turn'.",
                "Reveal an answer by marking the OPTION itself — ring or tick its letter or label, tight to the text. "
                "Never a ring around a whole drawing (house rule).",
                "Formulas are read, so they are set at reading size (≈ body, at most the title's size); a lesson's "
                "hero is a number or a sentence, never an equation blown up to fill the slide (house rule).",
                "Notation: quantity symbols italic (m, g, F), units upright (kg, N), a space between number and unit; "
                "every formula on a slide set the same way — all equation objects (deckkit.equation_omml).",
                "Icons as concept anchors, each with a word beside it; for K-12 a visual language (cutpaper · bricks · "
                "chalkboard) or a recurring character carries the fun."),
        pitfalls=("The lecture script pasted onto the slides — learners read instead of listening.",
                  "A continuous stream with no practice or checks until the end.",
                  "Checks that are not checks ('Got it?').",
                  "Answers that exist only in the speaker notes — the class discusses and never sees the result.",
                  "A worked example whose givens are missing from the slide."),
        sources=("Rosenshine, Principles of Instruction (AFT)", "Gagné's nine events of instruction (NIU)",
                 "Mayer's multimedia principles (segmenting, signaling, coherence, pre-training)",
                 "worked and faded examples (MIT, EEF)", "explanatory feedback (Moreno 2004)", "retrieval practice (CMU)",
                 "OpenStax, solving problems in physics (givens before substitution)", "NIST SP 811 (italic symbols, upright units)"),
    ),
    Purpose(
        "student_presentation", "Student class / group presentation",
        "A presentation a STUDENT gives for a course. It is graded on a clear central message, credible and varied "
        "evidence, an organisation the room can follow, language for the audience and delivery (AAC&U), and course "
        "rubrics add the time limit and legible visual aids — so the deck is built for those, not for a boardroom.",
        binds_on=("class presentation", "course presentation", "course project", "group project", "group presentation",
                  "student presentation", "presentation for my class", "presentation for class", "book report",
                  "课堂汇报", "课堂展示", "课堂报告", "小组汇报", "小组展示", "小组作业", "课程汇报", "课程展示",
                  "课程报告", "课程设计答辩", "期末汇报", "期末展示", "大作业"),
        required_sections=(
            ("introduction", ("introduction", "intro", "overview", "outline", "agenda", "roadmap", "today",
                              "引言", "简介", "目录", "背景", "概述")),
            ("conclusion", ("conclusion", "in conclusion", "summary", "takeaway", "to sum up", "结论",
                            "总结", "小结")),
            ("references", ("references", "reference", "sources", "source", "bibliography", "works cited",
                            "参考文献", "参考资料", "资料来源", "来源")),
        ),
        fidelity="Every fact, figure and image comes from a source the student can name — cite it on the slide in "
                 "short form and list it at the end. An instructor treats an unsourced claim as a missing one.",
        arc=("Title + who presents which part (a name on each section divider)",
             "Hook + the central message in one sentence",
             "Roadmap: the 2–4 parts",
             "Body: each part is one claim + its evidence (data · quote · image) with its source on the same slide",
             "Conclusion: the message again, and what it means",
             "References",
             "Q&A"),
        rules=("Build for what is graded: a clear central message, credible varied supporting material, an obvious "
               "organisation, language for classmates, delivery to the room (AAC&U) — plus what course rubrics add: the "
               "time limit and visual aids that every seat can read.",
               "Fit the time: about a slide a minute at most; plan the minutes per section in the speaker notes so they "
               "add up to the limit, and split them evenly across presenters.",
               "Cite on the slide: a short author–year (Smith, 2020) next to the fact it supports — when a slide has "
               "several sources, make clear which fact is whose — and the full list at the end.",
               "Every borrowed image carries a credit line under it: title, author, source, licence.",
               "The script goes in the speaker notes; the slide carries keywords and evidence."),
        design=("Visual aids are graded on relevance and legibility from every seat — design serves those first.",
                "Evidence as visuals (chart · photo · diagram) rather than bullet lists; icons with a word beside them.",
                "Section dividers double as presenter handovers."),
        pitfalls=("Text walls read aloud.", "Running over time.", "No clear central message.",
                  "Facts or images with no source on the slide."),
        sources=("AAC&U Oral Communication VALUE rubric", "Newcastle University presentation marking criteria",
                 "Brock University, citing in presentations", "Creative Commons, attribution best practices (TASL)",
                 "Monash, group presentations"),
    ),
    Purpose(
        "client_proposal", "Client proposal / bid / RFP response",
        "Asking a client to buy a specific piece of work. The client compares it with other bids, so it must show "
        "they were understood, exactly what they get, when, and for how much.",
        binds_on=("client proposal", "proposal for a client", "proposal to a client", "consulting proposal",
                  "service proposal", "sales proposal", "rfp", "request for proposal", "tender", "bid presentation",
                  "投标", "竞标", "比稿", "客户提案", "方案提案", "提案汇报"),
        required_sections=(
            ("their goals", ("their goals", "your goals", "your challenge", "objective", "objectives", "need",
                             "needs", "situation", "需求", "痛点", "目标", "现状")),
            ("scope", ("scope", "deliverable", "deliverables", "approach", "solution", "out of scope",
                       "范围", "交付", "方案")),
            ("timeline", ("timeline", "schedule", "phase", "phases", "milestone", "milestones", "时间",
                          "排期", "里程碑", "阶段")),
            ("investment", ("investment", "pricing", "price", "fee", "fees", "cost", "budget", "quote",
                            "报价", "费用", "价格", "预算", "投入")),
        ),
        fidelity="Scope and price are promises. State what is OUT of scope and the assumptions the price rests "
                 "on — the line you leave vague is the one the client will read most generously.",
        arc=("Their situation and goals, in their words (situation appraisal)",
             "What success looks like — the measures by which they will know",
             "Our approach, in phases",
             "Scope and deliverables — what is included, what is excluded, and what the client must provide",
             "Timeline: start, end and progress checks",
             "Investment: options (a 'choice of yeses'), each with one fee, payment terms and expenses",
             "Acceptance: the decision, who signs, and a start date (credentials folded in briefly, not a full section)"),
        rules=("Mirror the client's language and priorities; the first slides are about them.",
               "Make scope explicit — inclusions, exclusions, assumptions — and list the client's own accountabilities (access, data, people).",
               "Each option carries a single fixed fee; say how payment and expenses work.",
               "Write 'will', not 'can' or 'strive'; every superlative carries its proof (a number or a case).",
               "End on one acceptance step with a date."),
        design=("Clean and confident; co-brand with the client where appropriate.",
                "A timeline / phase strip and a pricing table with the recommended option highlighted.",
                "Every graphic carries an action caption: what the client should conclude, in their terms.",
                "Case-study cards with real logos and results only, used with permission."),
        pitfalls=("A deck that is all about us.", "Vague scope, or no client accountabilities.",
                  "A price with no options or rationale.", "No closing step."),
        sources=("Alan Weiss, sample proposals (situation, measures, value, options, terms)",
                 "Shipley, seven rules for winning proposals; proposal graphics"),
    ),
    Purpose(
        "investor_pitch", "Investor / startup pitch",
        "Raising money from investors who see many decks a week and decide fast. Sequoia's outline gives the order "
        "(purpose · problem · solution · why now · market · competition · model · team · vision); Kawasaki and YC add "
        "the traction and the single ask.",
        binds_on=("investor pitch", "pitch deck", "startup pitch", "fundraising", "fund raising", "seed round",
                  "pre-seed", "series a", "series b", "demo day", "vc pitch", "pitch to investors", "pitch to vcs",
                  "融资路演", "路演", "融资", "天使轮", "商业计划书", "创业大赛", "创业比赛"),
        required_sections=(
            ("problem", ("problem", "pain", "today people", "the gap", "问题", "痛点")),
            ("market", ("market", "tam", "sam", "som", "market size", "市场", "市场规模")),
            ("business model", ("business model", "revenue model", "pricing", "how we make money", "unit economics",
                                "商业模式", "盈利模式", "收入模式")),
            ("team", ("team", "founders", "founder", "who we are", "团队", "创始人")),
            ("the ask", ("the ask", "raising", "use of funds", "we are raising", "investment", "funding",
                         "融资", "募资", "资金用途", "本轮")),
        ),
        fidelity="Every traction number is real, dated and defined (users = what, revenue = booked or "
                 "recognised). Investors diligence the deck; one inflated metric costs the whole round's trust.",
        arc=("Purpose: what the company does, in one sentence",
             "Problem", "Solution — shown in its simplest form (a short list of steps), not a busy screenshot",
             "Why now", "Market size, worked bottom-up (price × number of customers)", "Competition and alternatives",
             "Business model", "Traction", "Team",
             "The ask: one amount, the runway it buys and the milestones it reaches + vision"),
        rules=("Size by use: about ten slides plus an appendix for a presented meeting; about five self-explanatory "
               "slides for an emailed deck; five to seven for a Demo Day — and the emailed deck makes sense with no "
               "speaker (nothing only in the notes).",
               "Each slide states its conclusion — a stranger glancing at it should be able to say your idea.",
               "Answer 'why now?' and 'why this team?'.",
               "Every metric says what it counts (users = what; bookings ≠ revenue), carries its period or date, and "
               "every % growth sits next to its absolute base.",
               "One ask amount, not a range, with the milestones it buys over a stated runway."),
        design=("Legible from the back of the room: large, bold, high-contrast type, text near the top. Aim for "
                "Kawasaki's 30pt on the headline and the one number per slide; supporting text never under the detail "
                "floor (18pt body, 14pt captions).",
                "Traction as a monthly (not cumulative) chart, a labelled y-axis with its unit, a dated period, and a "
                "caption stating the conclusion.",
                "No memes or decorative transitions; a click-reveal only where it paces a punchline. One idea per slide.",
                "When the material has only dated point values (no monthly series), show those values dated — never "
                "draw a series the data does not contain."),
        pitfalls=("Dense, illegible slides.", "Cumulative charts or vanity metrics with no base.", "No clear single ask."),
        sources=("Sequoia, Writing a business plan (purpose → vision order)", "Kawasaki, the 10/20/30 rule (30pt, the ask)",
                 "YC (Hale), How to design a better pitch deck", "YC, Demo Day pitch guide", "Seibel, How to pitch your company",
                 "a16z, 16 startup metrics", "Hustle Fund, the two pitch decks founders need"),
    ),
    Purpose(
        "training", "Corporate training / onboarding / self-paced course",
        "Teaching adults to do something at work — a tool, a process, a policy, a new job. Unlike a lecture the "
        "measure is on-the-job behaviour, and many of these decks are read alone, with no trainer in the room.",
        binds_on=("corporate training", "employee training", "staff training", "sales training", "compliance training",
                  "safety training", "training session", "training deck", "training workshop", "onboarding",
                  "new hire", "new employee", "e-learning", "elearning", "self-paced",
                  "培训", "入职", "新员工", "岗前", "内训", "合规培训", "安全培训"),
        required_sections=(
            ("objectives", ("objective", "objectives", "you will be able", "by the end", "learning goal", "目标",
                            "学习目标")),
            ("practice", ("practice", "exercise", "scenario", "try it", "your turn", "role-play", "role play",
                          "练习", "演练", "情景", "实操")),
            ("knowledge check", ("knowledge check", "quiz", "check your understanding", "self-assessment",
                                 "test yourself", "测验", "自测", "小测", "考核")),
            ("recap", ("recap", "summary", "checklist", "cheat sheet", "job aid", "key points", "小结", "总结",
                       "清单", "要点")),
        ),
        fidelity="Policy, safety and compliance content is quoted from the current source document with its "
                 "version or date — a paraphrased rule that drifts from the policy trains people to break it.",
        arc=("Why this matters to you — the job situation it solves",
             "Objectives: what you will be able to do",
             "Modules, each short: concept → demo / example → practice on a realistic scenario → knowledge check",
             "Common mistakes and how to avoid them",
             "Recap + a job aid (checklist) to keep",
             "Where to get help; for onboarding, what good looks like at 30 / 60 / 90 days"),
        rules=("Task-centred: teach what they will DO on the job, with scenarios from their context.",
               "A knowledge check or scenario shows its answer on the slide after the learners commit (a click reveal, "
               "or the next slide on a self-paced deck) — never only in the notes.",
               "Feedback on each wrong option names that specific mistake and explains the right answer; feedback "
               "explains, it does not praise ('Great job!' teaches nothing).",
               "Scenario options are on-the-job actions, and the feedback shows what happens as a result.",
               "A knowledge check per module, not one quiz at the end; practice spread through the course.",
               "Self-paced decks must stand alone: descriptive headings, instructions, and navigation."),
        design=("Module dividers with a progress marker; checks share one recognisable look (deckkit.check_question).",
                "The job aid: one task, numbered steps, keywords not prose, high contrast, key points marked by shape or "
                "bold — not colour alone — and designed to be printed or screenshotted.",
                "Self-read: a linked agenda for navigation; denser text is fine but structured, never a wall."),
        pitfalls=("An information dump.", "A click-through with an end quiz nobody learns from.",
                  "Feedback that only says right or wrong.", "Generic content that never touches their actual job."),
        sources=("Clark & Mayer, e-Learning and the Science of Instruction", "ATD, design considerations for job aids",
                 "QUB digital learning, feedback in objective tests", "Cathy Moore, scenario design (practitioner)",
                 "SHRM on onboarding check-ins"),
    ),
    Purpose(
        "all_hands", "All-hands / town hall / keynote / company annual meeting",
        "A leader speaking to the whole organisation or a large audience. The job is alignment and energy: where "
        "we are, where we are going, who made it happen — and honest answers about what people are worried about.",
        binds_on=("all-hands", "all hands", "town hall", "townhall", "company meeting", "company kickoff",
                  "sales kickoff", "kickoff meeting", "kick-off meeting", "keynote speech", "keynote talk",
                  "keynote address", "annual meeting", "年会", "全员大会", "全员会", "誓师大会", "启动会", "开工大会"),
        required_sections=(
            ("agenda", ("agenda", "today", "purpose of today", "what we will cover", "议程", "今天")),
            ("updates", ("update", "updates", "progress", "results", "highlights", "this year", "进展", "回顾",
                         "成绩", "成果")),
            ("recognition", ("recognition", "thank you", "thanks", "shout-out", "kudos", "award", "welcome",
                             "感谢", "表彰", "致谢", "欢迎", "颁奖")),
            ("q&a", ("q&a", "questions", "ask me anything", "ama", "问答", "提问", "答疑")),
        ),
        fidelity="Talk to the uncertainty people already feel — changes, decisions, departures. A deck that only "
                 "celebrates reads as spin, and the room fills the silence with rumour.",
        arc=("Purpose and agenda for today — and, if you like, two or three questions right away",
             "Where we are (what is) ↔ where we are going (what could be)",
             "Updates by team or function — short, outcome-based, against the goals announced earlier",
             "Recognition: people by full name and team, each with one specific contribution",
             "The hard part: what we know, what we can change, what is still undecided and when people will hear",
             "Live Q&A",
             "Close: one rallying message or call to action"),
        rules=("Three messages at most for the room to carry out; short segments.",
               "Every metric is dated and shown against the goal it serves.",
               "Talk to the uncertainty — acknowledge reality while leaving room for optimism; a deck that only "
               "celebrates reads as spin.",
               "The Q&A slide shows how to ask (link, QR code or channel, and an anonymous option) and when unanswered "
               "questions will be answered.",
               "Mark non-public figures as internal; that part is not recorded or shared."),
        design=("People and products in photographs where you have them; big type, little text (house style).",
                "A planned 'wow' moment is optional — a keynote convention; town halls are built for dialogue.",
                "Consistent section dividers per team; celebratory but on-brand."),
        pitfalls=("Filler updates that send people to their phones.", "A staged, inauthentic tone.",
                  "Undated numbers.", "Recognition with no names or specifics."),
        sources=("SHRM on better town halls", "HBR 2025, leading an all-hands after bad news",
                 "Gallup, authentic recognition", "Lattice on all-hands (vendor)", "GitLab handbook, SAFE framework",
                 "Duarte, Resonate (what is / what could be)"),
    ),
)

# 🔴 EVERY section's own NAME is one of its terms. Sounds obvious; five sections shipped without
# it, and `job_talk/track record` reported MISSING on a deck whose slide said "My track record"
# — the section's own words. A term list assembled from synonyms forgets the word it is a synonym
# OF. `tests/test_purpose_sections.py` asserts this for every section so a new one cannot repeat it.
BY_NAME = {p.name: p for p in PURPOSES}

# 🔴 DELIVERY MODES, NOT GENRES — deliberately absent from PURPOSES, with the reason.
# A webinar is not a kind of argument; it is a kind of ROOM. The same webinar can BE a lecture, a
# product pitch or an exec readout, and those three have different required content — so a section
# list attached to "webinar" would be a guess about which one, firing on two decks out of three.
# What a webinar actually constrains is the MEDIUM (contrast, the central safe area, type size,
# icon weight), and that already lives in the lint's type floors and `formats.py`'s safe zones.
# Recording this is the difference between "we chose not to" and "nobody thought about it": a
# reader who records `webinar` gets asked WHICH GENRE it is, rather than a silent NOT CHECKED.
NOT_A_GENRE = {
    ("webinar", "online presentation", "zoom talk", "teams talk", "virtual talk", "livestream",
     "网络研讨会", "线上分享", "直播"):
        "the same session can be a lecture, a product pitch or an exec readout, and those need "
        "different content. Record the GENRE as the "
        "purpose (the medium is already handled by the type floors and the safe-area rules), e.g. "
        "'a teaching webinar' or 'an investor webinar'.",
}


def not_a_genre(recorded: str):
    """The explanation when a recorded purpose names a MEDIUM rather than a genre, else None."""
    if not recorded:
        return None
    blob = str(recorded).lower()
    for terms, why in NOT_A_GENRE.items():
        if any(t in blob for t in terms):
            return why
    return None


def match(recorded: str):
    """The Purpose a recorded purpose/goal string binds to, or None.

    Substring matching on the USER's own words, because that is all a record carries. Deliberately
    conservative: no match means NOT CHECKED, never a guessed genre — applying a clinical-case
    section list to a product pitch would be worse than checking nothing.
    """
    if not recorded:
        return None
    blob = str(recorded).lower()
    best = None
    for p in PURPOSES:
        for term in p.binds_on:
            if term in blob:
                # longest term wins: "progress review" should beat a bare "review" elsewhere
                if best is None or len(term) > best[0]:
                    best = (len(term), p)
    return best[1] if best else None


# 🔴 DETAIL FLOORS — every genre. Each one is a defect a real build shipped and a person caught by eye
# (the 压强 lesson, 2026-11-27, eight findings from one 8-slide deck). They are small, so a generator skips
# them; they are visible, so the audience does not. Printed with every brief so planner, designer and critic
# all hold the same list.
DETAIL_FLOORS = (
    "Mark tight: a ring, underline or highlight hugs the thing it marks (the option's label, the one number). "
    "A mark that has to grow to avoid its own text is marking the wrong object.",
    "One face per kind: every formula on a slide is set the same way (all equation objects or all text), every "
    "number in one face, every unit spelled one way across the deck.",
    "Results on the slide: a question, check, activity or comparison shows its answer or result ON the slide — "
    "revealed on a click, or on the next slide — never only in the speaker notes.",
    "Reproducible from the screen: a calculation, worked example or metric shows its givens, units, assumptions "
    "and as-of date on the slide; a reader who sees only the slide can redo it.",
    "Readable floor: anything the audience must read stays at presented size — body ≥ 18pt, an explanation or "
    "caption ≥ 14pt on a 13.33in-wide slide (×0.75 on the 10in canvas: 13.5pt / 10.5pt). A component that "
    "shrinks text to fit is a layout defect, not a fit.",
    "Decodable marks: an icon or device carries a word beside it or is labelled at first use; one nobody can "
    "name in a second is decoration — drop it.",
    "Scale by role: the hero is a number or a sentence; formulas, labels and furniture stay at reading size.",
    "Colour is never the only signal: a status, category or answer also carries a word, letter or shape, so it "
    "reads in greyscale and to colour-blind viewers.",
)


def resolve(text):
    """A Purpose from its registry NAME or from recorded words (`match`), else None."""
    if not text:
        return None
    key = str(text).strip().lower()
    return BY_NAME.get(key) or match(text)


def brief(p):
    """The genre's playbook as plain text — what the planner, the designer and the critic work from."""
    out = ["DECK PLAYBOOK — {}  (purpose: {})".format(p.label, p.name), "  " + p.note]
    if p.arc:
        out.append("ARC — the beats, in order (adapt the count to the time budget; never drop the order):")
        out += ["  {}. {}".format(i, b) for i, b in enumerate(p.arc, 1)]
    if p.rules:
        out.append("CONTENT RULES:")
        out += ["  - " + r for r in p.rules]
    if p.design:
        out.append("DESIGN CONVENTIONS — applied INSIDE the deck's chosen direction. They govern structure and "
                   "legibility; the preset / visual language, the bold signature moves, components and icons stay. "
                   "Never flatten the design to meet one:")
        out += ["  - " + d for d in p.design]
    if p.pitfalls:
        out.append("FAILURE MODES — the critic checks for these:")
        out += ["  - " + f for f in p.pitfalls]
    out.append("DETAIL FLOORS — every genre, every slide (each one shipped once and was caught by eye):")
    out += ["  - " + d for d in DETAIL_FLOORS]
    if p.required_sections:
        out.append("REQUIRED SECTIONS — check_purpose.py fails the hand-off if the deck names none of a section's "
                   "words: " + ", ".join(lbl for lbl, _t in p.required_sections))
    if p.fidelity:
        out.append("FIDELITY: " + p.fidelity)
    if p.sources:
        out.append("Grounded in: " + "; ".join(p.sources))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--match", default=None, help="show which purpose a recorded string binds to")
    ap.add_argument("--brief", default=None, metavar="PURPOSE",
                    help="print the playbook for a purpose NAME or the user's recorded words")
    a = ap.parse_args(argv)
    if a.brief is not None:
        p = resolve(a.brief)
        if p is None:
            why = not_a_genre(a.brief)
            print("%r binds no registered genre%s. Ask which genre it is, or pick the nearest: %s" % (
                a.brief, " — " + why if why else "", ", ".join(x.name for x in PURPOSES)))
            return 2
        print(brief(p))
        return 0
    if a.match is not None:
        p = match(a.match)
        print("%r -> %s" % (a.match, p.name if p else "no purpose bound (NOT CHECKED)"))
        return 0
    for p in PURPOSES:
        print("%-14s %s" % (p.name, p.label))
        print("               %s" % p.note)
        print("               requires: %s" % ", ".join(lbl for lbl, _t in p.required_sections))
        print("               binds on: %s" % ", ".join(p.binds_on[:6]))
        if p.fidelity:
            print("               fidelity: %s" % p.fidelity.split(".")[0])
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
