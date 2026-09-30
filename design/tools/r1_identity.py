"""r1 finishing touches: the CPU decoupling into the gap r1_layout.py opened, SolderDemon identity.

  1. C20, C12, C29 and C31 stood squeezed against the CPU; stretching the board left 14 mm between
     its pins and the CPLDs. They go into one evenly spaced column in that gap, at the x where
     they tore up the least copper (CAP_X). They reach the supply only through the inner planes, so
     nothing but the tracks in their way has to be routed again (cpld_route.py does that).
  2. the SolderDemon identity, as on the busboard: the pixel-art logo (make_logo.py), the name
     in large type and what the board is under it. The front has no 17 mm to spare, so it goes on
     the back, between the CPU's rows of pins; it replaces the plain "SolderDemon m68k" text.

Runs on the routed r1 board and is safe to run again.

    python design/tools/make_logo.py 17
    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/r1_identity.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/cpld_route.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/trim_stubs.py
"""
from pathlib import Path
import re, sys

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cpld_board as cb

mm, T = pcb.FromMM, pcb.ToMM

CAPS = ['C20', 'C12', 'C29', 'C31']
CAP_YS = [59.0, 65.0, 71.0, 77.0]
# The gap runs from the CPU pads (166.6) to the CPLD pads (180.6). 175.8 is where the column tore up
# the least copper when it was chosen (--choose tries 172.0..176.0 again, on the r1 board before this).
CAP_X = 175.8
CAP_XS = [172.0 + 0.2 * i for i in range(21)]
LOGO = ('rosco_m68k', 'SolderDemon_Logo', (150.0, 73.1))
NAME = ('SolderDemon', (121.0, 71.8), 2.0, 0.4)
BOARD_NAME = ('M68K Computer r1', (121.0, 74.8), 1.0, 0.15)
OLD_BACK_TEXT = {'SolderDemon m68k', 'revision r1', 'solderdemon_m68k r1'}


def in_the_way(b, fps):
    """Tracks and vias the pads of `fps` would short or crowd (cb.rip_collisions, without ripping)."""
    pads = [p for fp in fps for p in fp.Pads()]
    hit = []
    for t in b.GetTracks():
        layers = [t.GetLayer()] if t.Type() == pcb.PCB_TRACE_T else list(t.GetLayerSet().CuStack())
        for p in pads:
            if t.Type() == pcb.PCB_TRACE_T and p.GetNetname() == t.GetNetname():
                continue
            if any(t.GetEffectiveShape(l).Collide(p.GetEffectiveShape(l), cb.CLEARANCE) for l in layers if p.IsOnLayer(l)):
                hit.append(t)
                break
    return hit


def place_caps(b, x):
    fps = []
    for ref, y in zip(CAPS, CAP_YS):
        fp = cb.find(b, ref)
        fp.SetOrientationDegrees(-90)
        fp.SetPosition(cb.at_mm(x, y))
        r = fp.Reference()
        r.SetPosition(cb.at_mm(x - 2.4, y))      # left: on the right it touches IC3's outline
        r.SetTextAngleDegrees(90)
        r.SetTextSize(pcb.VECTOR2I(mm(0.9), mm(0.9)))
        r.SetTextThickness(mm(0.15))
        fps.append(fp)
    return fps


def caps(b):
    before = {r: cb.find(b, r).GetPosition() for r in CAPS}
    best = min(CAP_XS, key=lambda x: len(in_the_way(b, place_caps(b, x)))) if '--choose' in sys.argv else CAP_X
    fps = place_caps(b, best)
    if all(fp.GetPosition() == before[fp.GetReference()] for fp in fps):
        return print(f'decoupling column already at x = {best:.1f}')   # routed around: leave it
    nets, n = cb.rip_collisions(b, fps)
    print(f'decoupling column at x = {best:.1f}: {n} tracks/vias torn up on {len(nets)} nets')


def back_text(b, text, xy, size, thick):
    t = pcb.PCB_TEXT(b)
    t.SetText(text)
    t.SetLayer(pcb.B_SilkS)
    t.SetMirrored(True)
    t.SetPosition(cb.at_mm(*xy))
    t.SetTextSize(pcb.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(thick))
    t.SetHorizJustify(pcb.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcb.GR_TEXT_V_ALIGN_CENTER)
    b.Add(t)


def identity(b):
    for d in list(b.GetDrawings()):
        if isinstance(d, pcb.PCB_TEXT) and d.GetLayer() == pcb.B_SilkS and \
                d.GetText() in OLD_BACK_TEXT | {NAME[0], BOARD_NAME[0]}:
            cb.remove(b, d)
    lib, name, (x, y) = LOGO
    for fp in list(b.GetFootprints()):
        if fp.GetFPIDAsString() == f'{lib}:{name}':
            cb.remove(b, fp)
    fp = pcb.FootprintLoad(str(cb.KICAD / f'{lib}.pretty'), name)
    fp.SetFPID(pcb.LIB_ID(lib, name))
    fp.SetReference('LOGO1')
    b.Add(fp)
    fp.SetPosition(cb.at_mm(x, y))
    fp.Flip(fp.GetPosition(), pcb.FLIP_DIRECTION_LEFT_RIGHT)
    back_text(b, *NAME[:1], NAME[1], *NAME[2:])
    back_text(b, *BOARD_NAME[:1], BOARD_NAME[1], *BOARD_NAME[2:])


def stroke_font():
    """Put the Futura texts (copyright, revision) in KiCad's own font. Futura is not installed
    here, so every program that opens the board -- KiCad itself, the router -- stops at a
    'Font not found' message box. Plain text edit: drop the face and the cache rendered with it."""
    src = cb.BOARD.read_bytes().decode('utf-8')
    new = re.sub(r'(\r?\n)\t+\(face "Futura"\)', '', src)
    new = re.sub(r'(\(gr_text "[^"]*"(?:(?!\n\t\)).)*?)\r?\n\t\t\(render_cache .*?\r?\n\t\t\)', r'\1', new, flags=re.S)
    if new != src:
        cb.BOARD.write_bytes(new.encode('utf-8'))
    return src.count('(face "Futura")')


def copyright_fits(b):
    """In KiCad's font the copyright line runs 0.5 mm into R21's pad; a size smaller it clears."""
    for d in b.GetDrawings():
        if isinstance(d, pcb.PCB_TEXT) and d.GetText().startswith('Copyright'):
            d.SetTextSize(pcb.VECTOR2I(mm(1.15), mm(1.15)))
            d.SetTextThickness(mm(0.15))


def main():
    b = pcb.LoadBoard(str(cb.BOARD))
    caps(b)
    identity(b)
    copyright_fits(b)
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    cb.save(b)
    print('texts moved off Futura:', stroke_font())
    b = pcb.LoadBoard(str(cb.BOARD))
    b.BuildConnectivity()
    print('unconnected before routing:', b.GetConnectivity().GetUnconnectedCount(True))


if __name__ == '__main__':
    main()
