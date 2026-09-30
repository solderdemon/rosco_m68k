"""Route what cpld_board.py left unconnected, on top of the r2.13 copper, with KiCadRoutingTools.

KiCadRoutingTools (github.com/drandyhaas/KiCadRoutingTools, a Rust A* router) lives next to the
other shared tools in the workspace, in tools/KiCadRoutingTools with its own .venv; set KRT to
use another clone. This script runs it on a copy of the board and brings the result back:

  1. the nets to route are the ones KiCad's DRC reports unconnected, not a list kept here;
  2. route.py routes them on the outer layers only (the inner two are the GND and VCC planes)
     at the board's own 0.1524 mm track and clearance, with 0.6/0.3 mm vias, and may move
     r2.13 signal tracks out of the way (--rip-existing-nets). Sizes never drop below the
     request (--escalation off) and the project's design rules are left alone;
  3. a net that a rip-up broke is routed again in a second pass, and so on, until KiCad finds
     no signal net open or a pass gains nothing;
  4. repair_planes.py joins any piece of GND or VCC plane, or any supply pad, the new vias
     have cut off;
  5. back in pcbnew: a track the router necked below 0.1524 mm is widened, the zones are refilled, a supply pad whose thermal spokes land on nothing
     gets a solid connection (as route_lib does on the generated cards), and every stub KiCad
     calls dangling is swept, until none is left -- unless sweeping it opens a connection, in
     which case it goes back.

If the sweep opens a connection again (it can take a stub a new track ended on), steps 1-5
repeat. KiCad's DRC judges every step; nothing the router says about itself is trusted.

    "C:/Program Files/KiCad/10.0/bin/python.exe" design/tools/cpld_route.py [--finish] [--start BOARD]

--finish skips the routing and only does step 5 on the board as it is; --start BOARD begins
from another board (a pass kept from an earlier run) instead of design/kicad/solderdemon_m68k.kicad_pcb.
"""
from pathlib import Path
import json, os, re, shutil, subprocess, sys, tempfile
import pcbnew as pcb
import wx

wx.Log.EnableLogging(False)
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cpld_board as cb
from check_board import check

KRT = Path(os.environ.get('KRT', HERE.parents[2] / 'tools' / 'KiCadRoutingTools'))
KRT_PY = next((p for p in (KRT / '.venv' / 'Scripts' / 'python.exe', KRT / '.venv' / 'bin' / 'python')
               if p.exists()), Path(shutil.which('python') or 'python'))
PLANES = {'GND', 'VCC'}
SIZES = ['--clearance', '0.1524', '--via-size', '0.6', '--via-drill', '0.3',
         '--escalation', 'off', '--no-fix-drc-settings']
OUTER = ['--layers', 'F.Cu', 'B.Cu']
# repair_planes needs the plane layers in its layer map; tracks stay off them (cost < 0)
ALL = ['--layers', 'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu', '--layer-costs', '1', '-1', '-1', '3']
LOG = cb.KICAD / 'routing'


def krt(tool, board, out, *args):
    """Run a KiCadRoutingTools CLI on `board`, writing `out`; its log goes to design/kicad/routing."""
    LOG.mkdir(exist_ok=True)
    log = LOG / f'{out.stem}.log'
    env = dict(os.environ, MSYS2_ARG_CONV_EXCL='*', PYTHONUTF8='1')
    with open(log, 'w', encoding='utf-8') as f:
        r = subprocess.run([str(KRT_PY), '-X', 'utf8', str(KRT / 'py_router' / tool), str(board), str(out), *args],
                           cwd=KRT, env=env, stdout=f, stderr=subprocess.STDOUT)
    if not out.exists():
        raise SystemExit(f'{tool} wrote nothing (exit {r.returncode}), see {log}')
    # the router writes a project next to its output; the rules are the designer's, so it goes
    shutil.copy(cb.BOARD.with_suffix('.kicad_pro'), out.with_suffix('.kicad_pro'))
    return out


def open_nets(board):
    """(signal nets, supply pads/zones) that KiCad reports unconnected, after a refill."""
    sig, pwr = set(), 0
    for u in check(board)['unconnected_items']:
        nets = {m for i in u['items'] for m in re.findall(r'\[([^\]]+)\]', i['description'])}
        if nets & PLANES:
            pwr += 1
        sig |= nets - PLANES
    # DRC prints '/' in a net name; the board file, and so the router, spells it '{slash}'
    return sorted(n.replace('/', '{slash}') for n in sig), pwr


