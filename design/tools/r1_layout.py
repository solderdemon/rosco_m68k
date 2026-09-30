"""Turn r2.42 into SolderDemon m68k r1: the DUART IC4 joins the CPLD column, the board grows longer.

r2.42 has IC3 (glue) and IC2 (decoder) one above the other, with the DUART IC4 below them but
8 mm further right. r1 puts all three PLCC-44 sockets in one column. IC4 cannot simply move left:
its left pins would land on the right row of the RAM U4. So the board is stretched instead:

  1. everything right of a cut is moved D mm to the right, and the board with it. The cut runs
     between the CPLDs and the CPU/decoupling on the left, and further down between U4 and the
     DUART; the step between the two runs under IC2. A track that crosses a vertical part of the
     cut is split there and bridged by a horizontal piece D long. Nothing gets closer to
     anything else by a horizontal stretch, so the copper stays as clean as it was. A track
     crossing the step itself is torn up and left to the router;
  2. IC4 goes under IC2, courtyards 1.3 mm apart like IC3/IC2, and its old copper is cut back;
     C22, which stood where the socket now goes, moves into the space IC4 left;
  3. copper still breaking a rule after that is torn up too; cpld_route.py routes what is open;
  4. the board starts its own numbering: revision r1.

Always starts again from the r2.42 board in git (BASE), so running it twice gives the same board.

    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/r1_layout.py
    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/cpld_route.py
"""
from pathlib import Path
import re, subprocess, sys, tempfile
import pcbnew as pcb
import wx

wx.Log.EnableLogging(False)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cpld_board as cb
from check_board import check

BASE = 'ab9931f'                 # r2.42, silkscreen cleaned
D = 5.0                          # how much longer the board gets, mm
X1, X2, YS = 173.3, 176.6, 108.5  # the cut: x = X1 above YS, x = X2 below it
IC4_CENTRE = (185.30 + D, 119.70)  # the CPLDs' column; top of the courtyard 1.3 mm under IC2
C22_AT = ((205.60 + D, 124.00), 90)
REVISION = 'r1'
DATE = '2026-09-30'

mm, T = pcb.FromMM, pcb.ToMM


def load_base():
    blob = subprocess.run(['git', 'show', f'{BASE}:design/kicad/solderdemon_m68k.kicad_pcb'], cwd=cb.KICAD,
                          capture_output=True, check=True).stdout
    tmp = Path(tempfile.mkdtemp()) / 'base.kicad_pcb'
    tmp.write_bytes(blob)
    tmp.with_suffix('.kicad_pro').write_bytes(cb.BOARD.with_suffix('.kicad_pro').read_bytes())
    return pcb.LoadBoard(str(tmp))


def right(x, y):
    """Is the point (mm) on the side of the cut that moves?"""
    return x > (X1 if y < YS else X2)


def right_i(p):
    return right(T(p.x), T(p.y))


def crossing(a, b):
    """Where segment a-b (mm) crosses a vertical part of the cut, or None if it crosses the step."""
    for x, lo, hi in ((X1, -1e9, YS), (X2, YS, 1e9)):
        if (a[0] - x) * (b[0] - x) < 0:
            y = a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
            if lo <= y < hi:
                return x, y
    return None


def stretch(b):
    shift = pcb.VECTOR2I(mm(D), 0)
    for fp in b.GetFootprints():
        sides = {right_i(p.GetPosition()) for p in fp.Pads()} or {right_i(fp.GetPosition())}
        if fp.GetReference() != 'IC4':
            assert len(sides) == 1, f'{fp.GetReference()} straddles the cut'
        if right_i(fp.GetPosition()):
            fp.Move(shift)
    torn, bridged = [], 0
    for t in list(b.GetTracks()):
        if t.Type() == pcb.PCB_VIA_T:
            if right_i(t.GetPosition()):
                t.Move(shift)
            continue
        s, e = t.GetStart(), t.GetEnd()
        rs, re_ = right_i(s), right_i(e)
        if rs and re_:
            t.Move(shift)
        elif rs != re_:
            a, c = (T(s.x), T(s.y)), (T(e.x), T(e.y))
            hit = crossing(a, c)
            if hit is None or right(*a) == right(*c):
                torn.append(t)
                continue
            x, y = hit
            cut = pcb.VECTOR2I(mm(x), mm(y))
            moved = pcb.VECTOR2I(mm(x + D), mm(y))
            # the left piece keeps this track; the right piece and the bridge are new
            for (p, q) in ((cut, moved), (moved, (e if re_ else s) + shift)):
                n = pcb.PCB_TRACK(b)
                n.SetStart(p); n.SetEnd(q)
                n.SetWidth(t.GetWidth()); n.SetLayer(t.GetLayer()); n.SetNet(t.GetNet())
                b.Add(n)
            if rs:
                t.SetStart(cut)
            else:
                t.SetEnd(cut)
            bridged += 1
    for t in torn:
        cb.remove(b, t)
    for d in b.GetDrawings():
        if isinstance(d, pcb.PCB_SHAPE) and d.GetShape() == pcb.SHAPE_T_SEGMENT:
            if right_i(d.GetStart()):
                d.SetStart(d.GetStart() + shift)
            if right_i(d.GetEnd()):
                d.SetEnd(d.GetEnd() + shift)
        elif right_i(d.GetBoundingBox().GetCenter()):
            d.Move(shift)
    for z in b.Zones():
        o = z.Outline()
        for i in range(o.TotalVertices()):
            v = o.CVertex(i)
            if right_i(v):
                o.SetVertex(i, pcb.VECTOR2I(v.x + shift.x, v.y))
    return bridged, sorted({t.GetNetname() for t in torn})


