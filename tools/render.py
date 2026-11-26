"""Render leandro.1 into README.md and the terminal SVGs. Usage: python3 tools/render.py"""
import hashlib
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


def svg(width, name, fluid=False, font=FONT):
    """fluid: no viewBox, so text keeps its pixel size and the window stretches to the image width."""
    lines = man(width)
    char = CHAR * font / FONT
    line_h = round(LINE * font / FONT)
    w = round(PAD * 2 + width * char)
    status = f" Manual page leandro(1) lines 1-{len(lines)}/{len(lines)} (END) "
    body_top = BAR + PAD
    h = body_top + (len(lines) + 2) * line_h + PAD - 6
    size = f'width="100%" height="{h}"' if fluid else f'viewBox="0 0 {w} {h}" width="{w}" height="{h}"'
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" {size} role="img" aria-label="Terminal window showing the manual page leandro(1)">',
        f"<style>text{{font:{font}px {MONO};fill:#c9d1d9;white-space:pre}}.b{{font-weight:700;fill:#fff}}.u{{text-decoration:underline;fill:#e3b341}}.title{{font:12px {SANS};fill:#8b949e}}.inv{{fill:#0d1117}}.in{{width:calc(100% - 2px)}}.cur{{animation:k 1.1s steps(1) infinite}}@keyframes k{{50%{{opacity:0}}}}@media (prefers-reduced-motion:reduce){{.cur{{animation:none}}}}</style>",
        f'<rect width="100%" height="{h}" rx="9" fill="#30363d"/>',
        f'<rect class="in" x="1" y="1" width="99.7%" height="{h - 2}" rx="8" fill="#0d1117"/>',
        f'<rect class="in" x="1" y="1" width="99.7%" height="{BAR}" rx="8" fill="#161b22"/>',
        f'<rect class="in" x="1" y="{BAR - 9}" width="99.7%" height="10" fill="#161b22"/>',
        f'<rect class="in" x="1" y="{BAR}" width="99.7%" height="1" fill="#30363d"/>',
        '<circle cx="18" cy="17" r="5.5" fill="#ff5f57"/><circle cx="36" cy="17" r="5.5" fill="#febc2e"/><circle cx="54" cy="17" r="5.5" fill="#28c840"/>',
        '<text x="50%" y="21" text-anchor="middle" class="title">man leandro</text>',
    ]
    for n, line in enumerate(lines):
        if not line.strip():
            continue
        y = body_top + n * line_h + round(font * 0.86)
        cols = [c for c in plain(line).split("  ") if c.strip()]
        if fluid and n in (0, len(lines) - 1) and len(cols) == 3:
            left, mid, right = (html.escape(c.strip()) for c in cols)
            o.append(f'<text x="{PAD}" y="{y}">{left}</text><text x="50%" y="{y}" text-anchor="middle">{mid}</text><text x="100%" dx="-{PAD}" y="{y}" text-anchor="end">{right}</text>')
            continue
        col = 0
        for text, style in spans(line):
            body = text.lstrip(" ")
            start = col + len(text) - len(body)
            col += len(text)
            body = body.rstrip(" ")
            if not body:
                continue
            cls = f' class="{style}"' if style else ""
            o.append(f'<text x="{PAD + start * char:.1f}" y="{y}"{cls} xml:space="preserve" textLength="{len(body) * char:.1f}">{html.escape(body)}</text>')
    sy = body_top + (len(lines) + 1) * line_h
    sw = len(status) * char
    o.append(f'<rect x="{PAD}" y="{sy - 2}" width="{sw:.1f}" height="{line_h - 2}" fill="#c9d1d9"/>')
    o.append(f'<text x="{PAD}" y="{sy + round(font * 0.86)}" class="inv" xml:space="preserve" textLength="{sw:.1f}">{html.escape(status)}</text>')
    o.append(f'<rect class="cur" x="{PAD + sw + 3:.1f}" y="{sy - 2}" width="{char:.1f}" height="{line_h - 2}" fill="#c9d1d9"/>')
    o.append("</svg>\n")
    (ROOT / "assets" / name).write_text("\n".join(o))
    return lines


for old in (ROOT / "assets").glob("man-*.svg"):
    old.unlink()
names = {}
for key, width, kwargs in (("wide", 76, dict(fluid=True, font=12)), ("medium", 50, dict(fluid=True, font=12)), ("narrow", 46, {})):
    svg(width, f"man-{key}.svg", **kwargs)
    tmp = ROOT / "assets" / f"man-{key}.svg"
    names[key] = f"man-{key}-{hashlib.sha256(tmp.read_bytes()).hexdigest()[:8]}.svg"
    tmp.rename(ROOT / "assets" / names[key])
text = "\n".join(plain(l) for l in man(60))
readme = f"""<picture>
  <source media="(max-width: 480px)" srcset="assets/{names['narrow']}">
  <source media="(max-width: 720px)" srcset="assets/{names['medium']}">
  <img src="assets/{names['wide']}" width="100%" alt="Terminal window showing the man page leandro(1): backend engineer, measures things">
</picture>

This is a real man page: [leandro.1](leandro.1). More at [albero.dev](https://albero.dev).

<details>
<summary>Plain text</summary>

```
{text}
```

</details>
"""
(ROOT / "README.md").write_text(readme)
