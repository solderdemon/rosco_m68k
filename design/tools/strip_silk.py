"""Remove upstream badges from the silkscreen and bump the copyright year.

Drops the WEEE bin, the OSHW certification block, the rosco_m68k GitHub URL
next to the expansion connector and both rosco_m68k logos. Plain text edit of the .kicad_pcb, so it does
not touch .kicad_pro. Run after brand_project.py; safe to run again.
"""
from pathlib import Path
import re

BOARD = Path(__file__).resolve().parent.parent / 'kicad' / 'solderdemon_m68k.kicad_pcb'
YEAR = '2026'

DROP = [
    '\t(footprint "Symbol:WEEE-Logo_5.6x8mm_SilkScreen"',
    '\t(footprint "rosco_m68k:OSHW_Mono_0.25_Scale"',
    '\t(gr_text "Certified Open\\nSource Hardware"',
    '\t(gr_text "EXPANSION - SEE http',
    '\t(footprint "rosco_m68k:SM-rosco_m68k_logo"',
    '\t(footprint "rosco_m68k:MD-rosco_m68k_logo"',
]
COPYRIGHT = '\t(gr_text "Copyright ©2019-'


def block_end(src, start):
    """Index just past the S-expression that opens at src[start]."""
    depth = 0
    in_str = False
    i = start
    while True:
        c = src[i]
        if in_str:
            if c == '\\':
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1


def main():
    src = BOARD.read_text(encoding='utf-8')
    removed = 0
    for head in DROP:
        at = src.find(head)
        if at < 0:
            continue
        end = block_end(src, at + 1)
        if src[end] == '\n':
            end += 1
        src = src[:at] + src[end:]
        removed += 1

    # The copyright text uses a TTF face; its render cache still spells the old year, so drop
    # the cache and let KiCad re-render it.
    at = src.find(COPYRIGHT)
    if at >= 0:
        end = block_end(src, at + 1)
        block = re.sub(r'©2019-\d{4}', '©2019-' + YEAR, src[at:end])
        block = re.sub(r'\n\t\t\(render_cache .*\n\t\t\)', '', block, flags=re.S)
        src = src[:at] + block + src[end:]
    src = re.sub(r'(Copyright ©2019-)\d{4}( Ross Bamford)', r'\g<1>' + YEAR + r'\2', src)

    BOARD.write_text(src, encoding='utf-8', newline='\r\n')   # KiCad on Windows writes CRLF
    print(f'removed {removed} silkscreen items; copyright 2019-{YEAR}')


if __name__ == '__main__':
    main()
