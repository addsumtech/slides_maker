# Schematic diagrams — drawing a labelled science schematic faithfully

`form-selection.md` already tells you **when** to reach for a schematic: a **principle ·
mechanism · experiment · definition** you're *explaining* (physics · chemistry · biology ·
engineering · econ · any subject) wants a **labelled diagram beside a short text description**,
not text alone, and the critic checks for it (`review-rubrics.md`, `critic.md`). This file is the
**how** — the part the diagram-kit (`node`/`connector`/`hub_spoke`/`flow_chain`) does *not* cover,
because those draw **boxes-and-arrows** (architectures, flows, frameworks), not the **physical /
spatial** picture of a force balance, a ray path, a circuit, or an apparatus.

The whole point of a schematic is **fidelity**: a wrong or generic box-and-dot cartoon of a
physical setup is *worse than none* — an expert (a supervisor, a class, a committee) spots a
flipped lens, a mis-labelled force, or a backwards reaction instantly. So the rule throughout is:
**build the real geometry/connections, label them correctly, and verify against the source.**

## 1 — Which tool: pick before you draw

| The schematic is… | Use | Why |
|---|---|---|
| **Conceptual box-flow** — modules, stages, a pipeline, a cause→effect graph, a framework | deckkit **native** kit: `node`+`connector`/`flow_chain`/`elbow_connector`/`loop_path`/`hub_spoke`/`step_list`/`concentric_rings` | editable PowerPoint shapes, on-brand, no external render; this is the *default* for anything that's really boxes joined by arrows |
| **Precise / label-critical physical schematic** — free-body & force diagram, optics ray path, electric circuit, exact vector/coordinate geometry, wave/field where the geometry is load-bearing | **matplotlib** (or a domain library) → transparent PNG → `deckkit.picture(fit="contain")` | full control of geometry, true arrowheads, angle arcs, axes, hatching, LaTeX labels; deterministic, editable, correct-by-construction — when **the exact geometry/labels ARE the meaning**, this is the safe default (and the only fully-faithful path) |
| **Rich / stylized / illustrative schematic** — a polished apparatus or experiment scene, a conceptual mechanism, a "hero" explainer, anything that must **match a generated-template's look** or where the user wants something **fancy** and the exact geometry is *not* load-bearing | **OpenAI / image tool** for the text-free *visual*, then **overlay the labels as editable native text + leader lines** (§1b) | a flat line drawing looks out of place in a richly-styled or image-generated deck; the image tool gives a far more polished, on-brand illustration. Safe **only** with the §1b guardrails (labels stay native, geometry verified) |
| **It must look like the *real* thing** — a *specific* molecule, a real micrograph, an actual instrument photo, a real plot of real numbers | **extract** the real figure (`extract_pdf.py`) or **compute** the real artifact (numpy/scipy/scikit-image/RDKit/a domain lib); see `image-generation.md` | a schematic *abstracts*; when the audience needs the genuine object, show the genuine object, whole — the image tool would fabricate a wrong one |
| **The law/relation IS the content** (F = ma, a rate law, a transform) | `equation_png` (typeset math) — often *beside* the schematic | the equation is the precise statement; the schematic gives the intuition. Frequently **both** |

**Choosing between matplotlib and the image tool** is the key call: it's the same **precision ↔ polish**
trade-off as native-chart vs generated-plate. Reach for **matplotlib/domain-lib** when the schematic is
*simple-to-moderate and the exact geometry or labels carry the meaning* (a ray diagram, a circuit, a
force balance — being *right* is the whole job). Reach for the **image tool** when the schematic is
*complex, wants to look fancy, or must sit naturally inside a stylized / generated-template deck* and the
exact geometry is illustrative rather than load-bearing — but **only with the §1b guardrails**, because a
generated schematic is faithful *only* if you keep the labels native and verify the picture is right.

**The one hard rule — never bake the LABELS (or load-bearing geometry you can't verify) into a
generated image.** Image tools garble text (misspelled, uneditable, off-brand) and will happily draw
*wrong physics* — a lens that converges the wrong way, a tripod with three legs that needs four, a
garbled circuit. So a generated schematic is acceptable **only** when (a) its labels are added back as
**native editable text**, not baked pixels, and (b) you've **looked at the picture and confirmed the
geometry/topology is domain-correct** (regenerating until it is). When the geometry itself *must* be
exact and you can't reliably art-direct it — a specific circuit topology, an exact ray path, a precise
free-body diagram — **use matplotlib/a domain library instead**; overlaying correct labels can't fix a
picture that's drawn wrong. (This is the same principle as everywhere else in the skill: text, labels,
numbers, and evidence stay editable objects on top of imagery, never inside it — `image-generation.md`.)

