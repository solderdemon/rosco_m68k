"""Just enough S-expression handling to edit KiCad files that were drawn by hand.

parse() turns text into nested lists of tokens: atoms stay exactly as written (a quoted string
keeps its quotes), so dump(parse(x)) reproduces x up to whitespace and KiCad reads it unchanged.
"""
import re

_TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def parse(text):
    stack, cur = [], []
    for m in _TOKEN.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append(cur)
            cur = []
        elif t == ')':
            done, cur = cur, stack.pop()
            cur.append(done)
        else:
            cur.append(t)
    assert not stack
    return cur[0]


def dump(x, indent=0):
    if not isinstance(x, list):
        return x
    if all(not isinstance(y, list) for y in x):
        return '(' + ' '.join(x) + ')'
    pad = '\t' * (indent + 1)
    head = [y for y in x if not isinstance(y, list)]
    out = '(' + ' '.join(head)
    for y in x:
        if isinstance(y, list):
            out += '\n' + pad + dump(y, indent + 1)
    return out + '\n' + '\t' * indent + ')'


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def unq(s):
    return s[1:-1].replace('\\"', '"').replace('\\\\', '\\') if s.startswith('"') else s


def find(x, key):
    """First child list whose head is `key`."""
    for y in x:
        if isinstance(y, list) and y and y[0] == key:
            return y
    return None


def findall(x, key):
    return [y for y in x if isinstance(y, list) and y and y[0] == key]


def prop(sym, name):
    for p in findall(sym, 'property'):
        if unq(p[1]) == name:
            return unq(p[2])
    return None
