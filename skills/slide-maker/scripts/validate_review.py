#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_review.py — deterministic schema check for the review-loop JSON contracts.

Validates a critic review (agents/critic.md § "Output — return ONLY this JSON") or an
arbiter payload (agents/arbiter.md Job 1 `verdicts` / Job 2 `checks`) BEFORE the
coordinator acts on it, so a malformed reply bounces back to the model with the
COMPLETE list of missing/invalid fields — one re-ask fixes everything, instead of a
ping-pong of one-error-at-a-time retries.

    python3 scripts/validate_review.py critic  review.json     # '-' reads stdin
    python3 scripts/validate_review.py arbiter verdicts.json
    python3 scripts/validate_review.py critic review.json --record ~/Downloads/<deck>/
    python3 scripts/validate_review.py --selftest

Exit 0 = valid ("OK — valid <kind> output"). Exit 1 = invalid, one line per problem.

`--record <deck-dir>` additionally writes the hand-off gate record into
`<deck-dir>/.deck-gates.json` DERIVED FROM THE VALIDATED REVIEW (verdict, blocker/major
counts, the review file's path + sha256), so `render_deck.py --deliverables` can re-read the
evidence instead of trusting a summary the model typed from memory. On an arbiter Job-2
payload it records the confirmation pass under `critic.corroborated_by`.

Stdlib only (no jsonschema): the contracts are transcribed by hand from the two agent
files — when a contract changes there, change it here too.

Critic checks: required top-level fields + types; verdict/severity/fix_risk enums; the
coverage anti-skim block (slides_opened ints · passes · stats_block_seen ·
contract_card_seen true|false|'none-declared'); plan_audit dict-or-null (null is the
direction-preview / external-no-plan escape); the optional probes block (per_slide rows
+ memory_sentence); per-finding required keys (id · slide · severity · dimension ·
issue · why · fix); and the consent rule — a "consent" verdict alongside a
blocker/major finding is a contract violation (critic.md: any blocker/major → revise).

Arbiter checks: Job 1 `verdicts` (finding_ref · real_verdict · rederivation ·
fix_verdict; better_fix required iff fix_verdict='hurts') and/or Job 2 `checks`
(finding_ref · resolved · regressions · dulled; still_wrong required iff not resolved;
better_fix required iff dulled), plus the OPTIONAL `escalated_unreviewed:
[{slide, issue}]` escalation escape hatch — accepted on either job, never required.
"""
import json
import os
import sys

GATES_FILE = ".deck-gates.json"


def _digest(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def record_gate(kind, obj, review_path, deck_dir):
    """Write the hand-off gate record FROM THE VALIDATED REVIEW, not from memory.

    The `.deck-gates.json` critic block is what `render_deck.py --deliverables` checks. If the
    model types that block itself at hand-off, the record is self-certification — the same
    failure the gate exists to prevent, because the model that skipped the loop writes the same
    JSON as the model that ran it. So the record is produced HERE, as a side effect of the
    validation the coordinator must run anyway before acting on any review, and it carries the
    review file's path + sha256 so the gate can re-read the evidence instead of trusting a
    summary. A hand-written block still passes (nothing breaks), but it is *labelled* as
    self-reported — visible, rather than indistinguishable.
    """
    if review_path == "-":
        return "not recorded: review came from stdin — pass a real file to --record"
    gates_path = os.path.join(deck_dir, GATES_FILE)
    try:
        gates = json.load(open(gates_path, encoding="utf-8"))
        if not isinstance(gates, dict):
            raise ValueError("not a JSON object")
    except FileNotFoundError:
        gates = {}
    except Exception as exc:
        return "not recorded: {} exists but is unusable ({})".format(gates_path, exc)

    rp = os.path.abspath(review_path)
    if kind == "critic":
        findings = obj.get("findings") or []
        sev = [f.get("severity") for f in findings if isinstance(f, dict)]
        prev = gates.get("critic") or {}
        seen = prev.get("reviews") or []
        if rp not in seen:
            seen.append(rp)
        gates["critic"] = {
            "verdict": obj.get("verdict"),
            # REVIEWS, not rounds. This used to write `"rounds": len(seen)` over the review FILES
            # it had seen, so the standard panel — 2 lenses x 2 rounds — recorded `rounds: 4`
            # against a cap SKILL.md states as 2. Every consumer of that number (the hand-off note,
            # the two prints in render_deck.py) then reported a deck as having run twice the rounds
            # it ran. A round is a concept only the coordinator holds: one round is N lens reviews
            # of the same build, and nothing in a review file says which round it belongs to. So
            # this records what it can actually count, and leaves `rounds` to whoever knows it —
            # preserved if already present, never invented here.
            "reviews_seen": len(seen),
            "blockers": sev.count("blocker"),
            "majors": sev.count("major"),
            "source": rp,
            "sha256": _digest(rp),
            "reviews": seen,
            "recorded_by": "validate_review.py",
        }
        if prev.get("rounds") is not None:
            gates["critic"]["rounds"] = prev["rounds"]
        if prev.get("corroborated_by"):
            gates["critic"]["corroborated_by"] = prev["corroborated_by"]
    else:  # arbiter — a Job-2 payload is the confirmation pass high-stakes consent needs
        if "checks" not in obj:
            return "not recorded: only an arbiter Job-2 `checks` payload records a confirmation"
        critic = gates.setdefault("critic", {})
        corro = critic.setdefault("corroborated_by", [])
        if rp not in corro:
            corro.append(rp)
        # A Job-2 payload can say the OPPOSITE of corroboration — the fix did not land, it dulled a
        # named strength, it regressed a neighbour. Recording only a COUNT lost that: `--gate-check`
        # printed "consent corroborated by 1 arbiter pass(es)" and exited 0 on a payload reporting
        # resolved=False + dulled=True + a regression, because the count was written by one line and
        # read by none. Keep the count (back-compatible) AND carry the open items themselves, so the
        # hand-off gate can refuse a corroboration that corroborates nothing.
        _open = [c for c in obj["checks"]
                 if isinstance(c, dict) and (c.get("dulled") or not c.get("resolved")
                                             or c.get("regressions"))]
        critic["dulled_reopened"] = len(_open)
        critic["arbiter_open"] = [{
            "finding_ref": c.get("finding_ref"),
            "resolved": bool(c.get("resolved")),
            "dulled": bool(c.get("dulled")),
            "still_wrong": c.get("still_wrong"),
            "regressions": c.get("regressions") or [],
            "from": rp,
        } for c in _open]

    with open(gates_path, "w", encoding="utf-8") as fh:
        json.dump(gates, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return "recorded -> {}".format(gates_path)


CRITIC_VERDICTS = ("consent", "revise")
SEVERITIES = ("blocker", "major", "minor")
FIX_RISKS = ("low", "medium", "high")
REAL_VERDICTS = ("real", "false_positive", "unsure")
FIX_VERDICTS = ("helps", "hurts", "neutral")

_TYPES = {
    "str": str,
    "int": int,
    "bool": bool,
    "list": list,
    "dict": dict,
}


def _is(value, typ):
    """Type check that keeps JSON semantics: a bool is NOT an int."""
    if typ == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, _TYPES[typ])


def _field(obj, key, typ, path, errors, required=True, enum=None):
    """Check obj[key] exists (when required) and has the right type/enum.

    Appends every problem to `errors` (never raises) and returns the value when it is
    usable for deeper checks, else None.
    """
    if key not in obj:
        if required:
            errors.append("%s.%s: missing (required, expected %s%s)"
                          % (path, key, typ,
                             " — one of %s" % "|".join(enum) if enum else ""))
        return None
    value = obj[key]
    if not _is(value, typ):
        errors.append("%s.%s: wrong type %s (expected %s), got %r"
                      % (path, key, type(value).__name__, typ, value))
        return None
    if enum is not None and value not in enum:
        errors.append("%s.%s: invalid value %r — expected one of %s"
                      % (path, key, value, "|".join(enum)))
        return None
    return value


def _str_list(obj, key, path, errors, required=True):
    values = _field(obj, key, "list", path, errors, required=required)
    if isinstance(values, list):
        for i, v in enumerate(values):
            if not _is(v, "str"):
                errors.append("%s.%s[%d]: must be a string, got %r" % (path, key, i, v))
    return values


# The nine per-purpose overlays in references/review-rubrics.md. A critic reads the universal
# rubric in full plus EXACTLY ONE of these — the other eight describe decks it is not reviewing.
RUBRIC_OVERLAYS = (
    "progress / lab meeting",
    "work status update",
    "academic conference talk",
    "academic job talk / faculty interview",
    "company / stakeholder presentation",
    "product description / pitch",
    "thesis / committee defense",
    "teaching / instructional",
    "conference / research poster",
)


def _rubric_overlay(obj, errors):
    """`rubric_overlay` — which per-purpose rubric section this review actually applied.

    review-rubrics.md has told critics to read one overlay and skip the other eight for a while,
    and nothing ever checked. That is the shape of instruction this skill's own enforcement
    invariant ranks last: a rule that lives only in reference prose is advisory in practice. It
    matters more than a token count, because a critic that read the WRONG overlay reviews a job
    talk against the pitch bar and reports a clean verdict either way — the failure is silent in
    exactly the place the panel exists to be loud.

    So the review names its overlay and this validator checks it. `none — <reason>` stays legal:
    a deck that matches none of the nine is real, and forcing a wrong pick would be worse than
    the gap. What is NOT legal is silence, or a bare "none" with nothing after it.
    """
    val = _field(obj, "rubric_overlay", "str", "$", errors)
    if not isinstance(val, str):
        return
    norm = val.strip().lower()
    if norm in RUBRIC_OVERLAYS:
        return
    if norm.startswith("none"):
        tail = norm[4:].lstrip(" -—:")
        if len(tail) >= 8:
            return
        errors.append("$.rubric_overlay: 'none' needs a reason after it (e.g. "
                      "'none — internal design-system deck, no purpose overlay fits'), got %r" % val)
        return
    errors.append("$.rubric_overlay: %r is not one of the nine per-purpose sections in "
                  "references/review-rubrics.md (%s), nor 'none — <reason>'"
                  % (val, ", ".join(RUBRIC_OVERLAYS)))


# The contract-card audit, by lens, exactly as agents/critic.md's output block declares it.
# These are not bookkeeping: each one is a declared design or content contract judged from the
# PIXELS. Omitting them is how a deck ships with its stated idea never checked against what got
# built — and until this gate existed, omitting them was free.
PLAN_AUDIT_FIELDS = {
    "lens_b": ("concept_landed", "skeleton_rhythm", "signature_move", "memorable_one_thing",
               "composition", "register_interiors", "money_slide", "semantic_colour",
               "type_tokens"),
    "lens_a": ("memory_sentence", "matches_deck_message", "curve_visible", "takeaway_titles",
               "motion_manifest"),
}
SIGNATURE_MOVE_FIELDS = ("verdict", "why", "proof")
COMPOSITION_FIELDS = ("cover_archetype", "home_skeleton_plurality")
# Which probe each lens owes. Lens B runs the thumbnail pass, Lens A writes the memory sentence;
# a sole critic owes both. Section critics fill per_slide for their range only, so presence is
# what is checked here, never a count.
PROBE_BY_LENS = {"lens_b": "per_slide", "lens_a": "memory_sentence"}


# The pass kinds a panel actually dispatches, and the words each is written with. `audience` is
# here because it is a REAL third critic, not a variant of the other two: review-rubrics.md gives it
# its own turf at raise-count 1 ("the audience critic owns back-of-room readability/jargon"),
# large-deck-orchestration.md dispatches it beside content and design, and critic-panel.md lists it
# as the optional third panel member. It judges the room, not the contract card, so it owes no lens
# audit — and a gate that demanded one would make the documented third critic unable to file, which
# is how an honest reviewer learns to route around the gate.
PASS_KINDS = (
    # 中文/日本語 spellings are here because this skill builds decks in any language and dispatches
    # the critic in the deck's language. A critic writing `passes: ["内容视角（全篇）", "设计视角（全
    # 篇）"]` matched no English word, so a single-lens Chinese panel critic fell through to the
    # sole-critic fallback and was asked for the OTHER lens's audit — a gate that only understands
    # English is a gate that rejects honest reviews on exactly the decks this skill advertises.
    ("lens_a", ("content", "lens a", "内容", "narrative", "fidelity", "叙事")),
    ("lens_b", ("design", "lens b", "设计", "設計", "デザイン", "layout", "版式")),
    ("audience", ("audience", "back-of-room", "back of room", "受众", "受眾", "观众")),
    # The whole-deck coherence critic of a SECTIONED panel. It is not a lens — it reads the whole
    # deck for arc and seams — and `agents/critic.md` assigns it `memory_sentence` and not
    # `per_slide`. Its pass line names content and design (it looks at both), so without this it
    # was read as a sole critic and rejected for the per-slide probe it is told not to fill.
    ("coherence", ("coherence", "seams", "连贯", "貫")),
)


def _pass_kinds(obj):
    """Which kinds of pass this review claims to have run, read off `coverage.passes`.

    The passes list is already required and already the thing the coordinator reads, so the
    audit requirement rides on the critic's own declaration rather than on a new field it
    could forget.
    """
    cov = obj.get("coverage")
    passes = cov.get("passes") if isinstance(cov, dict) else None
    out = set()
    for p in passes if isinstance(passes, list) else []:
        if not isinstance(p, str):
            continue
        low = p.lower()
        for kind, words in PASS_KINDS:
            if any(w in low for w in words):
                out.add(kind)
    return out


def _audit_owed(obj):
    """The lens audits this review owes — the one decision both audit rules key off.

    Three cases, and the third is the one worth stating. A review naming content and/or design
    owes those lenses. A review naming ONLY a non-lens pass (the audience critic) owes none. A
    review naming nothing legible is a SOLE critic and owes both — that is not a guess, it is
    `agents/critic.md`'s own rule ("if no lens is named you are the sole critic — run both lenses
    as two passes"), and reading it the other way would turn an unparseable `passes` line into a
    free exemption from the whole audit.
    """
    kinds = _pass_kinds(obj)
    if not kinds:
        return sorted(PLAN_AUDIT_FIELDS)
    return sorted(kinds & set(PLAN_AUDIT_FIELDS))


def _probes_owed(obj, lenses):
    """Which fresh-eyes probes this review owes — NOT simply one per lens.

    `agents/critic.md` splits them by ROLE, and on a sectioned deck the role is not the lens:
    "section critics fill per_slide for their slides and the whole-deck coherence critic fills
    memory_sentence". Deriving the probe from the lens alone rejected both halves of that panel —
    a per-section critic that ran both lenses over slides 4-9 was told it owed a whole-deck memory
    sentence it is not in a position to write, and the coherence critic was told it owed a
    per-slide probe it is told not to fill. `references/large-deck-orchestration.md` makes that
    panel mandatory on every ~15+ slide deck, so the whole panel bounced, and the message even
    said the probe was owed "on a full-deck review" to a review that had declared it was not one.
    """
    cov = obj.get("coverage")
    if _is(cov, "dict"):
        if cov.get("scope") is not None:
            return {"per_slide"}                  # a declared range: it did not read the whole deck
        if "coherence" in _pass_kinds(obj):
            return {"memory_sentence"}            # the whole-deck arc/seams critic of a panel
    return {PROBE_BY_LENS[lens] for lens in lenses}


def _plan_audit_subfields(obj, errors):
    """Require the audit subfields of every lens this review says it ran.

    agents/critic.md:987 tells the critic "the main loop rejects a review whose lens-required
    probe fields or plan_audit subfields are missing, exactly as it rejects `slides_opened`
    gaps". That sentence was false: the validator checked only that plan_audit was a dict, so
    `"plan_audit": {}` with `"contract_card_seen": true` and no probes at all validated clean
    and consented. Every contract the panel exists to test — did the concept land, did the
    signature move survive, does the register reach interior slides, does the remembered
    sentence match the deck message — could be skipped with nothing reporting it.

    Scoped by lens on purpose. A design-lens critic is not asked for `memory_sentence`, and a
    per-section critic is not asked to cover slides outside its range; a gate that demanded
    both from everyone would be waived on its first honest failure.
    """
    audit = obj["plan_audit"]
    lenses = _audit_owed(obj)
    if not lenses:
        return          # an audience-only pass: it judges the room, not the contract card
    for lens in lenses:
        block = audit.get(lens)
        if block is None:
            errors.append("$.plan_audit.%s: missing — `coverage.passes` says this review ran the "
                          "%s lens, so its contract-card audit is required (see agents/critic.md "
                          "'Output'). Use `\"plan_audit\": null` only when no plans exist."
                          % (lens, "content" if lens == "lens_a" else "design"))
            continue
        if not _is(block, "dict"):
            continue                                   # already reported as a type error above
        path = "$.plan_audit.%s" % lens
        for key in PLAN_AUDIT_FIELDS[lens]:
            if key not in block:
                errors.append("%s.%s: missing (required — every declared contract is judged, or "
                              "the audit is not one)" % (path, key))
        # A scalar here is not a shorthand, it is a skipped judgement — and it is the natural way
        # to degrade, because the SIBLING fields (`skeleton_rhythm`, `register_interiors`) really
        # are plain `kept|broken|degraded` strings. Guarding the nested checks on `_is(…, "dict")`
        # without an else meant `"signature_move": "landed"` passed the presence test and then
        # bought a silent exemption from `proof` — the rendered evidence the whole audit exists for.
        for key, fields in (("signature_move", SIGNATURE_MOVE_FIELDS),
                            ("composition", COMPOSITION_FIELDS)):
            if lens != "lens_b" or key not in block:
                continue
            val = block[key]
            if _is(val, "dict"):
                for sub in fields:
                    _field(val, sub, "str", "%s.%s" % (path, key), errors)
            else:
                errors.append("%s.%s: wrong type %s (expected an object with %s — a bare string "
                              "looks like the `kept|broken` fields beside it, but this one carries "
                              "the evidence, and a scalar skips every part of it)"
                              % (path, key, type(val).__name__, "/".join(fields)))
    probes = obj.get("probes")
    for probe_key in sorted(_probes_owed(obj, lenses)):
        if not _is(probes, "dict") or probe_key not in probes:
            errors.append("$.probes.%s: missing (required — this review's role owes it; a "
                          "per-section critic owes only `per_slide`, a whole-deck coherence "
                          "critic only `memory_sentence`, a lens critic the one its lens owns, a "
                          "sole critic both. Direction previews and archetype samples set "
                          "`plan_audit: null` and are exempt)" % probe_key)


def _contract_card_consistency(obj, errors):
    """`contract_card_seen: true` must be backed by an audit that used it.

    This is the cross-field rule, and it is the one that closes the hole: without it a review
    can assert it received the contract card while auditing none of its contracts. The claim
    and the work it implies now travel together.
    """
    cov = obj.get("coverage")
    if not _is(cov, "dict") or cov.get("contract_card_seen") is not True:
        return
    if "plan_audit" not in obj:
        return          # already reported as a missing required field — one error, not two
    if not _audit_owed(obj):
        return          # audience-only pass: it may hold the card as context and audit none of it
    audit = obj["plan_audit"]
    if audit is None or (_is(audit, "dict") and not audit):
        errors.append("$.plan_audit: `coverage.contract_card_seen` is true but the audit is "
                      "%s — a review that received the contract card and audited none of it is "
                      "the shape this gate exists to reject. Either audit the card, or say the "
                      "card was absent (`false` / `'none-declared'`)."
                      % ("null" if audit is None else "empty"))


# ---------------------------------------------------------------- critic ----

def validate_critic(obj):
    """Return a list of problems ([] = valid) for a critic review JSON."""
    errors = []
    if not isinstance(obj, dict):
        return ["$: critic output must be a JSON object, got %s" % type(obj).__name__]

    _field(obj, "purpose", "str", "$", errors)
    _rubric_overlay(obj, errors)

    # coverage — the anti-skim gate
    cov = _field(obj, "coverage", "dict", "$", errors)
    if isinstance(cov, dict):
        slides = _field(cov, "slides_opened", "list", "$.coverage", errors)
        if isinstance(slides, list):
            for i, v in enumerate(slides):
                if not _is(v, "int"):
                    errors.append("$.coverage.slides_opened[%d]: must be an int slide"
                                  " number, got %r" % (i, v))
        _str_list(cov, "passes", "$.coverage", errors)
        _field(cov, "stats_block_seen", "bool", "$.coverage", errors)
        if "contract_card_seen" not in cov:
            errors.append("$.coverage.contract_card_seen: missing (required — "
                          "true | false | 'none-declared')")
        elif not (_is(cov["contract_card_seen"], "bool")
                  or cov["contract_card_seen"] == "none-declared"):
            errors.append("$.coverage.contract_card_seen: invalid value %r — expected "
                          "true | false | 'none-declared'" % (cov["contract_card_seen"],))

    # plan_audit — dict of lens audits, or null (with the reason) on direction
    # previews / external no-plan decks
    if "plan_audit" not in obj:
        errors.append("$.plan_audit: missing (required — the contract-card audit dict, "
                      "or null for direction previews / external decks with no plans)")
    elif obj["plan_audit"] is not None:
        if not _is(obj["plan_audit"], "dict"):
            errors.append("$.plan_audit: wrong type %s (expected dict or null)"
                          % type(obj["plan_audit"]).__name__)
        else:
            for lens in ("lens_a", "lens_b"):
                if lens in obj["plan_audit"] and not _is(obj["plan_audit"][lens], "dict"):
                    errors.append("$.plan_audit.%s: wrong type %s (expected dict)"
                                  % (lens, type(obj["plan_audit"][lens]).__name__))
            _plan_audit_subfields(obj, errors)
    _contract_card_consistency(obj, errors)

    # probes — optional (direction previews skip it); fields are lens-scoped so each
    # is optional, but a present field must be well-formed
    if "probes" in obj:
        if not _is(obj["probes"], "dict"):
            errors.append("$.probes: wrong type %s (expected dict)"
                          % type(obj["probes"]).__name__)
        else:
            probes = obj["probes"]
            per_slide = _field(probes, "per_slide", "list", "$.probes", errors,
                               required=False)
            if isinstance(per_slide, list):
                for i, row in enumerate(per_slide):
                    row_path = "$.probes.per_slide[%d]" % i
                    if not _is(row, "dict"):
                        errors.append("%s: must be an object {slide, first_read, "
                                      "takeaway_guess}, got %r" % (row_path, row))
                        continue
                    if not _is(row.get("slide"), "int"):
                        errors.append("%s.slide: must be an int, got %r"
                                      % (row_path, row.get("slide")))
                    _field(row, "first_read", "str", row_path, errors)
                    _field(row, "takeaway_guess", "str", row_path, errors)
            _field(probes, "memory_sentence", "str", "$.probes", errors, required=False)

    verdict = _field(obj, "verdict", "str", "$", errors, enum=CRITIC_VERDICTS)
    _field(obj, "ceiling", "str", "$", errors, required=False)
    _field(obj, "summary", "str", "$", errors)
    _str_list(obj, "strengths", "$", errors)

    findings = _field(obj, "findings", "list", "$", errors)
    worst = set()
    if isinstance(findings, list):
        for i, f in enumerate(findings):
            f_path = "$.findings[%d]" % i
            if not _is(f, "dict"):
                errors.append("%s: must be an object, got %r" % (f_path, f))
                continue
            _field(f, "id", "str", f_path, errors)
            if "slide" not in f:
                errors.append("%s.slide: missing (required — int, or \"deck\" for a "
                              "deck-level finding)" % f_path)
            elif not (_is(f["slide"], "int") or f["slide"] == "deck"):
                errors.append("%s.slide: invalid value %r — expected an int or \"deck\""
                              % (f_path, f["slide"]))
            sev = _field(f, "severity", "str", f_path, errors, enum=SEVERITIES)
            if sev:
                worst.add(sev)
            for key in ("dimension", "issue", "why", "fix"):
                _field(f, key, "str", f_path, errors)
            _field(f, "fix_risk", "str", f_path, errors, required=False, enum=FIX_RISKS)

    # the consent rule: any blocker/major finding forces "revise" (critic.md)
    if verdict == "consent" and worst & {"blocker", "major"}:
        errors.append("$.verdict: 'consent' with a blocker/major finding violates the "
                      "contract — any blocker or major forces verdict 'revise'")
    return errors


# --------------------------------------------------------------- arbiter ----

def validate_arbiter(obj):
    """Return a list of problems ([] = valid) for an arbiter Job 1/Job 2 JSON."""
    errors = []
    if not isinstance(obj, dict):
        return ["$: arbiter output must be a JSON object, got %s" % type(obj).__name__]

    if "verdicts" not in obj and "checks" not in obj:
        errors.append("$: arbiter output must carry 'verdicts' (Job 1 — validate "
                      "findings) or 'checks' (Job 2 — verify fixes); neither is present")

    verdicts = _field(obj, "verdicts", "list", "$", errors, required=False)
    if isinstance(verdicts, list):
        for i, v in enumerate(verdicts):
            v_path = "$.verdicts[%d]" % i
            if not _is(v, "dict"):
                errors.append("%s: must be an object, got %r" % (v_path, v))
                continue
            _field(v, "finding_ref", "str", v_path, errors)
            _field(v, "real_verdict", "str", v_path, errors, enum=REAL_VERDICTS)
            _field(v, "rederivation", "str", v_path, errors)
            fix_verdict = _field(v, "fix_verdict", "str", v_path, errors,
                                 enum=FIX_VERDICTS)
            if fix_verdict == "hurts":
                if not _is(v.get("better_fix"), "str"):
                    errors.append("%s.better_fix: required when fix_verdict is 'hurts' "
                                  "— the corrected fix for the real problem" % v_path)
            elif "better_fix" in v and not _is(v["better_fix"], "str"):
                errors.append("%s.better_fix: must be a string, got %r"
                              % (v_path, v["better_fix"]))

    checks = _field(obj, "checks", "list", "$", errors, required=False)
    if isinstance(checks, list):
        for i, c in enumerate(checks):
            c_path = "$.checks[%d]" % i
            if not _is(c, "dict"):
                errors.append("%s: must be an object, got %r" % (c_path, c))
                continue
            _field(c, "finding_ref", "str", c_path, errors)
            resolved = _field(c, "resolved", "bool", c_path, errors)
            if resolved is False and not _is(c.get("still_wrong"), "str"):
                errors.append("%s.still_wrong: required when resolved is false — "
                              "what remains" % c_path)
            _str_list(c, "regressions", c_path, errors)
            dulled = _field(c, "dulled", "bool", c_path, errors)
            if dulled is True and not _is(c.get("better_fix"), "str"):
                errors.append("%s.better_fix: required when dulled is true — resolve "
                              "the finding WITHOUT subtracting the named strength"
                              % c_path)

    # optional escalation escape hatch — a blocker-grade issue no critic caught,
    # reported for the next critic round (never required, on either job)
    if "escalated_unreviewed" in obj:
        esc = obj["escalated_unreviewed"]
        if not _is(esc, "list"):
            errors.append("$.escalated_unreviewed: wrong type %s (expected list of "
                          "{slide, issue})" % type(esc).__name__)
        else:
            for i, e in enumerate(esc):
                e_path = "$.escalated_unreviewed[%d]" % i
                if not _is(e, "dict"):
                    errors.append("%s: must be an object {slide, issue}, got %r"
                                  % (e_path, e))
                    continue
                if "slide" not in e:
                    errors.append("%s.slide: missing (required — int, or \"deck\")"
                                  % e_path)
                elif not (_is(e["slide"], "int") or _is(e["slide"], "str")):
                    errors.append("%s.slide: invalid value %r — expected an int or "
                                  "\"deck\"" % (e_path, e["slide"]))
                _field(e, "issue", "str", e_path, errors)
    return errors


# -------------------------------------------------------------- selftest ----

def _selftest():
    """Three inline fixtures: a valid critic, a broken critic, a valid+broken arbiter."""
    good_critic = {
        "purpose": "MICCAI oral, 10 min, broad audience",
        "rubric_overlay": "academic conference talk",
        "coverage": {"slides_opened": [1, 2, 3], "passes": ["content lens (full deck)",
                                                            "design lens (full deck)"],
                     "stats_block_seen": True, "contract_card_seen": "none-declared"},
        "plan_audit": None,
        "probes": {"per_slide": [{"slide": 1, "first_read": "big title",
                                  "takeaway_guess": "the method is fast"}],
                   "memory_sentence": "4D recon in one pass; message understood"},
        "verdict": "revise",
        "summary": "Fix the cropped figure first.",
        "strengths": ["clean grid"],
        "findings": [{"id": "s2-crop-1", "slide": 2, "severity": "major",
                      "dimension": "figures", "issue": "legend clipped",
                      "why": "audience can't decode the curves",
                      "fix": "re-crop to include the legend", "fix_risk": "low"}],
    }
    errs = validate_critic(good_critic)
    assert errs == [], "valid critic flagged: %s" % errs

    bad_critic = {
        "purpose": "x",
        # coverage missing entirely
        "plan_audit": "n/a",                       # wrong type (str, not dict/null)
        "verdict": "consent",                      # consent + blocker below = violation
        "summary": "y",
        "strengths": ["ok", 42],                   # non-string strength
        "findings": [{"id": "f1", "slide": "3",    # slide as string, not int/"deck"
                      "severity": "critical",      # bad enum
                      "issue": "z"}],              # dimension/why/fix missing
    }
    errs = validate_critic(bad_critic)
    for needle in ("$.coverage: missing", "$.plan_audit: wrong type",
                   "$.strengths[1]", "$.findings[0].slide",
                   "$.findings[0].severity", "$.findings[0].dimension",
                   "$.findings[0].why", "$.findings[0].fix"):
        assert any(needle in e for e in errs), "expected %r in %s" % (needle, errs)
    assert any("$.rubric_overlay: missing" in e for e in errs), errs

    # rubric_overlay — the scoping backstop. A review must name which of the nine per-purpose
    # sections it applied; the whole point is that neither silence nor a made-up name passes.
    assert any("not one of the nine" in e for e in
               validate_critic(dict(good_critic, rubric_overlay="vibes"))), "bogus overlay passed"
    assert validate_critic(dict(good_critic, rubric_overlay="Academic Conference Talk")) == [], \
        "overlay match must be case-insensitive"
    assert validate_critic(dict(good_critic,
                                rubric_overlay="none — internal design-system deck")) == [], \
        "'none — <reason>' is a legitimate answer"
    assert any("needs a reason after it" in e for e in
               validate_critic(dict(good_critic, rubric_overlay="none"))), "bare 'none' passed"

    # ("critical" fails the enum so no severity survives; the consent rule is
    #  exercised separately with a well-typed blocker)
    consent_blocker = dict(good_critic, verdict="consent")
    consent_blocker["findings"] = [dict(good_critic["findings"][0], severity="blocker")]
    errs = validate_critic(consent_blocker)
    assert any("forces verdict 'revise'" in e for e in errs), errs

    good_arbiter = {
        "verdicts": [{"finding_ref": "s2-crop-1", "real_verdict": "real",
                      "rederivation": "source p.4 Fig 2 — legend exists, crop cuts it",
                      "fix_verdict": "hurts",
                      "better_fix": "re-crop whole figure, not just the legend strip"}],
        "escalated_unreviewed": [{"slide": 5, "issue": "headline number contradicts "
                                                       "the source table"}],
    }
    errs = validate_arbiter(good_arbiter)
    assert errs == [], "valid arbiter flagged: %s" % errs

    bad_arbiter = {
        "checks": [{"finding_ref": "s2-crop-1", "resolved": False,
                    # still_wrong missing though resolved is false
                    "regressions": "none",         # wrong type (str, not list)
                    "dulled": True}],              # better_fix missing though dulled
    }
    errs = validate_arbiter(bad_arbiter)
    for needle in ("$.checks[0].still_wrong", "$.checks[0].regressions",
                   "$.checks[0].better_fix"):
        assert any(needle in e for e in errs), "expected %r in %s" % (needle, errs)
    assert validate_arbiter({}) != [], "empty arbiter object must fail (no job payload)"

    print("selftest ok — 3 fixture groups passed")
    return 0


# ------------------------------------------------------------------- cli ----

def main(argv):
    if argv == ["--selftest"]:
        return _selftest()
    record_dir = None
    if "--record" in argv:
        i = argv.index("--record")
        if i + 1 >= len(argv):
            print("usage: --record needs the deck directory (where .deck-gates.json lives)",
                  file=sys.stderr)
            return 2
        record_dir = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 2 or argv[0] not in ("critic", "arbiter"):
        print("usage: validate_review.py critic|arbiter <file|-> [--record <deck-dir>]"
              "   (or --selftest)", file=sys.stderr)
        return 2
    kind, path = argv
    raw = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as exc:
        print("INVALID %s output — not JSON: %s" % (kind, exc), file=sys.stderr)
        return 1
    errors = (validate_critic if kind == "critic" else validate_arbiter)(obj)
    if errors:
        print("INVALID %s output — %d problem(s):" % (kind, len(errors)),
              file=sys.stderr)
        for e in errors:
            print("  - %s" % e, file=sys.stderr)
        return 1
    print("OK — valid %s output" % kind)
    if record_dir is not None:
        print("[gate] %s" % record_gate(kind, obj, path, record_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