## 1b — The image-tool path: generate the visual, keep the labels native

When you've chosen the image tool (rich / stylized / template-matched schematic, geometry not
load-bearing), follow this so it stays faithful:

1. **Art-direct a TEXT-FREE illustration.** Prompt the *physical scene / apparatus / mechanism* in the
   deck's visual style (match a generated template's palette + render style — reuse its `style.py` /
   image-prompt motif), and **explicitly ask for no text, no labels, no numbers, no arrows-with-words**.
   Leave **calm, uncluttered zones** where the labels and leader lines will go. Generate with the
   existing pipeline — `scripts/image_prompts.py` to build the manifest, then `generate_images_codex.py`
   (no-key, native imagegen) or `generate_images_openai.py` (API fallback); see `image-generation.md`.
2. **VERIFY the geometry before using it.** Open the PNG and check the physics/chemistry/topology is
   *correct* (the lens/mirror curvature & ray sense, the apparatus parts & connections, counts,
   relative sizes). Wrong → regenerate with a sharper prompt, or fall back to matplotlib. A pretty but
   wrong schematic is worse than a plain correct one.
3. **Place it whole** with `deckkit.picture(fit="contain")`, then **overlay every label as native
   editable text** (`deckkit.text`) with **leader lines/arrows** (`deckkit.connector`/`arrow`) pointing
   from the label to the feature — correct spelling, deck font, deck language, ≥4.5:1 contrast, sized to
   read. Symbols in math format (`equation_png`/`eq_par`). These labels are the schematic's *meaning*
   and they stay yours, not the model's.
4. **Keep it reproducible** — the prompt + the label/leader placement live in the build script; the PNG
   sits in `~/Downloads/<deck>/assets/generated/`.

Net: the **image tool supplies the styled picture; you supply the correct, editable labels** — the same
"AI = background, real content = native objects on top" division the skill uses for generated templates
and content plates. The §5 fidelity gate still applies in full.

**Domain libraries beat hand-drawing when one exists** — reach for the real tool and place its
output whole: `RDKit`/`pysmiles` (molecules from SMILES), `schemdraw` (publication circuits),
`SchemDraw`/`lcapy` (circuits with analysis), `networkx`+matplotlib (graphs), `matplotlib` patches
(everything else). If the deck's environment has the domain library, prefer it — it's *more*
accurate than improvising patches.

## 2 — House style for every matplotlib schematic

Match the deck so the schematic reads as *part of* it, not a pasted-in textbook scan:

- **Transparent background** (`savefig(..., transparent=True)`) so it sits on any slide fill.
- **Deck palette** — pass your `style`'s `ACCENTS`/ink colours in; one accent carries the *focus*
  (the force you're explaining, the ray that matters), everything else a neutral ink/grey. Same
  one-accent discipline as the charts.
- **Ink colour to the surface** — dark line-work + dark labels on a light deck; light (`#E8ECF0`)
  on a dark deck (pass a `dark` flag, like `designed_charts.py`).
- **Fonts** — set `font` to the deck's face; on a **CJK / non-Latin** deck pass `deckkit.EAFONT`
  first in the font stack (copy the `_available_cjk()` pattern from `designed_charts.py`) or labels
  render as tofu. Math labels use mathtext (`r"$\vec{F}_g$"`).
- **Label size to read at slide scale** — a schematic is placed ~4–6 in wide; set label fontsize
  so it lands ≈ the deck's **body** size on the slide (test in the render), never tiny.
- **No title baked in** — the slide's assertion title + a one-line caption do that job (and stay
  editable). Bake in only the diagram's own intrinsic labels (force names, node values, axis units).
- **High DPI** (`dpi=200–300`) so line-work is crisp when scaled.
- **`ax.set_aspect('equal')`** for anything with real geometry (force diagrams, optics, circuits) so
  angles and lengths aren't distorted; turn the axis frame off (`ax.axis('off')`) unless axes ARE
  the point (coordinate geometry).
- **Draw an AGGREGATE separate from its constituents.** When the schematic shows a net/resultant/total
  alongside the parts that produce it (a net magnetization among spin arrows, a resultant among component
  vectors, a centroid among points), do NOT draw it *inside* the cluster — it then reads as just another
  component. Give it its own zone, connect the group to it with an explicit operator (`⇒`/`Σ`/`=`/arrow),
  and make it the focal accent (heavier/coloured). See `design-principles.md` "Show an aggregate separate
  from its constituents."

