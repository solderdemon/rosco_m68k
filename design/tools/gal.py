"""GAL22V10 / ATF22V10C: pin list from a GALasm .pld and a simulator that runs the compiled JEDEC fuse map.

The simulation works from the fuses, not from the equations, so it checks what GALasm actually
assembled (polarity, feedback, output enables). Fuse map (5892 fuses, 44 columns per row):
  row 0 = asynchronous reset (AR), row 131 = synchronous preset (SP);
  OLMC blocks (first row = output enable, the rest ORed): pin 23 rows 1-9, pin 22 10-20,
  pin 21 21-33, pin 20 34-48, pin 19 49-65, pin 18 66-82, pin 17 83-97, pin 16 98-110,
  pin 15 111-121, pin 14 122-130;
  5808 + 2k / 5809 + 2k = S0 (1 = active high) / S1 (1 = combinational) for pin 23 - k.
Unprogrammed rows are all 0 (false). A fuse at 0 connects its literal; column 2i is signal i, 2i + 1 its complement. Feedback of a
registered OLMC is /Q, of a combinational one the pin. Registers clock on the rising edge of pin 1.
"""
import re

COL = {1: 0, 2: 4, 3: 8, 4: 12, 5: 16, 6: 20, 7: 24, 8: 28, 9: 32, 10: 36, 11: 40, 13: 42,
       14: 38, 15: 34, 16: 30, 17: 26, 18: 22, 19: 18, 20: 14, 21: 10, 22: 6, 23: 2}
BLOCK = {23: (1, 9), 22: (10, 11), 21: (21, 13), 20: (34, 15), 19: (49, 17),
         18: (66, 17), 17: (83, 15), 16: (98, 13), 15: (111, 11), 14: (122, 9)}
FUSES = 5892


def pins(pld_text):
    """{pin number: name} from a GALasm source (24 names after the type and signature lines)."""
    lines = [l.split(';')[0].strip() for l in pld_text.splitlines()]
    lines = [l for l in lines if l]
    assert lines[0] == 'GAL22V10', lines[0]
    names = ' '.join(lines[2:]).split()[:24]
    assert len(names) == 24 and names[11] == 'GND' and names[23] == 'VCC', names
    return {i + 1: n for i, n in enumerate(names)}


def jedec(text):
    body = text[text.index('\x02') + 1 if '\x02' in text else 0:]
    fuses = [0] * FUSES
    m = re.search(r'\*F([01])', body)
    if m: fuses = [int(m.group(1))] * FUSES
    for addr, bits in re.findall(r'\*L(\d+)\s+([01\s]+)', body):
        for i, b in enumerate(re.sub(r'\s', '', bits)):
            fuses[int(addr) + i] = int(b)
    return fuses




def signals(pld_text):
    """{name: 'reg' | 'tri' | 'comb'} for every output defined by an equation (AR/SP excluded)."""
    body = pld_text.split('DESCRIPTION')[0]
    out = {}
    for name, ext in re.findall(r'^\s*/?(\w+)(?:\.(\w+))?\s*=', body, flags=re.M):
        if name in ('AR', 'SP'): continue
        kind = {'R': 'reg', 'T': 'tri', 'E': 'tri'}.get(ext.upper(), 'comb')
        if out.get(name) != 'reg': out[name] = kind if out.get(name) != 'tri' or kind == 'reg' else 'tri'
    return out


class Gal22V10:
    def __init__(self, fuses):
        f = fuses; assert len(f) == FUSES
        self.rows = []                                   # (columns that must be 1, columns that must be 0)
        for r in range(132):
            one = zero = 0
            for c in range(44):
                if f[r * 44 + c] == 0:
                    if c & 1: zero |= 1 << (c >> 1)
                    else: one |= 1 << (c >> 1)
            self.rows.append((one, zero))
        self.s0 = {23 - k: f[5808 + 2 * k] for k in range(10)}
        self.s1 = {23 - k: f[5809 + 2 * k] for k in range(10)}
        self.q = {p: 0 for p in BLOCK}                   # power-up reset
        self.terms = {p: [self.rows[r] for r in range(st + 1, st + n)] for p, (st, n) in BLOCK.items()}

    @staticmethod
    def _term(row, cv):
        one, zero = row
        return int(cv & one == one and not cv & zero)

    def _columns(self, level):
        """level: pin -> 0/1 (net values). Returns the 22 signals as a bit mask."""
        cv = 0
        for pin, col in COL.items():
            v = 1 - self.q[pin] if pin in BLOCK and not self.s1[pin] else level.get(pin, 0)
            cv |= v << (col >> 1)
        return cv

    def _sum(self, pin, cv):
        return int(any(cv & one == one and not cv & zero for one, zero in self.terms[pin]))

    def outputs(self, level):
        """pin -> 0/1, or None when disabled. Applies the asynchronous reset."""
        cv = self._columns(level)
        if self._term(self.rows[0], cv):
            for p in self.q: self.q[p] = 0
            cv = self._columns(level)
        out = {}
        for pin, (start, n) in BLOCK.items():
            if not self._term(self.rows[start], cv): out[pin] = None; continue
            v = self._sum(pin, cv) if self.s1[pin] else self.q[pin]
            out[pin] = v if self.s0[pin] else 1 - v
        return out

    def clock(self, level):
        """Rising edge on pin 1: level = pin values just before the edge."""
        cv = self._columns(level)
        sp = self._term(self.rows[131], cv)
        self.q.update({p: (1 if sp else self._sum(p, cv)) for p in BLOCK if not self.s1[p]})
