"""Prove that the two ATF1502AS of r2.14 behave exactly like the four ATF22V10C of r2.13.

The r2.13 side runs the real JEDEC fuse maps of code/pld/{address_decoder,duartsel,glue,watchdog}
through gal.py, wired together the way the r2.13 board wires them (BOOT and ANYIACK between the
GALs, IOSEL from IC2 to IC3, the combinational feedback of IC2's PPDTACK and IC6's WDEN). The
r2.14 side runs code/pld/cpld/*.pld through cupl.py. Both see the same random bus traffic -- with
the clock, AS and reset biased so that the boot latch gets set and the watchdog gets to fire --
and every board-level net they drive has to agree at every step.

RESET, HALT, DTACK and BERR are open drain with pull-ups, and RESET/HALT can also be pulled low
by the CPU, so those are resolved as wired-AND nets with an extra external driver.

    python design/tools/verify_cpld.py [steps]
"""
from pathlib import Path
import random, sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gal, cupl

PLD = HERE.parent.parent / 'code' / 'pld'
OLD = {'IC2': 'address_decoder/ic2_address_decoder', 'IC3': 'duartsel/ic3_duart_sel',
       'IC5': 'glue/ic5_glue_logic', 'IC6': 'watchdog/ic6_watchdog'}
NEW = {'IC2': 'cpld/ic2_decoder', 'IC3': 'cpld/ic3_glue'}
# GALasm pin name -> board net, where the r2.13 sources and schematic disagree
RENAME = {'EVENRAM': 'EVENRAMSEL', 'ODDRAM': 'ODDRAMSEL', 'EVENROM': 'EVENROMSEL',
          'ODDROM': 'ODDROMSEL', 'DUIACK': 'DUAIACK', 'IACK': 'ANYIACK'}

INPUTS = [f'A{i}' for i in (1, 2, 3)] + [f'A{i}' for i in range(6, 24)] + \
         ['UDS', 'LDS', 'AS', 'RW', 'FC0', 'FC1', 'FC2', 'HWRST', 'LGEXP', 'CLK']
OPEN_DRAIN = ['RESET', 'HALT', 'DTACK', 'BERR']
OUTPUTS = ['EVENRAMSEL', 'ODDRAMSEL', 'EVENROMSEL', 'ODDROMSEL', 'IOSEL', 'EXPSEL', 'WR',
           'RUNLED', 'DUASEL', 'DUAIACK'] + OPEN_DRAIN


class OldBoard:
    """The four GALs of r2.13 on their nets. Pins with no net on the board get a private one,
    because a combinational OLMC feeds back from its own pin (see AGENTS.md)."""

    def __init__(self):
        self.gals, self.pins = {}, {}
        for ref, stem in OLD.items():
            src = (PLD / f'{stem}.pld').read_text()
            self.gals[ref] = gal.Gal22V10(gal.jedec((PLD / f'{stem}.jed').read_text()))
            names = gal.pins(src)
            self.pins[ref] = {p: (RENAME.get(n, n) if n not in ('NC', 'GND', 'VCC') else f'{ref}.{p}')
                              for p, n in names.items()}
        # IC6 pin 13 is called /OE in the source but is tied to GND on the board
        self.pins['IC6'][13] = 'GND'

    def settle(self, ext):
        """ext: input nets plus RESET_EXT/HALT_EXT (1 = CPU pulls the line low). Returns nets."""
        net = dict(ext, GND=0, VCC=1)
        drive = {}
        for _ in range(8):
            drive = {}
            for ref, g in self.gals.items():
                lvl = {p: net.get(n, 1) for p, n in self.pins[ref].items()}
                for p, v in g.outputs(lvl).items():
                    n = self.pins[ref][p]
                    if v is not None:
                        drive.setdefault(n, []).append(v)
            new = dict(net)
            for n, vs in drive.items():
                if n in OPEN_DRAIN:
                    continue
                assert len(vs) == 1, (n, vs)
                new[n] = vs[0]
            for n in OPEN_DRAIN:
                low = any(v == 0 for v in drive.get(n, [])) or ext.get(n + '_EXT', 0)
                assert all(v == 0 for v in drive.get(n, [])), f'{n} driven high'
                new[n] = 0 if low else 1
            if new == net:
                return net
            net = new
        raise AssertionError('r2.13 nets do not settle')

    def clock(self, net, pin_name, rising):
        for ref, g in self.gals.items():
            if self.pins[ref][1] in rising:
                g.clock({p: net.get(n, 1) for p, n in self.pins[ref].items()})