Shared canvas helper (copy into the build script, adapt per recipe):

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Arc, Circle, Rectangle, Polygon

def _canvas(w=6, h=4, dark=False, font="Helvetica Neue"):
    plt.rcParams["font.family"] = font          # prepend deckkit.EAFONT for a CJK deck
    fig, ax = plt.subplots(figsize=(w, h), dpi=240)
    ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_alpha(0)                        # transparent
    return fig, ax

INK   = "#E8ECF0"   # dark-deck ink  (use "#1B2430" on a light deck)
MUT   = "#8A93A0"
def save(fig, path):
    fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.05); plt.close(fig)
```

## 3 — Recipes (copy, adapt the geometry/labels to the source)

Each returns a transparent PNG you place with `deckkit.picture(slide, x, y, w, png, fit="contain")`.
**Adapt the numbers to the actual setup you're explaining** — these are scaffolds, not fixed art.

### Free-body / force diagram (physics)
A block on an incline; gravity, normal, friction. The *accurate* part is the directions and the
angle — get them right.

```python
import numpy as np
def force_diagram(path, theta_deg=30, accent="#76B900", dark=True, font="Helvetica Neue"):
    fig, ax = _canvas(5.5, 4, dark, font); ink = INK if dark else "#1B2430"
    th = np.radians(theta_deg)
    # incline (ground hatch via a thick line + short ticks)
    x0,y0 = 0,0; L=4.2
    ax.plot([x0, x0+L*np.cos(th)], [y0, y0+L*np.sin(th)], color=ink, lw=2)
    for t in np.linspace(0.1, 0.95, 9):                      # hatching under the slope
        bx,by = x0+t*L*np.cos(th), y0+t*L*np.sin(th)
        ax.plot([bx, bx-0.18], [by, by-0.18], color=MUT, lw=1)
    # block (a rotated square on the slope)
    cx,cy = x0+2.0*np.cos(th), y0+2.0*np.sin(th)
    s=0.7; ang=th
    R=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])
    sq=np.array([[-s,-0.0],[s,-0.0],[s,2*s],[-s,2*s]]).T*0.5
    sq=(R@sq).T+[cx,cy]
    ax.add_patch(Polygon(sq, closed=True, fc="none", ec=ink, lw=1.8))
    bc = sq.mean(0)                                          # block centre = force origin
    def vec(dx,dy,c,lab,lx=0,ly=0):
        ax.add_patch(FancyArrowPatch(bc,(bc[0]+dx,bc[1]+dy),color=c,lw=2.2,
                     arrowstyle="-|>",mutation_scale=18))
        ax.text(bc[0]+dx+lx, bc[1]+dy+ly, lab, color=c, fontsize=15, ha="center", va="center")
    vec(0,-1.5, accent, r"$\vec{F}_g = m\vec{g}$", ly=-0.18)     # gravity: straight down (the focus)
    n=1.3; vec(-n*np.sin(th), n*np.cos(th), ink, r"$\vec{N}$", lx=-0.18)   # normal: ⟂ to slope
    f=1.0; vec(-f*np.cos(th), -f*np.sin(th), ink, r"$\vec{f}$", ly=-0.2)   # friction: down-slope
    ax.add_patch(Arc((x0,y0),1.4,1.4,theta1=0,theta2=theta_deg,color=MUT,lw=1.2))
    ax.text(x0+0.95, y0+0.22, rf"$\theta={theta_deg}°$", color=MUT, fontsize=12)
    ax.autoscale_view(); save(fig, path)
