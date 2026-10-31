# The Farey-graph logo

The logo exists in two colourings, black and white for light mode and black with the page's
text grey (`#d7d7d7`) for dark mode. Both, static and animated, are computed by one script:

    py _logo/farey_logo.py

It takes about 20 seconds (the frames are computed in parallel) and overwrites these files in
`images/`: `farey-logo.png` and `farey-logo-animated.webp` (light mode), `farey-logo-dark.png`
and `farey-logo-animated-dark.webp` (dark mode). It needs Python with Pillow and NumPy
(`py -m pip install --user pillow numpy`).
Options: `--static-only`, `--size N` (pixels), `--out FOLDER` (e.g. for a large copy for slides).

Settings such as size, colours (`VARIANTS`), frame rate (60 fps) and the length of one cycle
(1.86 s) are at the top of `farey_logo.py`, and its opening comment explains the construction.

## Where it comes from

`tikz/` holds the original TikZ files the logo was first made with:

- `tikz/main.tex`: the animation, one picture per PDF page. `farey_logo.py` is a direct port of
  it. Its midpoint (page 16) is the static logo. The 2024 GIF was made from a slightly different
  version of this file: with `\maxFrames{30}` and `\foreach \flip in {0,1}`, so 62 frames,
  converted with the command in `tikz/PDFtoGIF.txt` and then sped up to 30 ms per frame.
- `tikz/FareyGraph_TikzCode.tex`: an older drawing of the static logo, upside down and with
  black and white swapped, and with slightly bolder lines towards the edge.

Changes made in the port: no white circle around the disc (it showed as a ring on the dark
page), a smooth transparent edge, and the animation starts at the static logo.
The previous hand-made files are kept in `_originals/` (`farey-logo.png`, `farey-logo-animated.gif`).
