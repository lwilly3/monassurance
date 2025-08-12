#!/usr/bin/env python
"""Generate a simple SVG coverage badge from coverage.xml.
Usage: python gen_coverage_badge.py coverage.xml coverage_badge.svg
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET

TEMPLATE = """<svg xmlns='http://www.w3.org/2000/svg' width='110' height='20' role='img' aria-label='coverage: {pct}%'>
<linearGradient id='a' x2='0' y2='100%'><stop offset='0' stop-color='#bbb' stop-opacity='.1'/><stop offset='1' stop-opacity='.1'/></linearGradient>
<rect rx='3' width='110' height='20' fill='#555'/>
<rect rx='3' x='62' width='48' height='20' fill='{color}'/>
<path fill='{color}' d='M62 0h4v20h-4z'/>
<rect rx='3' width='110' height='20' fill='url(#a)'/>
<g fill='#fff' text-anchor='middle' font-family='Verdana,Geneva,DejaVu Sans,sans-serif' font-size='11'>
<text x='31' y='15' fill='#010101' fill-opacity='.3'>coverage</text><text x='31' y='14'>coverage</text>
<text x='85' y='15' fill='#010101' fill-opacity='.3'>{pct}%</text><text x='85' y='14'>{pct}%</text>
</g>
</svg>"""

def pick_color(pct: float) -> str:
    if pct >= 90:
        return '#4c1'
    if pct >= 75:
        return '#97CA00'
    if pct >= 60:
        return '#dfb317'
    return '#e05d44'

def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: gen_coverage_badge.py coverage.xml badge.svg", file=sys.stderr)
        return 1
    cov_path, out_path = sys.argv[1], sys.argv[2]
    try:
        tree = ET.parse(cov_path)
        root = tree.getroot()
        line_rate = float(root.get('line-rate', '0')) * 100.0
    except Exception as e:  # pragma: no cover
        print(f"Erreur lecture {cov_path}: {e}", file=sys.stderr)
        return 2
    color = pick_color(line_rate)
    svg = TEMPLATE.format(pct=f"{line_rate:.1f}", color=color)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f"Badge écrit: {out_path} ({line_rate:.1f}%)")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