```
*Fidelity check:* normal ⟂ to the surface, gravity vertical, friction opposes motion, the angle arc
matches the incline. A force that points the wrong way is the classic, fatal error here.

### Optics ray diagram (converging lens)
Object → lens → real inverted image, three principal rays. Get the ray rules right.

```python
def ray_diagram(path, f=1.6, do=3.4, accent="#76B900", dark=True, font="Helvetica Neue"):
    fig, ax = _canvas(7, 3.6, dark, font); ink = INK if dark else "#1B2430"
    ax.axhline(0, color=MUT, lw=1)                                   # principal axis
    ax.plot([0,0],[-1.6,1.6], color=ink, lw=2)                       # lens
    ax.annotate("", (0,1.55),(0,1.75), arrowprops=dict(arrowstyle="<->",color=ink,lw=1.4))
    for s in (1,-1):                                                 # foci & 2F
        for m,lab in [(f,"F"),(2*f,"2F")]:
            ax.plot(s*m,0,"o",color=MUT,ms=3)
            ax.text(s*m,-0.22, lab, color=MUT, fontsize=11, ha="center")
    ho=1.1                                                            # object (upright arrow, left)
    ax.add_patch(FancyArrowPatch((-do,0),(-do,ho),color=ink,lw=2.4,arrowstyle="-|>",mutation_scale=16))
    di = 1/(1/f - 1/do); hi = -ho*di/do                              # thin-lens eqn (the real geometry)
    ax.add_patch(FancyArrowPatch((di,0),(di,hi),color=accent,lw=2.4,arrowstyle="-|>",mutation_scale=16))
    # three principal rays — all meet at the image tip (di, hi)
    ax.plot([-do,0,di],[ho,ho,hi], color=accent, lw=1.3)             # 1) parallel in → through far focus F'
    ax.plot([-do,di],[ho,hi], color=MUT, lw=1.1)                     # 2) straight through the optical centre
    ax.plot([-do,0,di],[ho,hi,hi], color=MUT, lw=1.1)               # 3) through near focus F → parallel out
    ax.text(-do,ho+0.18,"object",color=ink,fontsize=12,ha="center")
    ax.text(di,hi-0.22,"real image",color=accent,fontsize=12,ha="center")
    ax.set_xlim(-do-0.6, di+0.8); ax.set_ylim(-1.8,1.9); save(fig, path)
```
*Fidelity check:* image distance from the **thin-lens equation** (1/f = 1/do + 1/di), not eyeballed;
a real image is **inverted** and on the far side; the parallel ray bends through the far focus.

### Electric circuit
Prefer **`schemdraw`** if available (publication-grade, trivial) — *its element API varies by version,
so check `schemdraw.elements` for the exact names*:
```python
import schemdraw, schemdraw.elements as e
d = schemdraw.Drawing()
d += e.SourceV().label("9 V"); d += e.Resistor().right().label("R₁")
d += e.Resistor().down().label("R₂"); d += e.Line().left(); d += e.Line().up()
d.save(path, transparent=True)
```
Hand-drawn fallback: place resistor (zig-zag `ax.plot`), battery (long/short bars), wires
(straight lines on a grid), junction dots (`ax.plot('o')`); keep wires orthogonal, label each
component, mark current direction with one arrow. *Check polarity and series/parallel topology.*

### Chemistry apparatus + reaction
Apparatus (round-bottom flask, condenser, beaker) from patches; **reactions** as a labelled arrow,
not a sketch:
```python
def reaction_arrow(path, lhs=r"$2H_2 + O_2$", rhs=r"$2H_2O$", over="", under="", accent="#76B900",
                   dark=True, font="Helvetica Neue"):
    fig, ax = _canvas(6, 1.3, dark, font); ink = INK if dark else "#1B2430"
    ax.text(0.04,0.5, lhs, fontsize=20, color=ink, va="center", transform=ax.transAxes)
    ax.annotate("", (0.62,0.5),(0.40,0.5), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=ink, lw=1.8))
    if over:  ax.text(0.51,0.62, over,  fontsize=11, color=MUT, ha="center", transform=ax.transAxes)
    if under: ax.text(0.51,0.34, under, fontsize=11, color=MUT, ha="center", transform=ax.transAxes)
    ax.text(0.96,0.5, rhs, fontsize=20, color=accent, va="center", ha="right", transform=ax.transAxes)
    ax.set_xlim(0,1); ax.set_ylim(0,1); save(fig, path)
