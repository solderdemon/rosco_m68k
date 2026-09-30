"""Reader and simulator for the subset of CUPL used in code/pld/cpld/*.pld.

Supports PIN / PINNODE / FIELD declarations (with [a..b] ranges and lists), intermediate variables,
the operators ! & # $ and parentheses, numbers ('b'/'d'/'h', bare = hex), field equality and ranges
(FIELD:'d'n, FIELD:['d'lo..'d'hi]) and the extensions .d .t .ck .ar .oe .io. Each register is clocked
by the rising edge of an input pin named in its .ck. It is not a compiler: it lets the netlist
simulation run the real source.
"""
import re

HEADER = {'name', 'partno', 'date', 'revision', 'designer', 'company', 'assembly', 'location', 'device', 'property'}


def number(tok):
    m = re.fullmatch(r"'([bdhoBDHO])'([0-9a-fA-F]+)", tok)
    if m: return int(m.group(2), {'b': 2, 'd': 10, 'h': 16, 'o': 8}[m.group(1).lower()])
    return int(tok, 16)


def expand(s):
    """'[A1..16]' / '[X8..0]' / '[PG0..1, VIDEO_ON]' / 'NAME' -> list of names."""
    s = s.strip()
    if not s.startswith('['): return [s]
    out = []
    for item in s[1:-1].split(','):
        item = item.strip()
        m = re.fullmatch(r'([A-Za-z_]+?)(\d+)\.\.(\d+)', item)
        if m:
            a, b = int(m.group(2)), int(m.group(3))
            out += [f'{m.group(1)}{i}' for i in (range(a, b + 1) if a <= b else range(a, b - 1, -1))]
        else:
            out.append(item)
    return out


