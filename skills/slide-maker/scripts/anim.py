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
        # timing is the last child of <p:sld> (after cSld / clrMapOvr / transition)
        self.slide._element.append(parse_xml(xml))
        return len(self.steps)


def slide_transition(slide, kind="fade", duration=0.5):
    """Add a simple slide-level transition (subtle; 'fade' is the safe default).
    Goes before <p:timing> in the slide; call before Build.apply() if you use both."""
    dur_ms = int(duration * 1000)
    # PowerPoint transition element; p14 fade is widely supported
    xml = (
        f'<p:transition xmlns:p="{P_NS}" '
        f'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" '
        f'spd="med" p14:dur="{dur_ms}"><p:fade/></p:transition>'
    )
    el = parse_xml(xml)
    # insert before timing if present, else append
    timing = slide._element.find(qn("p:timing"))
    if timing is not None:
        timing.addprevious(el)
    else:
        slide._element.append(el)
