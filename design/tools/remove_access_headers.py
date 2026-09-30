"""Remove the legacy CS2 and address/EXPSEL breakout headers from r2.14.

Run after cpld_board.py and before cpld_route.py. The schematic edit preserves
the hand-drawn sheets' formatting and the PCB edit retains project settings.
"""
from pathlib import Path
import sys

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cpld_board as cb
import sexp


SHEETS = {
    'Expansion.kicad_sch': {
        'symbol': {'J6'},
        'labels': {('EXPSEL', '44.45', '58.42'),
                   ('A20', '44.45', '60.96'),
                   ('A21', '44.45', '63.5'),
                   ('A22', '44.45', '66.04'),
                   ('A23', '44.45', '68.58')},
    },
    'DUART.kicad_sch': {
        'symbol': {'J7'},
        'labels': {('SPICS2', '96.52', '143.51')},
    },
}


def top_level_spans(source):
    """Yield root-child forms without reformatting the original schematic."""
    depth = 0
    start = None
    quoted = escaped = False
    for i, ch in enumerate(source):
        if quoted:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                quoted = False
        elif ch == '"':
            quoted = True
        elif ch == '(':
            if depth == 1:
                start = i
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 1 and start is not None:
                yield start, i + 1
                start = None
    assert depth == 0


def remove_schematic_parts(path, spec):
    source = path.read_text(encoding='utf-8')
    wanted_symbols = set(spec['symbol'])
    wanted_labels = set(spec['labels'])
    spans = []
    for start, end in top_level_spans(source):
        form = sexp.parse(source[start:end])
        if form[0] == 'symbol' and sexp.prop(form, 'Reference') in wanted_symbols:
            wanted_symbols.remove(sexp.prop(form, 'Reference'))
            spans.append((start, end))
        elif form[0] == 'global_label':
            xy = sexp.find(form, 'at')
            key = (sexp.unq(form[1]), xy[1], xy[2])
            if key in wanted_labels:
                wanted_labels.remove(key)
                spans.append((start, end))
    assert not wanted_symbols and not wanted_labels, (path, wanted_symbols, wanted_labels)
    for start, end in reversed(spans):
        line_start = source.rfind('\n', 0, start) + 1
        line_end = source.find('\n', end)
        source = source[:line_start] + source[line_end + 1:]
    path.write_text(source, encoding='utf-8')
    return len(spans)


def remove_board_parts():
    board = pcb.LoadBoard(str(cb.BOARD))
    for ref in ('J6', 'J7'):
        fp = cb.find(board, ref)
        assert fp is not None, ref
        cb.remove(board, fp)
    removed_text = 0
    for drawing in list(board.GetDrawings()):
        if not isinstance(drawing, pcb.PCB_TEXT):
            continue
        label = drawing.GetText()
        pos = drawing.GetPosition()
        x, y = pcb.ToMM(pos.x), pcb.ToMM(pos.y)
        if label == 'CS2 (SPI)' or (label in {'A20', 'A21', 'A22', 'A23'}
                                    and 103 < x < 107 and 110 < y < 121):
            cb.remove(board, drawing)
            removed_text += 1
        elif label == 'Revision 2.14 (DEVELOPMENT)':
            drawing.SetText('Revision 2.42')
        elif label == 'revision 2.14-DEVELOPMENT':
            drawing.SetText('revision 2.42')
    assert removed_text == 5, removed_text
    board.GetTitleBlock().SetRevision('2.42')
    cb.save(board)


def main():
    for filename, spec in SHEETS.items():
        path = cb.KICAD / filename
        print(filename, remove_schematic_parts(path, spec), 'forms removed')
    for path in cb.KICAD.glob('*.kicad_sch'):
        source = path.read_text(encoding='utf-8')
        revised = source.replace('(rev "2.13-DEV")', '(rev "2.42")') \
                        .replace('(rev "2.14-DEV")', '(rev "2.42")') \
                        .replace('(date "2023-12-10")', '(date "2026-09-27")')
        if source != revised:
            path.write_text(revised, encoding='utf-8')
    remove_board_parts()
    print('J6 and J7 removed from the PCB')


if __name__ == '__main__':
    main()
