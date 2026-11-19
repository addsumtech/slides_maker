#!/usr/bin/env python3
"""anim — purposeful PowerPoint animations for decks built with deckkit.

python-pptx has no animation API, so this injects the slide's <p:timing> XML
directly. The model is deliberately simple and matches how a good presenter thinks:
draw your STATIC base first (titles, the always-visible scaffold), then wrap each
thing you want to *reveal on click* in a build step. Each step appears on its own
click, in order, with a tasteful fade by default.

Why click-builds (and not flying text): the point of animation in a talk is to
control attention and pace — reveal one idea at a time so the audience reads the
slide with you, not ahead of you. Motion that doesn't do that is noise. See
references/animation.md for when builds help and when to leave a slide static.

Usage (with deckkit; deckkit's helpers append shapes to the slide, so we capture
them by recording what gets added inside each step):

    from anim import Build
    b = Build(slide)
    # ... draw static base normally (always visible) ...
    with b.step():            # click 1 reveals everything drawn in this block
        chip(s, ...); arrow(s, ...)
    with b.step():            # click 2
        callout(s, ...)
    b.apply(effect="fade")    # default fade; also "appear", "wipe"

Verification caveat: render_deck.sh (LibreOffice) shows the FINAL built state only —
it cannot play the build sequence, and neither can the static-PNG critic. So (1)
make sure the fully-built slide reads correctly on its own (the PNG must be complete),
and (2) tell the user / note the intended click order. Confirm playback in real
PowerPoint / Keynote, which read this timing XML.
"""
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
import contextlib

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"

# effect name -> (presetID, animEffect filter or None for "appear")
_EFFECTS = {
    "fade":   (10, "fade"),
    "appear": (1,  None),
    "wipe":   (22, "wipe(up)"),
}
_SHAPE_TAGS = {qn("p:sp"), qn("p:pic"), qn("p:graphicFrame"),
               qn("p:cxnSp"), qn("p:grpSp")}


