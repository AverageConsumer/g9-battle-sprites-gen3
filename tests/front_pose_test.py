"""Checks tools/front_pose.py on synthetic sheets. Run from the mod root:
    python tests/front_pose_test.py
"""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import front_pose as fp  # noqa: E402

passed = failed = 0


def check(cond, msg):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL: " + msg)


FS = 64


def frame(top, bottom, x0=24, x1=40, extra=None):
    """A frame with a body from row `top` to `bottom` (exclusive); `extra` = another box (wings)."""
    im = Image.new("RGBA", (FS, FS), (0, 0, 0, 0))
    im.paste((255, 0, 0, 255), (x0, top, x1, bottom))
    if extra:
        im.paste((0, 255, 0, 255), extra)
    return im


# a still sprite: the rest bottom is its bottom
still = [frame(20, 60) for _ in range(8)]
check(fp.rest_bottom(still) == 60, "a still sprite rests on its own bottom")

# a hopper: mostly on the ground, three frames in the air, the FIRST one mid-hop
hop = [frame(8, 48)] + [frame(20, 60) for _ in range(9)] + [frame(10, 50), frame(14, 54)]
check(fp.rest_bottom(hop) == 60, f"a hopper rests on the ground, not the hop (got {fp.rest_bottom(hop)})")
check(0 not in fp.rest_cluster(hop), "its mid-hop first frame is not part of the rest pose")

# a bobber: rows 58..62 in turn, mostly 60; the median of the rest cluster
bob = [frame(20, b) for b in (60, 60, 61, 59, 60, 62, 58, 60, 61, 59)]
check(fp.rest_bottom(bob) == 60, f"a bobber rests on its median (got {fp.rest_bottom(bob)})")

# frame_bottoms and empty frames
empty = Image.new("RGBA", (FS, FS), (0, 0, 0, 0))
check(fp.frame_bottoms([frame(5, 30), empty]) == [30, None], "frame bottoms, None for an empty frame")
check(fp.rest_bottom([empty, empty]) is None, "an empty sheet has no rest pose")
check(fp.rest_cluster([frame(20, 60), empty, frame(20, 60)]) == [0, 2], "empty frames never count")

# centre tops: a wing raised at the side does not count, the body's top does
wing = [frame(30, 60, extra=(2, 0, 10, 40)) for _ in range(4)]
tops = fp.centre_tops(wing)
check(all(t == 30 for t in tops), f"a raised wing at the side is not the body's top (got {tops})")
head = [frame(30, 60, extra=(28, 4, 36, 30))]
check(fp.centre_tops(head) == [4], "a head in the middle is")

# a sheet on disk, with a window: only the kept frames
tmp = Path(__file__).resolve().parent / "_front_pose_sheet.png"
sheet = Image.new("RGBA", (FS * 4, FS), (0, 0, 0, 0))
for i, b in enumerate((40, 60, 60, 60)):
    sheet.paste(frame(10, b), (i * FS, 0))
sheet.save(tmp)
try:
    gap, fs, frames = fp.rest_gap(tmp, (1, 4))
    check(fs == FS and len(frames) == 3 and gap == 4, f"rest_gap over the kept window (gap {gap})")
finally:
    tmp.unlink()

print(f"{passed}/{passed + failed} checks passed (front pose)")
sys.exit(0 if failed == 0 else 1)
