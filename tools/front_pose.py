#!/usr/bin/env python3
"""
The resting pose of an animated sprite sheet: the frames most alike, the pose the animation keeps
coming back to. Shared by tools/front_anchor.py and tools/front_feet.py so both put a front
sprite's feet in the same place.

  1. each kept frame's alpha mask, over the union box of all frames, reduced to GRID x GRID
  2. distance between two frames = cells that differ / cells set in either (XOR / union)
  3. the medoid: the frame with the smallest total distance to all the others
  4. the rest cluster: the medoid and the frames nearest it, the most-alike half (at least
     MIN_CLUSTER frames, or every frame when there are fewer)
  5. the rest bottom: the MEDIAN bottom row over the rest cluster, so a few hop or dip frames in
     it do not move it

Pure PIL. Frames are RGBA images of one sheet (fs x fs each).
"""

from __future__ import annotations

import math
import statistics
from pathlib import Path

from PIL import Image

GRID = 32
MIN_CLUSTER = 3


def load_frames(sheet: Path, window=None) -> tuple[list[Image.Image], int]:
    """The kept frames of a sheet (all of them when `window` is None) and the frame size."""
    with Image.open(sheet) as im:
        fs = im.height
        n = im.width // fs
        a, b = (window[0], min(window[1], n)) if window else (0, n)
        rgba = im.convert("RGBA")
        return [rgba.crop((f * fs, 0, (f + 1) * fs, fs)) for f in range(a, b)], fs


def union_box(frames: list[Image.Image]) -> tuple[int, int, int, int] | None:
    boxes = [b for b in (f.getbbox() for f in frames) if b]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def frame_bottoms(frames: list[Image.Image]) -> list[int | None]:
    """Each frame's bottom: the row below its lowest opaque pixel (None for an empty frame)."""
    return [b[3] if b else None for b in (f.getbbox() for f in frames)]


def _mask(frame: Image.Image, box) -> int:
    """The frame's alpha over `box`, reduced to GRID x GRID cells, as a bitmask."""
    a = frame.getchannel("A").crop(box).resize((GRID, GRID), Image.BOX)
    m = 0
    for i, v in enumerate(a.getdata()):
        if v:
            m |= 1 << i
    return m


def rest_cluster(frames: list[Image.Image]) -> list[int]:
    """Indexes of the resting-pose frames (see the module doc); empty frames never count."""
    box = union_box(frames)
    live = [i for i, f in enumerate(frames) if f.getbbox()]
    if box is None or not live:
        return []
    if len(live) <= MIN_CLUSTER:
        return live
    masks = {i: _mask(frames[i], box) for i in live}

    def dist(i: int, j: int) -> float:
        u = (masks[i] | masks[j]).bit_count()
        return (masks[i] ^ masks[j]).bit_count() / u if u else 0.0

    total = {i: sum(dist(i, j) for j in live) for i in live}
    medoid = min(live, key=lambda i: (total[i], i))
    near = sorted(live, key=lambda j: (dist(medoid, j), j))
    k = max(MIN_CLUSTER, math.ceil(len(live) / 2))
    return sorted(near[:k])


def rest_bottom(frames: list[Image.Image]) -> int | None:
    """The median bottom row of the resting pose (see frame_bottoms)."""
    bottoms = frame_bottoms(frames)
    rest = [bottoms[i] for i in rest_cluster(frames) if bottoms[i] is not None]
    return int(statistics.median_low(rest)) if rest else None


def rest_gap(sheet: Path, window=None) -> tuple[int, int, list[Image.Image]] | None:
    """(empty rows under the resting pose, frame size, the kept frames), or None for an empty sheet."""
    frames, fs = load_frames(sheet, window)
    b = rest_bottom(frames)
    return None if b is None else (fs - b, fs, frames)


def centre_tops(frames: list[Image.Image]) -> list[int | None]:
    """Each frame's top row within the middle third of the union box's columns: the body, most
    likely, not wings, arms or a tail swung out to the side. None when that band is empty."""
    box = union_box(frames)
    if box is None:
        return [None] * len(frames)
    w = box[2] - box[0]
    x0 = box[0] + w // 3
    x1 = max(x0 + 1, box[0] + (2 * w + 2) // 3)
    out = []
    for f in frames:
        b = f.getchannel("A").crop((x0, 0, x1, f.height)).getbbox()
        out.append(b[1] if b else None)
    return out