class Device:
    def __init__(self, text):
        text = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
        self.pins, self.nodes, self.fields, self.eq = {}, [], {}, {}
        for st in (s.strip() for s in text.split(';')):
            if not st: continue
            word = st.split()[0].lower()
            if word in HEADER: continue
            if word == 'pin':
                nums, names = (x.strip() for x in st[3:].split('='))
                nums = [int(n) for n in nums.strip('[]').split(',')]; names = expand(names)
                assert len(nums) == len(names) and not any(n.startswith('!') for n in names), st
                for n, name in zip(nums, names):
                    assert n not in self.pins, f'pin {n} used twice'
                    self.pins[n] = name
            elif word == 'pinnode':
                self.nodes += expand(st.split('=', 1)[1])
            elif word == 'field':
                name, lst = (x.strip() for x in st[5:].split('=', 1)); self.fields[name] = expand(lst)
            else:
                lhs, rhs = (x.strip() for x in st.split('=', 1))
                m = re.fullmatch(r'(\[[^\]]*\]|\w+)(?:\.(\w+))?', lhs); assert m, st
                ext = (m.group(2) or '').lower()
                targets = expand(m.group(1))
                const = re.fullmatch(r"'[bdhoBDHO]'[0-9a-fA-F]+", rhs)
                for i, t in enumerate(reversed(targets)):          # a constant spreads LSB-last like CUPL
                    key = (t, ext)
                    assert key not in self.eq, f'{t}.{ext} defined twice'
                    self.eq[key] = f"'b'{number(rhs) >> i & 1}" if const and len(targets) > 1 else rhs
        names = set(self.pins.values())
        self.inputs = sorted(n for n in names if not any((n, e) in self.eq for e in ('', 'd', 't')))
        self.regs = sorted({t for t, e in self.eq if e in ('d', 't')})
        self.comb = [t for t, e in self.eq if e == '']
        for r in self.regs:
            assert (r, 'ck') in self.eq, f'{r} has no clock'
        self.clocks = {r: self.eq[(r, 'ck')].strip() for r in self.regs}
        assert set(self.clocks.values()) <= set(self.inputs), self.clocks
        self._compile()

    # ---- expression -> python -------------------------------------------------------------
    def _py(self, expr):
        toks = re.findall(r"'[bdhoBDHO]'[0-9a-fA-F]+|\w+(?:\.\w+)?|\.\.|[!&#$()\[\]:,]", expr)
        pos = [0]

        def peek(): return toks[pos[0]] if pos[0] < len(toks) else None
        def take(t=None):
            tok = toks[pos[0]]; pos[0] += 1
            assert t is None or tok == t, (expr, t, tok)
            return tok

        def xorx():                                    # CUPL precedence: ! then & then # then $
            parts = [orx()]
            while peek() == '$': take(); parts.append(orx())
            return '(' + ' ^ '.join(parts) + ')' if len(parts) > 1 else parts[0]

        def orx():
            parts = [andx()]
            while peek() == '#': take(); parts.append(andx())
            return '(' + ' | '.join(parts) + ')' if len(parts) > 1 else parts[0]

        def andx():
            parts = [notx()]
            while peek() == '&': take(); parts.append(notx())
            return '(' + ' & '.join(parts) + ')' if len(parts) > 1 else parts[0]

        def notx():
            if peek() == '!': take(); return f'(1 - {notx()})'
            if peek() == '(': take(); e = xorx(); take(')'); return e
            tok = take()
            if tok.startswith("'"): return str(number(tok))
            if peek() == ':':
                take(); bits = self.fields[tok]
                val = ' | '.join(f'{self.ref(b)} << {len(bits) - 1 - i}' for i, b in enumerate(bits))
                if peek() == '[':
                    take(); lo = number(take()); take('..'); hi = number(take()); take(']')
                    return f'int({lo} <= ({val}) <= {hi})'
                return f'int(({val}) == {number(take())})'
            return self.ref(tok)

        out = xorx(); assert pos[0] == len(toks), (expr, toks[pos[0]:])
        return out

    def ref(self, tok):
        name, _, ext = tok.partition('.')
        if ext.lower() == 'io' or name in self.inputs: return f'p[{name!r}]'
        if name in self.regs: return f'q[{name!r}]'
        if (name, '') in self.eq: return f'c[{name!r}]'
        raise KeyError(f'unknown signal {tok}')

    def _compile(self):
        order, seen = [], set()

        def visit(n, stack=()):
            if n in seen: return
            assert n not in stack, f'combinational loop through {n}'
            for dep in re.findall(r"c\['(\w+)'\]", self._py(self.eq[(n, '')])): visit(dep, stack + (n,))
            seen.add(n); order.append(n)
        for n in self.comb: visit(n)
        lines = ['def comb(p, q):', '    c = {}']
        lines += [f'    c[{n!r}] = {self._py(self.eq[(n, "")])}' for n in order]
        lines += ['    return c', '', 'def nxt(p, q, c):', '    n = dict(q)']
        for r in self.regs:
            if (r, 'd') in self.eq: lines.append(f'    n[{r!r}] = {self._py(self.eq[(r, "d")])}')
            else: lines.append(f'    n[{r!r}] = q[{r!r}] ^ {self._py(self.eq[(r, "t")])}')
        lines.append('    return n')
        lines += ['', 'def aclr(p, q, c):', '    return {']
        lines += [f'        {r!r}: {self._py(self.eq[(r, "ar")])},' for r in self.regs if (r, 'ar') in self.eq]
        lines += ['    }', '', 'def oe(p, q, c):', '    return {']
        lines += [f'        {t!r}: {self._py(self.eq[(t, "oe")])},' for t, e in self.eq if e == 'oe']
        lines.append('    }')
        env = {}; exec('\n'.join(lines), env)
        self.comb_fn, self.next_fn, self.aclr_fn, self.oe_fn = env['comb'], env['nxt'], env['aclr'], env['oe']

    # ---- simulation -----------------------------------------------------------------------
    def reset_state(self):
        return {r: 0 for r in self.regs}

    def outputs(self, p, q):
        """Pin name -> 0/1, or None when the output is disabled; applies asynchronous clears to q."""
        c = self.comb_fn(p, q)
        for r, v in self.aclr_fn(p, q, c).items():
            if v: q[r] = 0
        c = self.comb_fn(p, q); en = self.oe_fn(p, q, c); out = {}
        for n in self.pins.values():
            if n in self.inputs: continue
            v = q[n] if n in self.regs else c[n]
            out[n] = v if en.get(n, 1) else None
        return out

    def clock_edge(self, p, q, rising):
        """State after rising edges on the input pins in `rising`; p = pin levels just before."""
        c = self.comb_fn(p, q); n = self.next_fn(p, q, c)
        n = {r: (n[r] if self.clocks[r] in rising else q[r]) for r in q}
        for r, v in self.aclr_fn(p, q, c).items():
            if v: n[r] = 0
        return n
