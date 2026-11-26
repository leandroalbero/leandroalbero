"""Render leandro.1 into README.md and the terminal SVGs. Usage: python3 tools/render.py"""
import html
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MONO = 'ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace'
SANS = '-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif'
FONT, CHAR, LINE, PAD, BAR = 14, 8.45, 20, 22, 34


def man(width):
    return subprocess.run(
        ["mandoc", "-T", "ascii", "-O", f"width={width}", str(ROOT / "leandro.1")],
        check=True, capture_output=True, text=True,
    ).stdout.rstrip("\n").split("\n")


def spans(line):
    cells, i = [], 0
    while i < len(line):
        if i + 2 < len(line) and line[i + 1] == "\b":
            cells.append((line[i + 2], "u" if line[i] == "_" else "b"))
            i += 3
        else:
            cells.append((line[i], ""))
            i += 1
    out, cur, style = [], "", None
    for ch, st in cells:
        if st != style and cur:
            out.append((cur, style))
            cur = ""
        cur, style = cur + ch, st
    if cur:
        out.append((cur, style))
    return out


def plain(line):
    return "".join(text for text, _ in spans(line))


def svg(width, name):
    lines = man(width)
    w = round(PAD * 2 + width * CHAR)
    status = f" Manual page leandro(1) lines 1-{len(lines)}/{len(lines)} (END) "
    body_top = BAR + PAD
    h = body_top + (len(lines) + 2) * LINE + PAD - 6
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Terminal window showing the manual page leandro(1)">',
        f"<style>text{{font:{FONT}px {MONO};fill:#c9d1d9;white-space:pre}}.b{{font-weight:700;fill:#fff}}.u{{text-decoration:underline;fill:#e3b341}}.title{{font:12px {SANS};fill:#8b949e}}.inv{{fill:#0d1117}}.cur{{animation:k 1.1s steps(1) infinite}}@keyframes k{{50%{{opacity:0}}}}@media (prefers-reduced-motion:reduce){{.cur{{animation:none}}}}</style>",
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="9" fill="#0d1117" stroke="#30363d"/>',
        f'<path d="M.5 {BAR}V9.5a9 9 0 0 1 9-9H{w - 9.5}a9 9 0 0 1 9 9V{BAR}z" fill="#161b22" stroke="#30363d"/>',
        '<circle cx="18" cy="17" r="5.5" fill="#ff5f57"/><circle cx="36" cy="17" r="5.5" fill="#febc2e"/><circle cx="54" cy="17" r="5.5" fill="#28c840"/>',
        f'<text x="{w / 2}" y="21" text-anchor="middle" class="title">man leandro</text>',
    ]
    for n, line in enumerate(lines):
        if not line.strip():
            continue
        parts = "".join(
            f'<tspan class="{st}">{html.escape(t)}</tspan>' if st else html.escape(t)
            for t, st in spans(line)
        )
        o.append(f'<text x="{PAD}" y="{body_top + n * LINE + 12}" xml:space="preserve">{parts}</text>')
    sy = body_top + (len(lines) + 1) * LINE
    sw = len(status) * CHAR
    o.append(f'<rect x="{PAD}" y="{sy - 2}" width="{sw:.1f}" height="{LINE - 2}" fill="#c9d1d9"/>')
    o.append(f'<text x="{PAD}" y="{sy + 12}" class="inv" xml:space="preserve" textLength="{sw:.1f}">{html.escape(status)}</text>')
    o.append(f'<rect class="cur" x="{PAD + sw + 3:.1f}" y="{sy - 2}" width="{CHAR}" height="{LINE - 2}" fill="#c9d1d9"/>')
    o.append("</svg>\n")
    (ROOT / "assets" / name).write_text("\n".join(o))
    return lines


wide = svg(66, "man-wide.svg")
svg(46, "man-narrow.svg")
alt = " ".join(" ".join(plain(l).split()) for l in wide if l.strip())
readme = f"""<picture>
  <source media="(max-width: 600px)" srcset="assets/man-narrow.svg">
  <img src="assets/man-wide.svg" width="{round(PAD * 2 + 66 * CHAR)}" alt="{html.escape(alt, quote=True)}">
</picture>

This is a real man page: [leandro.1](leandro.1). More at [albero.dev](https://albero.dev).
"""
(ROOT / "README.md").write_text(readme)
