r"""Static and animated Farey-graph logo of the homepage.

A Python port of tikz/main.tex (the TikZ animation the logo was originally made with).
Running it writes
    images/farey-logo.png              the static logo
    images/farey-logo-animated.webp    the animation, starting and ending at the static logo

Usage (from any folder):
    py _logo/farey_logo.py                      # write both files for the website
    py _logo/farey_logo.py --static-only        # only the static logo
    py _logo/farey_logo.py --size 2000 --out C:/somewhere   # e.g. a large copy for slides
Needs Pillow and NumPy:  py -m pip install --user pillow numpy

The construction, as in main.tex
--------------------------------
The unit disc is cut by circles that meet its boundary at right angles (hyperbolic geodesics).
Three boundary points, at the polar angles 90, 180 + A and 360 - B (degrees), split the boundary
into three arcs. On each arc, level 0 is the circle through the arc's two endpoints, and every
further level halves all sub-arcs of the previous level and adds their circles. Levels are filled
alternately black and white, each on top of the previous ones (\drawFarey in main.tex). An arc of
exactly 180 degrees has a straight line as its "circle"; this gives the special first page of
main.tex (the half-white rectangle) without treating it separately.

The animation moves the points 180 + A and 360 - B with the easing \move from main.tex: over one
half of the cycle, A runs from 0 to 90 and B from 90 to 0. The second half repeats the first with
black and white swapped (\flip), which brings the picture back to its start. Halfway through the
white-centred half (A = B = 30) the three points sit at 90, 210 and 330 degrees, the symmetric
picture used as the static logo; the animation starts there, so hovering starts without a jump.

Differences from the TikZ output: no white circle around the disc (it showed as a ring on a dark
background); the disc edge fades smoothly into transparency; TikZ's hairline outlines around each
filled circle (invisible at this size) are left out.
"""

import argparse
import math
import os
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image

# ---------- Settings ----------
SIZE = 320              # width = height in pixels; the page shows the logo at about 70-145 px
SUPERSAMPLE = 4         # sub-pixels per pixel and direction, for smooth edges
DEPTH = 9               # levels of halving, as \depth in main.tex
FPS = 60                # frames per second
CYCLE_MS = 1860         # length of one full cycle in milliseconds (1.86 s, the speed of the old GIF)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_IMAGES = os.path.join(HERE, "..", "images")


def move(x):
    """\\move from main.tex: position (in degrees) of a moving point at time x in [0, 1]."""
    return 120 * x * x - 60 * x + 30 if x > 0.5 else 60 * x


def render(t, flip, size=SIZE, supersample=SUPERSAMPLE, depth=DEPTH):
    """One picture: time t in [0, 1) within a half cycle; flip 0 = black base, 1 = white base."""
    n = size * supersample
    c = (np.arange(n) + 0.5) / n * 2 - 1
    x, y = np.meshgrid(c, -c)                       # y points up, as in TikZ
    inside = x * x + y * y <= 1
    phi = np.degrees(np.arctan2(y, x)) % 360        # polar angle of each sub-pixel
    white = np.full(x.shape, flip == 1)             # base fill of the disc

    # A point at radius r lies inside the circle over a sub-arc of width g exactly when
    # cos(delta) >= q * cos(g/2), where delta is its angle from the middle of that sub-arc and
    # q = (r^2 + 1) / (2r). (For g = 180 this is the half-disc beyond the diameter.)
    r = np.sqrt(x * x + y * y)
    q = (r * r + 1) / (2 * np.maximum(r, 1e-12))
    a, b = move(t), move(1 - t)
    for start, end in [(90, 180 + a), (180 + a, 360 - b), (360 - b, 450)]:
        span = end - start
        ang = (phi - start) % 360                   # angle measured from the arc's start
        idx = np.flatnonzero(inside & (ang < span)) # only these points can lie in this arc's circles
        for level in range(depth + 1):
            gap = span / 2 ** level                 # width of each sub-arc at this level
            half = math.radians(gap / 2)
            # circles of this level reach no closer to the centre than radius (1 - sin) / cos
            idx = idx[r.flat[idx] >= (1 - math.sin(half)) / math.cos(half) - 1e-9] if gap < 180 else idx
            delta = np.radians(ang.flat[idx] % gap) - half
            cap = idx[np.cos(delta) >= q.flat[idx] * math.cos(half)]
            white.flat[cap] = (level + flip) % 2 == 0   # as in \drawFarey: odd -> black, even -> white

    rgb = np.where(white[..., None], np.array(WHITE, float), np.array(BLACK, float))
    alpha = inside.astype(float)
    # average the sub-pixels (colour weighted by coverage), then undo the weighting
    premult = (rgb * alpha[..., None]).reshape(size, supersample, size, supersample, 3).mean(axis=(1, 3))
    alpha = alpha.reshape(size, supersample, size, supersample).mean(axis=(1, 3))
    rgb = np.where(alpha[..., None] > 0, premult / np.maximum(alpha[..., None], 1e-12), 0)
    rgba = np.dstack([rgb, alpha * 255])
    return Image.fromarray(np.clip(rgba + 0.5, 0, 255).astype(np.uint8), "RGBA")


def render_job(job):
    """render() with one tuple argument, for the parallel workers."""
    t, flip, size = job
    return render(t, flip, size=size)


def timing(fps=FPS, cycle_ms=CYCLE_MS):
    """Frames per half cycle (even, so that the static picture t = 1/2 is a frame) and the frame
    durations. A WebP stores whole milliseconds, so they are rounded such that frame i starts at
    i * 1000/fps ms exactly up to rounding: at 60 fps they alternate 17, 17, 16 ms."""
    per_half = max(2, 2 * round(cycle_ms * fps / 1000 / 4))
    starts = [round(i * 1000 / fps) for i in range(2 * per_half + 1)]
    return per_half, [b - a for a, b in zip(starts, starts[1:])]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--size", type=int, default=SIZE, help="width and height in pixels")
    parser.add_argument("--out", default=SITE_IMAGES, help="output folder (default: the site's images/)")
    parser.add_argument("--static-only", action="store_true", help="only write the static logo")
    args = parser.parse_args()
    per_half, durations = timing()
    os.makedirs(args.out, exist_ok=True)

    static = render(0.5, 1, size=args.size)
    static_path = os.path.join(args.out, "farey-logo.png")
    static.save(static_path, optimize=True)
    print(f"wrote {static_path}")
    if args.static_only:
        return

    jobs = [(k / per_half, flip, args.size) for flip in (0, 1) for k in range(per_half)]
    with ProcessPoolExecutor() as pool:             # one worker per processor core
        frames = list(pool.map(render_job, jobs))
    first = per_half + per_half // 2                # flip 1, t = 1/2: the static picture
    frames = frames[first:] + frames[:first]
    anim_path = os.path.join(args.out, "farey-logo-animated.webp")
    # lossless: sharp black-and-white drawings compress better without loss than with;
    # method 4 (of 0-6): method 6 takes minutes longer for about 2% smaller files
    frames[0].save(anim_path, save_all=True, append_images=frames[1:], duration=durations, loop=0,
                   lossless=True, quality=100, method=4)
    print(f"wrote {anim_path} ({len(frames)} frames at {FPS} fps, one cycle {sum(durations)} ms, "
          f"{os.path.getsize(anim_path) // 1024} KB)")


if __name__ == "__main__":
    main()