class Build:
    """Records click-reveal build steps on one slide and writes its timing XML."""

    def __init__(self, slide):
        self.slide = slide
        self._spTree = slide.shapes._spTree
        self.steps = []          # list of [spid, spid, ...] — one entry per click
        self._id = 3             # cTn ids 1 (tmRoot) and 2 (mainSeq) are reserved

    def _nid(self):
        v = self._id
        self._id += 1
        return v

    @contextlib.contextmanager
    def step(self):
        """Everything drawn inside this block reveals together on the next click."""
        before = len(self._spTree)
        yield
        new = list(self._spTree)[before:]
        spids = []
        for el in new:
            if el.tag not in _SHAPE_TAGS:
                continue
            cnv = el.find(".//" + qn("p:cNvPr"))
            if cnv is not None and cnv.get("id"):
                spids.append(cnv.get("id"))
        if spids:
            self.steps.append(spids)

    # -- XML construction -------------------------------------------------
    def _effect_xml(self, spid, node_type, preset_id, filt, dur_ms):
        anim = ""
        if filt is not None:
            anim = (f'<p:animEffect transition="in" filter="{filt}">'
                    f'<p:cBhvr><p:cTn id="{self._nid()}" dur="{dur_ms}"/>'
                    f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr>'
                    f'</p:animEffect>')
        return (
            f'<p:par><p:cTn id="{self._nid()}" presetID="{preset_id}" '
            f'presetClass="entr" presetSubtype="0" fill="hold" grpId="0" '
            f'nodeType="{node_type}"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst>{anim}'
            f'<p:set><p:cBhvr><p:cTn id="{self._nid()}" dur="1" fill="hold">'
            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            f'<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>'
            f'</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
            f'</p:childTnLst></p:cTn></p:par>'
        )

    def _step_xml(self, spids, preset_id, filt, dur_ms):
        effects = "".join(
            self._effect_xml(spid, "clickEffect" if i == 0 else "withEffect",
                             preset_id, filt, dur_ms)
            for i, spid in enumerate(spids)
        )
        return (
            f'<p:par><p:cTn id="{self._nid()}" fill="hold">'
            f'<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{self._nid()}" fill="hold">'
            f'<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst>{effects}</p:childTnLst></p:cTn></p:par>'
            f'</p:childTnLst></p:cTn></p:par>'
        )

    def apply(self, effect="fade", duration=0.5):
        """Write the timing XML for the recorded steps onto the slide.

        effect: 'fade' (default, tasteful), 'appear' (instant), or 'wipe'.
        duration: seconds per reveal.
        Returns the number of build steps written (0 = nothing recorded)."""
        if not self.steps:
            return 0
        if effect not in _EFFECTS:
            raise ValueError(f"unknown effect {effect!r}; use one of {list(_EFFECTS)}")
        preset_id, filt = _EFFECTS[effect]
        dur_ms = int(duration * 1000)
        steps_xml = "".join(self._step_xml(s, preset_id, filt, dur_ms) for s in self.steps)
        xml = (
            f'<p:timing xmlns:p="{P_NS}" xmlns:a="{A_NS}"><p:tnLst>'
            f'<p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
            f'<p:childTnLst><p:seq concurrent="1" nextAc="seek">'
            f'<p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            f'{steps_xml}'
            f'</p:childTnLst></p:cTn>'
            f'<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            f'<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
            f'</p:seq></p:childTnLst></p:cTn></p:par>'
            f'</p:tnLst></p:timing>'
        )
        # 🔴 CT_Slide allows exactly ONE <p:timing> (maxOccurs=1) and orders its children
        # cSld, clrMapOvr?, transition?, timing?, extLst? — so this can neither append blindly
        # nor add a second one.
        #
        # It used to do both. Measured: two `Build(s)` on one slide, each calling apply(), left
        # `['cSld', 'clrMapOvr', 'timing', 'timing']`; `prs.save()` raised nothing, LibreOffice
        # rendered it happily, `lint_layout` reported clean, and `preflight_check.py` — which
        # only asks whether the string 'p:timing' appears — read the duplicate as *more*
        # compliant. PowerPoint is the one consumer that enforces the schema, so the first
        # signal would have been a user seeing "PowerPoint found a problem and needs to repair".
        # That is the failure class no gate in this toolkit could see: every check is geometric,
        # pixel-based or semantic, and none of them looks at whether the part is well-formed
        # against ECMA-376.
        #
        # A second apply() on one slide is a BUILD ERROR, not something to merge: the steps of
        # the second Build were never in the first one's sequence, so silently keeping either
        # tree ships a deck whose click order is not what the author wrote.
        sld = self.slide._element
        if sld.find(qn("p:timing")) is not None:
            raise ValueError(
                "anim: this slide already carries a <p:timing> — Build.apply() ran twice on it. "
                "CT_Slide allows exactly one, and a second one makes the file schema-invalid: "
                "PowerPoint refuses to open it while python-pptx, LibreOffice and every lint "
                "here stay silent. Use ONE Build per slide and put every beat in its steps.")
        node = parse_xml(xml)
        ext = sld.find(qn("p:extLst"))
        if ext is not None:
            ext.addprevious(node)          # timing precedes extLst — append would invert them
        else:
            sld.append(node)
        return len(self.steps)


# The slide-level transitions this writes. Deliberately short: SKILL.md's motion rule is that
# transitions are "optional, secondary, off the critical path" and a deck with none plus good
# appear-builds beats one with a fade on every slide — so this is a small set of calm, widely
# supported elements, not a catalogue. `cut` is the honest way to say "no transition, explicitly".
_TRANSITIONS = {
    "fade": "<p:fade/>",
    "cut": "<p:cut/>",
    "wipe": '<p:wipe dir="d"/>',
    "push": '<p:push dir="u"/>',
}


_MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"
_P159_NS = "http://schemas.microsoft.com/office/powerpoint/2015/09/main"
_P14_NS = "http://schemas.microsoft.com/office/powerpoint/2010/main"


def _place_transition(slide, el):
    """Put a transition where CT_Slide wants it: after clrMapOvr, before timing and extLst."""
    sld = slide._element
    if sld.find(qn("p:transition")) is not None or sld.find("{%s}AlternateContent" % _MC_NS) is not None:
        raise ValueError("this slide already carries a transition — one per slide")
    for tag in ("p:timing", "p:extLst"):
        nxt = sld.find(qn(tag))
        if nxt is not None:
            nxt.addprevious(el)
            return
    sld.append(el)


