"""Refill the zones of a board (in a copy, next to the project's own .kicad_pro) and print what
KiCad's DRC says about it: errors by type, and the unconnected items.

    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/check_board.py board.kicad_pcb [--parity]
"""
from pathlib import Path
import collections, json, shutil, subprocess, sys, tempfile
import pcbnew as pcb
import wx

wx.Log.EnableLogging(False)
HERE = Path(__file__).resolve().parent
PRO = HERE.parent / 'kicad' / 'solderdemon_m68k.kicad_pro'
CLI = 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'


def check(board, parity=False):
    tmp = Path(tempfile.mkdtemp()) / 'solderdemon_m68k.kicad_pcb'
    shutil.copy(board, tmp)
    shutil.copy(PRO, tmp.with_suffix('.kicad_pro'))
    b = pcb.LoadBoard(str(tmp))
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    pcb.SaveBoard(str(tmp), b)
    shutil.copy(PRO, tmp.with_suffix('.kicad_pro'))
    if parity:
        for f in (PRO.parent).glob('*.kicad_sch'):
            shutil.copy(f, tmp.parent / f.name)
        for f in ('sym-lib-table', 'fp-lib-table', 'rosco_m68k.kicad_sym'):
            if (PRO.parent / f).exists():
                shutil.copy(PRO.parent / f, tmp.parent / f)
    rpt = tmp.with_suffix('.json')
    subprocess.run([CLI, 'pcb', 'drc', '--format', 'json', *(['--schematic-parity'] if parity else []),
                    '-o', str(rpt), str(tmp)], capture_output=True)
    return json.loads(rpt.read_text(encoding='utf-8'))


if __name__ == '__main__':
    d = check(sys.argv[1], '--parity' in sys.argv)
    for k in ('violations', 'unconnected_items', 'schematic_parity'):
        c = collections.Counter((v['type'], v['severity']) for v in d.get(k, []))
        print(k, sum(c.values()), dict(c))
    for v in d['violations']:
        if v['severity'] == 'error':
            print('  E', v['type'], [i['description'][:70] for i in v['items']])
    for u in d['unconnected_items']:
        print('  U', [i['description'][:70] for i in u['items']])
