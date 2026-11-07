#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_material — turn a gallery deck into the MATERIAL it was built from, with none of its design.

Used by the design-strength comparison (docs/superpowers/specs/2026-11-07-design-strength-baseline-design.md):
the current skill and an older one each build a deck from this folder, and the result is compared with
the gallery deck. So the folder carries the content — every text in reading order, tables, chart data,
speaker notes, the original images — and nothing that says how it looked: no colours, faces, sizes or
positions. The brief comes from the gallery manifest's title and use line, never from profile.md,
whose prose describes the design.

    python3 scripts/design_bench/extract_material.py <template.pptx> --title T --use U --out DIR
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


MIN_SIDE = 600          # px: icons (160–200), glows and swatches the gallery decks rasterised are smaller
MIN_OPAQUE = 0.9        # share of opaque pixels: a cut-out glow or reflection is mostly transparent


def _is_content_image(blob):
    """A photo or illustration someone would hand over as material — not a raster of the deck's own
    design (an icon in its palette, a glow, a reflection, a motif), which would leak the look."""
    import io
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(blob))
        im.load()
    except Exception:                                               # noqa: BLE001
        return False
    if min(im.size) < MIN_SIDE:
        return False
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        a = im.convert("RGBA").getchannel("A").resize((64, 64))
        if sum(1 for v in a.tobytes() if v > 250) / 4096 < MIN_OPAQUE:
            return False
    return True


def _walk(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _walk(sh.shapes)
        else:
            yield sh


def _pos(sh):
    return ((sh.top or 0), (sh.left or 0))


def _md_table(rows):
    rows = [[(c or "").replace("\n", " ").replace("|", "／").strip() for c in r] for r in rows]
    if not rows:
        return ""
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def _chart_rows(chart):
    plot = chart.plots[0]
    cats = [str(c) for c in plot.categories]
    series = list(plot.series)
    rows = [[""] + [s.name or "" for s in series]]
    for i, c in enumerate(cats):
        rows.append([c] + ["" if i >= len(s.values) or s.values[i] is None else "%g" % s.values[i]
                           for s in series])
    return rows


def extract(pptx_path: str, *, title: str, use: str, out_dir: str) -> dict:
    prs = Presentation(pptx_path)
    img_dir = os.path.join(out_dir, "images")
    os.makedirs(img_dir, exist_ok=True)
    seen, n_tables, n_charts = {}, 0, 0
    pages = []
    for k, slide in enumerate(prs.slides, 1):
        lines, imgs = [], []
        for sh in sorted(_walk(slide.shapes), key=_pos):
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    blob, ext = sh.image.blob, sh.image.ext
                except Exception:                                   # noqa: BLE001 — linked/odd pictures
                    continue
                if not _is_content_image(blob):
                    continue
                h = hashlib.sha1(blob).hexdigest()
                if h not in seen:
                    seen[h] = "img%02d.%s" % (len(seen) + 1, ext)
                    with open(os.path.join(img_dir, seen[h]), "wb") as f:
                        f.write(blob)
                if seen[h] not in imgs:
                    imgs.append(seen[h])
            elif getattr(sh, "has_table", False) and sh.has_table:
                n_tables += 1
                lines.append(_md_table([[c.text for c in r.cells] for r in sh.table.rows]))
            elif getattr(sh, "has_chart", False) and sh.has_chart:
                n_charts += 1
                try:
                    lines.append("图表数据：\n" + _md_table(_chart_rows(sh.chart)))
                except Exception:                                   # noqa: BLE001
                    lines.append("（图表，数据无法读取）")
            elif getattr(sh, "has_text_frame", False) and sh.has_text_frame:
                t = "\n".join(p.text.strip() for p in sh.text_frame.paragraphs if p.text.strip())
                if t:
                    lines.append(t)
        notes = ""
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        block = ["## 原稿第 %d 页" % k, ""] + [l + "\n" for l in lines]
        if imgs:
            block.append("本页配图：" + "、".join(imgs) + "\n")
        if notes:
            block.append("讲稿备注：" + notes + "\n")
        pages.append("\n".join(block))
    head = ("# 素材：%s\n\n这是内容池，不是页面方案：页码只表示原稿里的先后，"
            "页数、每页放什么、怎么组织都由你规划。图片在 images/ 下，可用可不用。\n\n" % title)
    with open(os.path.join(out_dir, "素材.md"), "w", encoding="utf-8") as f:
        f.write(head + "\n".join(pages))
    brief = ("# 测试材料说明\n\n这是用于测试的材料，按自动模式完成，不要提问。\n\n"
             "- 主题：%s\n- 用途与场合：%s\n- 语言：中文\n- 篇幅：原稿 %d 页，可按内容增减\n"
             "- 素材：同目录的 素材.md 与 images/\n" % (title, use, len(pages)))
    with open(os.path.join(out_dir, "测试材料说明.md"), "w", encoding="utf-8") as f:
        f.write(brief)
    return {"pages": len(pages), "images": len(seen), "tables": n_tables, "charts": n_charts}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pptx")
    ap.add_argument("--title", required=True)
    ap.add_argument("--use", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    print(extract(a.pptx, title=a.title, use=a.use, out_dir=a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