def morph(slide, duration=1.6):
    """PowerPoint MORPH into this slide from the previous one — the cinematic move between two pages.

    Morph animates every object the two slides share: a number grows into the hero, a diagram
    assembles part by part, a photograph pushes in, a map pans. PowerPoint pairs objects BY OBJECT
    (same picture, same text, same shape type); name a pair with `morph_key()` when the match must be
    forced (a box that becomes a different box). Spend it on 1-3 beats a deck exists for — the
    reveal, the turn, the peak — never on every slide: a morph everywhere is a screensaver.

    Written as `mc:AlternateContent` with a FADE fallback, so viewers without Morph (Keynote,
    LibreOffice, older PowerPoint) still get a calm fade and the file stays valid. 🔴 The render
    check cannot see it — LibreOffice draws the two end states only; confirm the motion in
    PowerPoint itself (`morph_slides(prs)` lists which slides carry one)."""
    ms = int(duration * 1000)
    xml = ('<mc:AlternateContent xmlns:mc="{mc}"><mc:Choice xmlns:p159="{p159}" Requires="p159">'
           '<p:transition xmlns:p="{p}" xmlns:p14="{p14}" spd="slow" p14:dur="{ms}">'
           '<p159:morph option="byObject"/></p:transition></mc:Choice>'
           '<mc:Fallback><p:transition xmlns:p="{p}" spd="slow"><p:fade/></p:transition></mc:Fallback>'
           '</mc:AlternateContent>').format(mc=_MC_NS, p159=_P159_NS, p=P_NS, p14=_P14_NS, ms=ms)
    _place_transition(slide, parse_xml(xml))


def morph_key(shape, key):
    """Force Morph to pair this shape with the one carrying the same key on the neighbouring slide.

    PowerPoint's rule: two shapes whose names both start with `!!` and are otherwise identical are
    morphed into each other whatever they look like. Refuses a shape that carries a deckkit tag in
    its name (chrome, bleed, motif, overlap…) — those names are lint declarations and renaming would
    erase them; key a plain shape, or let Morph match by object."""
    k = str(key or "").strip()
    if not k or any(c in k for c in ":|"):
        raise ValueError("morph_key(): give a short plain key like 'hero' (no ':' or '|')")
    name = str(getattr(shape, "name", "") or "")
    if name.startswith("deckkit") or ":" in name or "+" in name.split(" ")[0]:
        raise ValueError("morph_key(): {!r} carries a deckkit tag in its name — key a plain shape, or rely "
                         "on Morph's by-object matching".format(name[:60]))
    shape.name = "!!" + k
    return shape


def morph_slides(prs):
    """1-based numbers of the slides that morph in — for the hand-off note and a PowerPoint check."""
    out = []
    for i, s in enumerate(prs.slides, 1):
        if s._element.find(".//{%s}morph" % _P159_NS) is not None:
            out.append(i)
    return out


def slide_transition(slide, kind="fade", duration=0.5):
    """Add a simple slide-level transition (subtle; 'fade' is the safe default).

    `kind` is one of 'fade' | 'cut' | 'wipe' | 'push' — for the cinematic move use `morph()`. Goes
    before <p:timing> in the slide; call before Build.apply() if you use both."""
    if kind not in _TRANSITIONS:
        # Raise rather than fall back. `kind` was accepted and never read for as long as this
        # function existed — grep found it exactly once in the file, in the signature — while the
        # body hardcoded <p:fade/>, so every deck that asked for 'push' silently got a fade and
        # nothing anywhere said so. A wrong name must now be louder than a wrong result.
        raise ValueError("slide_transition(kind={!r}): unknown transition. One of: {}."
                         .format(kind, " · ".join(sorted(_TRANSITIONS))))
    dur_ms = int(duration * 1000)
    # PowerPoint transition element; p14 timing attr is widely supported
    xml = (
        f'<p:transition xmlns:p="{P_NS}" '
        f'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" '
        f'spd="med" p14:dur="{dur_ms}">{_TRANSITIONS[kind]}</p:transition>'
    )
    el = parse_xml(xml)
    # insert before timing if present, else append
    timing = slide._element.find(qn("p:timing"))
    if timing is not None:
        timing.addprevious(el)
    else:
        slide._element.append(el)