def finish():
    """Refill, give starved supply pads a solid connection, sweep dangling copper; save."""
    b = pcb.LoadBoard(str(cb.BOARD))
    healed = swept = 0
    # the router necks a track down next to a crowded pad; the board's floor is 0.1524 mm
    floor = pcb.FromMM(0.1524)
    narrow = [t for t in b.GetTracks() if t.Type() == pcb.PCB_TRACE_T and t.GetWidth() < floor]
    for t in narrow:
        t.SetWidth(floor)
    print(f'finish: {len(narrow)} tracks below 0.1524 mm widened')
    keep = set()                  # "dangling" copper that turned out to carry a connection
    opened = None
    for _ in range(12):
        pcb.ZONE_FILLER(b).Fill(b.Zones())
        cb.save(b)
        d = check(cb.BOARD)
        nets_open = {m for u in d['unconnected_items'] for i in u['items']
                     for m in re.findall(r'\[([^\]]+)\]', i['description'])}
        if opened is not None and nets_open - opened[0]:
            # the last sweep cut a connection: KRT sometimes ends a track on a pad's copper
            # rather than its centre, and KiCad calls that end dangling. Put it back.
            back = [t for t in opened[1] if t.GetNetname() in nets_open - opened[0]]
            for t in back:
                b.Add(t)
                keep.add(t.m_Uuid.AsString())
            swept -= len(back)
            opened = None
            continue
        starved = {(m.group(2), m.group(1)) for v in d['violations'] if v['type'] == 'starved_thermal'
                   for i in v['items'] for m in [re.match(r'PTH pad (\S+) \[\S+\] of (\S+)', i['description'])] if m}
        dead = {i['uuid'] for v in d['violations'] if v['type'] in ('track_dangling', 'via_dangling') for i in v['items']}
        dead -= keep
        if not starved and not dead:
            break
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if (fp.GetReference(), p.GetNumber()) in starved:
                    p.SetLocalZoneConnection(pcb.ZONE_CONNECTION_FULL)
                    healed += 1
        gone = [t for t in b.GetTracks() if t.m_Uuid.AsString() in dead]
        for t in gone:
            b.Remove(t)
        opened = (nets_open, gone)
        cb._GRAVE.extend(gone)
        swept += len(gone)
    print(f'finish: {healed} supply pads given a solid connection, {swept} dangling tracks/vias swept')
    return b


def main():
    for _ in range(3):
        if '--finish' not in sys.argv:
            route()
        b = finish()
        cb.save(b)
        d = check(cb.BOARD)
        # sweeping can take away a stub a connection needed; route what that opened again
        if not d['unconnected_items'] or '--finish' in sys.argv:
            break
    errors = [v for v in d['violations'] if v['severity'] == 'error']
    print(f"DRC: {len(errors)} errors, {len(d['unconnected_items'])} unconnected")
    for v in errors:
        print('  ', v['type'], [i['description'] for i in v['items']])


def route():
    work = Path(tempfile.mkdtemp())
    cur = work / 'r0.kicad_pcb'
    start = sys.argv[sys.argv.index('--start') + 1] if '--start' in sys.argv else cb.BOARD
    shutil.copy(start, cur)
    shutil.copy(cb.BOARD.with_suffix('.kicad_pro'), cur.with_suffix('.kicad_pro'))
    sig, pwr = open_nets(cur)
    print(f'to route: {len(sig)} signal nets, {pwr} supply connections')
    for n in range(1, 6):
        if not sig:
            break
        out = krt('route.py', cur, work / f'r{n}.kicad_pcb', '--nets', *sig, '--track-width', '0.1524',
                  '--rip-existing-nets', '*', *OUTER, *SIZES)
        left, pwr = open_nets(out)
        print(f'pass {n}: routed {len(sig)} nets, {len(left)} still open {left}, {pwr} supply connections open')
        if len(left) >= len(sig):
            break
        cur, sig = out, left
    if pwr:
        out = krt('repair_planes.py', cur, work / 'planes.kicad_pcb', '--nets', *sorted(PLANES),
                  '--track-width', '0.3', '--min-track-width', '0.2', '--repair-pads', '--no-kicad-recheck', *ALL, *SIZES)
        cur = out
        sig, pwr = open_nets(cur)
        print(f'repair_planes: {len(sig)} signal nets, {pwr} supply connections open')
    shutil.copy(cur, cb.BOARD)


if __name__ == '__main__':
    main()