def courtyard_box(fp):
    return fp.GetCourtyard(pcb.F_CrtYd).BBox()


def move_ic4(b):
    ic4 = cb.find(b, 'IC4')
    old = courtyard_box(ic4)
    c = old.GetCenter()
    ic4.Move(pcb.VECTOR2I(mm(IC4_CENTRE[0]) - c.x, mm(IC4_CENTRE[1]) - c.y))
    c22 = cb.find(b, 'C22')
    (x, y), rot = C22_AT
    c22.SetOrientationDegrees(rot)
    c22.SetPosition(cb.at_mm(x, y))
    return ic4, c22, old


def label_ic4(b):
    """Name and reference inside the socket, like the CPLDs above it."""
    x, y = IC4_CENTRE
    ic4 = cb.find(b, 'IC4')
    ic4.Reference().SetPosition(cb.at_mm(x, y - 2.2))
    ic4.Reference().SetTextAngleDegrees(0)
    ic4.Reference().SetTextSize(pcb.VECTOR2I(mm(1.0), mm(1.0)))
    ic4.Reference().SetTextThickness(mm(0.15))
    if not any(isinstance(d, pcb.PCB_TEXT) and d.GetText() == 'DUART' for d in b.GetDrawings()):
        t = pcb.PCB_TEXT(b)
        t.SetText('DUART')
        t.SetPosition(cb.at_mm(x, y + 0.9))
        t.SetLayer(pcb.F_SilkS)
        t.SetTextSize(pcb.VECTOR2I(mm(0.9), mm(0.9)))
        t.SetTextThickness(mm(0.15))
        b.Add(t)


def revision(b):
    for d in b.GetDrawings():
        if isinstance(d, pcb.PCB_TEXT) and re.fullmatch(r'[Rr]evision 2\.42', d.GetText()):
            d.SetText(d.GetText().replace('2.42', REVISION))
    tb = b.GetTitleBlock()
    tb.SetRevision(REVISION)
    tb.SetDate(DATE)
    tb.SetComment(4, 'SolderDemon m68k r1; based on rosco_m68k r2.x')


def schematic_revision():
    for sch in cb.KICAD.glob('*.kicad_sch'):
        src = sch.read_bytes().decode('utf-8')
        new = re.sub(r'\(rev "[^"]*"\)', f'(rev "{REVISION}")', src)
        new = re.sub(r'\(date "[^"]*"\)', f'(date "{DATE}")', new)
        if new != src:
            sch.write_bytes(new.encode('utf-8'))


def tear_offenders(b):
    """Tear up every track and via KiCad still finds in a clearance or short violation."""
    d = check(cb.BOARD)
    bad = {i['uuid'] for v in d['violations'] if v['severity'] == 'error'
           and v['type'] in ('clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance',
                             'copper_edge_clearance', 'via_dangling', 'track_dangling')
           for i in v['items']}
    gone = [t for t in b.GetTracks() if t.m_Uuid.AsString() in bad]
    for t in gone:
        cb.remove(b, t)
    return len(gone)


def main():
    b = load_base()
    bridged, torn = stretch(b)
    print(f'stretched by {D} mm: {bridged} tracks bridged across the cut, step torn up on {torn}')
    ic4, c22, old = move_ic4(b)
    nets, n = cb.rip_collisions(b, [ic4, c22])
    print(f'IC4 into the column: {n} tracks/vias in the way on {len(nets)} nets')
    ic4_nets = {p.GetNetname() for p in ic4.Pads()} - {'', 'GND', 'VCC'}
    cut = 0
    for box in (old, courtyard_box(ic4)):
        box.Inflate(mm(0.5))
        cut += cb.prune(b, ic4_nets | nets - {'GND', 'VCC'}, region=box)
    print('old DUART stubs cut back:', cut)
    n, left = cb.plane_vias(b, [ic4])
    print('DUART supply pins taken to the planes:', n, '; left to repair_planes:', left)
    label_ic4(b)
    revision(b)
    pcb.ZONE_FILLER(b).Fill(b.Zones())
    cb.save(b)
    for _ in range(4):
        b = pcb.LoadBoard(str(cb.BOARD))
        n = tear_offenders(b)
        if not n:
            break
        print('torn up for clearance:', n)
        pcb.ZONE_FILLER(b).Fill(b.Zones())
        cb.save(b)
    schematic_revision()
    b = pcb.LoadBoard(str(cb.BOARD))
    b.BuildConnectivity()
    print('unconnected before routing:', b.GetConnectivity().GetUnconnectedCount(True))


if __name__ == '__main__':
    main()
