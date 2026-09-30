"""Trim the dangling copper KiCadRoutingTools leaves behind, without opening a connection.

cpld_route.py sweeps a dangling track whole, and puts it back when that opens a net: some of them
carry a connection through their middle (another track ends on them) and only overshoot the
junction. Here such a track is cut back to its nearest junction instead; a track with neither end
connected goes; a via that joins tracks on one layer only becomes a short track on that layer; a
track shrunk to nothing goes. KiCad's DRC names the items; run until it names none.

    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/trim_stubs.py
"""
from pathlib import Path
import sys

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cpld_board as cb
from check_board import check

NEAR = 1000                      # nm: "the same point"


def uid(o):
    return o.m_Uuid.AsString()   # SWIG hands out a new wrapper each time, so `is` does not work


def trim(b, t, others, pads):
    l = t.GetLayer()

    def linked(e):
        return any(p.IsOnLayer(l) and p.HitTest(e) for p in pads) or any(
            (o.Type() == pcb.PCB_VIA_T and (o.GetPosition() - e).EuclideanNorm() <= o.GetWidth(l) // 2) or
            (o.Type() != pcb.PCB_VIA_T and o.GetLayer() == l and o.HitTest(e, 0)) for o in others)

    ends = {'s': linked(t.GetStart()), 'e': linked(t.GetEnd())}
    if not any(ends.values()):
        cb.remove(b, t)
        return 'removed'
    for which, ok in ends.items():
        if ok:
            continue
        loose = t.GetStart() if which == 's' else t.GetEnd()
        pts = [c for o in others
               for c in ([o.GetPosition()] if o.Type() == pcb.PCB_VIA_T else
                         [o.GetStart(), o.GetEnd()] if o.GetLayer() == l else [])
               if t.HitTest(c, 0) and (c - loose).EuclideanNorm() > NEAR]
        pts += [p.GetPosition() for p in pads if p.IsOnLayer(l) and t.HitTest(p.GetPosition(), 0)]
        (t.SetStart if which == 's' else t.SetEnd)(min(pts, key=lambda c: (c - loose).EuclideanNorm()))
    return 'trimmed'


def via_to_track(b, v, others):
    on = [o for o in others if o.Type() != pcb.PCB_VIA_T and o.HitTest(v.GetPosition(), 0)]
    layers = {o.GetLayer() for o in on}
    if len(layers) != 1:
        return None
    l = layers.pop()
    for o in on:
        for e in (o.GetStart(), o.GetEnd()):
            if v.HitTest(e) and (e - v.GetPosition()).EuclideanNorm() > NEAR:
                n = pcb.PCB_TRACK(b)
                n.SetStart(e); n.SetEnd(v.GetPosition())
                n.SetLayer(l); n.SetWidth(o.GetWidth()); n.SetNet(v.GetNet())
                b.Add(n)
    cb.remove(b, v)
    return 'via to track'


def main():
    for _ in range(5):
        d = check(cb.BOARD)
        ids = {i['uuid'] for v in d['violations'] if v['type'] in ('track_dangling', 'via_dangling')
               for i in v['items']}
        b = pcb.LoadBoard(str(cb.BOARD))
        done = []
        for t in [t for t in b.GetTracks() if uid(t) in ids]:
            others = [o for o in b.GetTracks() if uid(o) != uid(t) and o.GetNetname() == t.GetNetname()]
            pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == t.GetNetname()]
            what = via_to_track(b, t, others) if t.Type() == pcb.PCB_VIA_T else trim(b, t, others, pads)
            done.append(f'{what} {t.GetNetname()}')
        for t in [t for t in b.GetTracks() if t.Type() == pcb.PCB_TRACE_T and t.GetLength() < NEAR]:
            cb.remove(b, t)
            done.append(f'zero length {t.GetNetname()}')
        if not done:
            break
        print('\n'.join(done))
        pcb.ZONE_FILLER(b).Fill(b.Zones())
        cb.save(b)
    d = check(cb.BOARD)
    print(f"dangling: {sum(v['type'].endswith('dangling') for v in d['violations'])}, "
          f"unconnected: {len(d['unconnected_items'])}")


if __name__ == '__main__':
    main()