class NewBoard:
    def __init__(self):
        self.dev = {ref: cupl.Device((PLD / f'{stem}.pld').read_text()) for ref, stem in NEW.items()}
        self.q = {ref: d.reset_state() for ref, d in self.dev.items()}

    def settle(self, ext):
        net = dict({n: 1 for n in OUTPUTS}, **ext)
        for n in OPEN_DRAIN:
            net[n] = 0 if ext.get(n + '_EXT', 0) else 1
        for _ in range(8):
            drive = {}
            for ref, d in self.dev.items():
                for n, v in d.outputs(net, self.q[ref]).items():
                    if v is not None:
                        drive.setdefault(n, []).append(v)
            new = dict(net)
            for n, vs in drive.items():
                if n in OPEN_DRAIN:
                    continue
                assert len(vs) == 1, (n, vs)
                new[n] = vs[0]
            for n in OPEN_DRAIN:
                assert all(v == 0 for v in drive.get(n, [])), f'{n} driven high'
                new[n] = 0 if any(v == 0 for v in drive.get(n, [])) or ext.get(n + '_EXT', 0) else 1
            if new == net:
                return net
            net = new
        raise AssertionError('r2.14 nets do not settle')

    def clock(self, net, rising):
        for ref, d in self.dev.items():
            self.q[ref] = d.clock_edge(net, self.q[ref], rising)


def stimulus(rng, prev):
    """Next input vector. Mostly holds the bus still and toggles CLK, so bus cycles last long
    enough for the watchdog; sometimes starts a fresh cycle, sometimes resets."""
    v = dict(prev)
    v['CLK'] = 1 - prev['CLK']
    r = rng.random()
    if r < 0.03:                                   # new bus cycle: new address and strobes
        for n in INPUTS:
            if n not in ('CLK', 'HWRST', 'LGEXP'):
                v[n] = rng.getrandbits(1)
        # bias towards the interesting decodes: low memory, ROM, IO, CPU space
        top = rng.choice([0x0, 0xE, 0xF, rng.getrandbits(4)])
        for i, a in enumerate((20, 21, 22, 23)):
            v[f'A{a}'] = top >> i & 1
        if rng.random() < 0.3:
            v['FC0'] = v['FC1'] = v['FC2'] = 1
        elif rng.random() < 0.5:
            v['FC2'], v['FC1'], v['FC0'] = 1, 0, 1  # supervisor program
        if rng.random() < 0.5:
            for a in range(6, 20):
                v[f'A{a}'] = 0 if a < 18 or rng.random() < 0.5 else v[f'A{a}']
    elif r < 0.10:
        v['AS'] = 1 - prev['AS']
    elif r < 0.11:
        v['HWRST'] = 1 - prev['HWRST']
    elif r < 0.115:
        v['LGEXP'] = 1 - prev['LGEXP']
    elif r < 0.12:
        v['RESET_EXT'] = 1 - prev['RESET_EXT']
    elif r < 0.125:
        v['HALT_EXT'] = 1 - prev['HALT_EXT']
    return v


def main(steps=400000, seed=1):
    rng = random.Random(seed)
    old, new = OldBoard(), NewBoard()
    v = {n: 1 for n in INPUTS}
    v.update(HWRST=1, CLK=0, LGEXP=1, RESET_EXT=0, HALT_EXT=0)
    prev_old = prev_new = None
    seen = {n: set() for n in OUTPUTS}
    boot_set = berr_fired = 0
    for step in range(steps):
        a = old.settle(v)
        b = new.settle(v)
        for n in OUTPUTS:
            if a[n] != b[n]:
                diff = {k: v[k] for k in sorted(v)}
                raise SystemExit(f'step {step}: {n} r2.13={a[n]} r2.14={b[n]}\n inputs {diff}\n'
                                 f' old q {[(r, g.q) for r, g in old.gals.items()]}\n new q {new.q}')
            seen[n].add(a[n])
        boot_set += new.q['IC2']['BOOT']
        berr_fired += 1 - b['BERR']
        nxt = stimulus(rng, v)
        rising = {n for n in ('AS', 'CLK') if v[n] == 0 and nxt[n] == 1}
        # registers sample the levels just before the edge
        if rising:
            old.clock(a, None, rising)
            new.clock(b, rising)
        v = nxt
    stuck = [n for n, s in seen.items() if len(s) < 2]
    print(f'{steps} steps, all {len(OUTPUTS)} nets agree; BOOT set in {boot_set} steps, '
          f'BERR asserted in {berr_fired} steps')
    assert not stuck, f'never toggled: {stuck}'
    assert boot_set and berr_fired


if __name__ == '__main__':
    main(*(int(x) for x in sys.argv[1:]))