```
For a **specific molecule** use **RDKit** (`Draw.MolToImage(Chem.MolFromSmiles(...), ...)`) — never
hand-draw a named structure; for *apparatus*, patches are fine. *Check the equation balances and the
arrow points reactants→products* (⇌ for equilibrium: two half-arrows).

### Vector / coordinate geometry (math, mechanics)
Here the **axes ARE the content** — keep them (don't `axis('off')`):
```python
def vector_sum(path, a=(3,1), b=(1,2.4), accent="#76B900", dark=True, font="Helvetica Neue"):
    fig, ax = _canvas(5,4.5, dark, font); ink = INK if dark else "#1B2430"
    ax.axis("on"); [ax.spines[s].set_visible(False) for s in ("top","right")]
    ax.spines["left"].set_color(MUT); ax.spines["bottom"].set_color(MUT)
    ax.axhline(0,color=MUT,lw=0.8); ax.axvline(0,color=MUT,lw=0.8)
    def v(p0,p1,c,lab):
        ax.add_patch(FancyArrowPatch(p0,p1,color=c,lw=2.4,arrowstyle="-|>",mutation_scale=18))
        ax.text((p0[0]+p1[0])/2, (p0[1]+p1[1])/2+0.15, lab, color=c, fontsize=15)
    v((0,0),a,ink,r"$\vec{a}$"); v(a,(a[0]+b[0],a[1]+b[1]),MUT,r"$\vec{b}$")
    v((0,0),(a[0]+b[0],a[1]+b[1]),accent,r"$\vec{a}+\vec{b}$")     # resultant = the focus
    ax.set_xlim(-0.4,5); ax.set_ylim(-0.4,4.2); ax.set_xticks([]); ax.set_yticks([]); save(fig, path)
```

### Wave / field / signal
Use real `numpy` so the wave is *true* (dense `linspace`, never integer steps — an under-sampled
sine aliases into zig-zags; see SKILL.md "make the plot actually look CORRECT"):
```python
import numpy as np
def wave(path, accent="#76B900", dark=True, font="Helvetica Neue"):
    fig, ax = _canvas(6.5,3, dark, font); ink = INK if dark else "#1B2430"; ax.axis("on")
    [ax.spines[s].set_visible(False) for s in ("top","right")]
    x = np.linspace(0, 4*np.pi, 1000)                      # dense → smooth
    ax.plot(x, np.sin(x), color=accent, lw=2.2)
    ax.annotate("", (np.pi/2, 1.18),(np.pi/2,1.0), arrowprops=dict(arrowstyle="<->",color=MUT,lw=1))
    ax.annotate(r"amplitude $A$", (np.pi/2,0.5), color=MUT, fontsize=12)
    ax.annotate("", (np.pi/2, -0.05),(np.pi/2+2*np.pi,-0.05),
                arrowprops=dict(arrowstyle="<->",color=MUT,lw=1)); 
    ax.text(np.pi/2+np.pi,-0.32, r"wavelength $\lambda$", color=MUT, fontsize=12, ha="center")
    ax.set_xticks([]); ax.set_yticks([]); save(fig, path)
```

## 4 — Placement & layout on the slide

- **Schematic + text, side by side** is the default form (`form-selection.md` row 28): the diagram in
  one `columns(2)` half (or as the hero), 2–4 short labelled takeaways in the other — *not* the
  schematic alone and *not* text alone.
- Place with **`picture(fit="contain")`** so geometry is never cropped or stretched (a squashed force
  diagram lies about the angle).
- Give the slide an **assertion title** (the principle it shows) + a **one-line caption** pointing to
  what to look at ("the normal force balances only the perpendicular component").
- **Animation:** a schematic with parts is a natural **appear-build** — reveal the setup, then each
  force/ray/stage on click (`anim.py`, `references/animation.md`). It must still read correct fully-built.
- Keep every PNG in `~/Downloads/<deck>/assets/` and the **drawing code in the build script** — a
  matplotlib schematic is a raster, so "editing" = re-running the function, exactly like `equation_png`.

## 5 — The fidelity gate (do this before the critic)

A schematic is a **claim about how something works**, so it gets the same scrutiny as a number:

1. **Domain-accurate** — directions, geometry, topology, connections, reaction direction, ray rules,
   polarity are physically/chemically correct and **faithful to the source** (transcribe the setup the
   paper/textbook shows; don't invent a plausible-looking one).
2. **Computed where it can be** — image distance from the lens equation, a wave from real `numpy`, a
   molecule from its SMILES — not eyeballed, so it can't be subtly wrong.
3. **Every part labelled, correctly** — no unlabelled mystery arrow; labels in math format for symbols
   (`$\vec{F}$`, `$\lambda$`), spelled right, in the deck's language.
4. **View the rendered PNG and re-check** — aliasing, an occluding label, a clipped arrowhead, a
   distorted aspect, tofu glyphs. A wrong-*looking* schematic misleads even when the code is right.
5. **Readable at slide scale** — labels ≈ body size in the actual render, ≥4.5:1 contrast, line-work
   not hairline-thin once scaled.

If you can't make it accurate, say so and fall back to extracting the source's own figure, an
equation, or a careful text description — **never ship a confident-looking but wrong schematic.**
