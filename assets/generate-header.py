"""Generate the asteroid header. Requires Pillow and DejaVu Sans."""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 900, 105
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(FONT, 50)
label = "SANTIAGO CABANA"
letter_spacing = 3
letter_masks = []
cursor = (WIDTH - sum(font.getlength(char) for char in label)
          - letter_spacing * (len(label) - 1)) / 2
for char in label:
    advance = font.getlength(char)
    mask = Image.new("L", (WIDTH, HEIGHT))
    if char != " ":
        ImageDraw.Draw(mask).text(
            (cursor + advance / 2, 52), char, font=font, fill=255,
            anchor="mm", stroke_width=2, stroke_fill=255,
        )
    letter_masks.append(mask)
    cursor += advance + letter_spacing

rng = random.Random(947)
particles = []
positions = []
letter_ids = []
occupied = []
for row_y in range(18, 90, 3):
    for col_x in range(120, 780, 3):
        x = col_x + rng.uniform(-.6, .6)
        y = row_y + rng.uniform(-.6, .6)
        letter_id = next((i for i, mask in enumerate(letter_masks)
                          if mask.getpixel((int(x), int(y))) >= 160), None)
        if letter_id is None:
            continue
        size = rng.uniform(1.8, 4.0)
        if any(math.hypot(x - px, y - py) < (size + radius) * .8 for px, py, radius in occupied):
            continue
        dx = rng.randint(-90, 90)
        dy = rng.randint(-38, 38)
        # Let some rocks cross the letter silhouette instead of clipping their edges.
        positions.append((x, y))
        letter_ids.append(letter_id)
        occupied.append((x, y, size))
        stretch_x = rng.uniform(0.68, 1.0)
        stretch_y = rng.uniform(0.68, 1.0)
        points = []
        vertices = rng.choice((5, 6, 7, 8))
        for vertex in range(vertices):
            angle = vertex * math.tau / vertices + rng.uniform(-0.28, 0.28)
            radius = size * rng.uniform(0.42, 1.0)
            points.append(f"{math.cos(angle) * radius * stretch_x:.1f},{math.sin(angle) * radius * stretch_y:.1f}")
        delay = rng.uniform(-0.35, 0.35)
        particles.append(
            f'<g transform="translate({x:.1f} {y:.1f})"><polygon points="{" ".join(points)}" '
            f'style="--dx:{dx}px;--dy:{dy}px;--delay:{delay:.2f}s"/></g>'
        )

floating = []
for _ in range(24):
    x = rng.choice((rng.uniform(70, 185), rng.uniform(715, 830)))
    y = rng.uniform(12, 92)
    size = rng.uniform(1.2, 2.8)
    floating.append(
        f'<g transform="translate({x:.1f} {y:.1f})"><path '
        f'd="M{-size:.1f},0 L{-size * .4:.1f},{-size:.1f} L{size * .7:.1f},{-size * .6:.1f} '
        f'L{size:.1f},{size * .4:.1f} L0,{size:.1f} Z" '
        f'style="--delay:{rng.uniform(-7, 0):.1f}s"/></g>'
    )

def within_letter(mask, x1, y1, x2, y2):
    """Keep each connection inside the sampled letter, including gaps and counters."""
    return all(
        mask.getpixel((int(x1 + (x2 - x1) * step / 20),
                       int(y1 + (y2 - y1) * step / 20))) >= 160
        for step in range(21)
    )

def constellation_edges(points):
    """Connect nearby rocks inside letters without duplicate edges or cycles."""
    parent = list(range(len(points)))

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    candidates = []
    for i, (x, y) in enumerate(points):
        for j in range(i + 1, len(points)):
            nx, ny = points[j]
            distance = math.hypot(x - nx, y - ny)
            if (letter_ids[i] == letter_ids[j] and distance < 10
                    and within_letter(letter_masks[letter_ids[i]], x, y, nx, ny)):
                candidates.append((distance, i, j))

    for _, i, j in sorted(candidates):
        a, b = root(i), root(j)
        if a != b:
            parent[a] = b
            yield points[i], points[j]

svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="105" viewBox="0 0 900 105" role="img" aria-labelledby="title desc">
  <title id="title">Santiago Cabana</title>
  <desc id="desc">Pequeños asteroides flotan y se unen para formar el nombre sobre una cuadrícula transparente.</desc>
  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#64748b" stroke-opacity=".48"/></pattern>
    <linearGradient id="fade"><stop stop-color="black"/><stop offset=".18" stop-color="white"/><stop offset=".82" stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient>
    <mask id="edges"><rect width="900" height="105" fill="url(#fade)"/></mask>
  </defs>
  <style>
    .grid { animation: drift 12s linear infinite; }
    .particles polygon { fill: #3347a8; animation: assemble 9s ease-in-out infinite; animation-delay: var(--delay); }
    .particles g:nth-child(3n) polygon { fill: #6366f1; }
    .particles g:nth-child(5n) polygon { fill: #2563eb; }
    .constellation { fill: none; stroke: #4f46e5; stroke-width: 1.2; stroke-linecap: round; opacity: 0; animation: connections 9s ease-in-out infinite; }
    .floating path { fill: #6366f1; opacity: .7; animation: float 7s ease-in-out infinite alternate; animation-delay: var(--delay); }
    @keyframes drift { to { transform: translate(24px,24px); } }
    @keyframes assemble {
      0%,100% { transform: translate(var(--dx),var(--dy)) rotate(70deg); opacity: .75; }
      28%,72% { transform: translate(0,0) rotate(0); opacity: 1; }
    }
    @keyframes connections { 0%, 22%, 78%, 100% { opacity: 0; } 32%, 68% { opacity: .65; } }
    @keyframes float { from { transform: translate(-4px, 3px) rotate(-15deg); } to { transform: translate(5px, -5px) rotate(25deg); } }
    @media (prefers-color-scheme: dark) {
      .particles polygon { fill: #a5b4fc; }
      .particles g:nth-child(3n) polygon { fill: #818cf8; }
      .particles g:nth-child(5n) polygon { fill: #60a5fa; }
      .constellation { stroke: #a5b4fc; }
    }
    @media (prefers-reduced-motion: reduce) { .grid, .particles polygon, .constellation, .floating path { animation: none; } .constellation { opacity: .65; } }
  </style>
  <g mask="url(#edges)"><rect class="grid" x="-24" y="-24" width="948" height="153" fill="url(#grid)"/></g>
  <g class="floating">
''' + "\n".join("    " + p for p in floating) + '''
  </g>
  <g class="constellation">
''' + "\n".join(
    f'    <path d="M{x:.1f} {y:.1f}L{nx:.1f} {ny:.1f}"/>'
    for (x, y), (nx, ny) in constellation_edges(positions)
) + '''
  </g>
  <g class="particles">
''' + "\n".join("    " + p for p in particles) + '''
  </g>
</svg>
'''
Path(__file__).with_name("header.svg").write_text(svg, encoding="utf-8")
print(f"Generated header with {len(particles)} particles")
