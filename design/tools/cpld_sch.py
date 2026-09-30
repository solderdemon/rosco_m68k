"""Write the CPLDs sheet of rosco_m68k classic THT r2.14 (it replaces the GALs sheet of r2.13).

The pinout of both ATF1502AS comes from the PIN lines of code/pld/cpld/*.pld -- nothing here
repeats it. Every signal pin carries a global label named after its net, right on the pin end,
so the sheet needs no wires. The parts that already existed on the GALs sheet (the pull-ups R8
and R21, the jumper JP4, the decoupling capacitors, and IC2/IC3 themselves) keep their UUIDs, so
the board's footprints stay linked to them; IC5 and IC6 are gone.

KiCad ships the ATF1502AS only as TQFP-44. The PLCC-44 symbol made here is that symbol with its
pins renumbered: on the 44-pin Atmel/Altera parts PLCC pin = TQFP pin + 6 (mod 44), which the
datasheet's pin table confirms for every fixed pin (VCC 3/15/23/35, GND 10/22/30/42, TDI 7,
TMS 13, TCK 32, TDO 38, GCLK1 43, OE1 44, GCLR 1, OE2/GCLK2 2). It is also written into the
project library rosco_m68k.kicad_sym, which this script creates and adds to sym-lib-table.

    python design/tools/cpld_sch.py
"""
from pathlib import Path
import re, sys, uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sexp
from sexp import q

KICAD = HERE.parent / 'kicad'
PLD = HERE.parent.parent / 'code' / 'pld' / 'cpld'
SYMDIR = Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
OLD = KICAD / 'GALs.kicad_sch'
NEW = KICAD / 'CPLDs.kicad_sch'
ROOT = KICAD / 'solderdemon_m68k.kicad_sch'
PROJECT_LIB = KICAD / 'rosco_m68k.kicad_sym'
LIB_TABLE = KICAD / 'sym-lib-table'

ROOT_UUID = '9031bb33-c6aa-4758-bf5c-3274ed3ebab7'
SHEET_UUID = '00000000-0000-0000-0000-0000617d19f3'
SHEET_FILE_UUID = '5290e0d7-1f24-4c0b-91ff-28c5a304ab9a'
NS = uuid.UUID('3b0c6a8e-5f0e-4d8e-9a57-1f0a1b2c4d14')      # for the new UUIDs, so reruns match

CPLD_LIB = 'rosco_m68k:ATF1502AS-xJx44'
PLCC = 'Package_LCC:PLCC-44_THT-Socket'
VCC_PINS, GND_PINS = (3, 15, 23, 35), (10, 22, 30, 42)
JTAG_PINS = {7: 'JTAG_TDI', 13: 'JTAG_TMS', 32: 'JTAG_TCK', 38: 'JTAG_TDO'}
# TDI of the header goes to IC2, IC2's TDO to IC3's TDI, IC3's TDO back to the header
JTAG_CHAIN = {'IC2': {38: 'JTAG_CHAIN'}, 'IC3': {7: 'JTAG_CHAIN'}}
CHIPS = {  # ref: (CUPL source, uuid kept from r2.13, position)
    'IC2': ('ic2_decoder.pld', '00000000-0000-0000-0000-00006161cada', (76.2, 99.06)),
    'IC3': ('ic3_glue.pld', '00000000-0000-0000-0000-0000616af603', (165.1, 99.06)),
}
# label shapes; every other signal pin is an input
OUTPUT = {'IC2': {'EVENRAMSEL', 'ODDRAMSEL', 'EVENROMSEL', 'ODDROMSEL', 'IOSEL', 'EXPSEL', 'WR'},
          'IC3': {'DUASEL', 'DUAIACK', 'RUNLED'}}
OPEN_DRAIN = {'IC2': {'DTACK'}, 'IC3': {'RESET', 'HALT', 'BERR'}}
# JTAG header, Altera/Atmel 10-pin layout (ATDH1150USB, USB-Blaster)
JTAG_HEADER = {1: 'JTAG_TCK', 2: 'GND', 3: 'JTAG_TDO', 4: 'VCC', 5: 'JTAG_TMS', 6: None, 7: None,
               8: None, 9: 'JTAG_TDI', 10: 'GND'}
# decoupling: r2.13 capacitors keep their UUID; C33 is new. On the board the GAL decoupling
# C23-C25 (on other sheets) now sits by the CPLDs and C33 is IC2's second. (ref, uuid or None)
CAPS = [('C9', '00000000-0000-0000-0000-00006161cac0'), ('C10', '00000000-0000-0000-0000-000061687a3b'),
        ('C12', '00000000-0000-0000-0000-0000616269b3'), ('C31', '00000000-0000-0000-0000-0000616ba5ed'),
        ('C32', '00000000-0000-0000-0000-0000616be28d'), ('C33', None)]
CAP_FP = 'rosco_m68k:C2.5-3'
R_FP = 'rosco_m68k:0207_10'
R8 = '00000000-0000-0000-0000-000061653f75'
R21 = '00000000-0000-0000-0000-000061654750'
JP4 = '00000000-0000-0000-0000-0000617668ac'


def uid(*key):
    return str(uuid.uuid5(NS, '/'.join(key)))


def cupl_pins(name):
    text = re.sub(r'/\*.*?\*/', ' ', (PLD / name).read_text(), flags=re.S)
    return {int(n): s for n, s in re.findall(r'^\s*PIN\s+(\d+)\s*=\s*(\w+)\s*;', text, flags=re.M)}


# ---- library symbols -------------------------------------------------------------------------
def lib_symbol(libfile, name):
    t = sexp.parse((SYMDIR / libfile).read_text(encoding='utf-8'))
    for s in sexp.findall(t, 'symbol'):
        if sexp.unq(s[1]) == name:
            assert not sexp.find(s, 'extends'), f'{name} extends another symbol'
            return s
    raise KeyError(name)


def rename(sym, old, new):
    """Rename a symbol and its unit sub-symbols (NAME_u_s)."""
    sym[1] = q(new)
    for s in sexp.findall(sym, 'symbol'):
        s[1] = q(sexp.unq(s[1]).replace(old, new.split(':')[-1], 1))
    return sym


def set_prop(sym, name, value):
    for p in sexp.findall(sym, 'property'):
        if sexp.unq(p[1]) == name:
            p[2] = q(value)
            return
    raise KeyError(name)


def plcc_symbol():
    s = lib_symbol('CPLD_Microchip.kicad_sym', 'ATF1502AS-xAx44')
    rename(s, 'ATF1502AS-xAx44', 'ATF1502AS-xJx44')
    set_prop(s, 'Value', 'ATF1502AS-xJx44')
    set_prop(s, 'Footprint', PLCC)
    set_prop(s, 'Description', 'Microchip CPLD, 32 Macrocell, 5 V, PLCC-44 (in a through-hole socket)')
    set_prop(s, 'ki_fp_filters', 'PLCC*44*')

    def walk(x):
        for y in x:
            if isinstance(y, list):
                if y[0] == 'pin':
                    num = sexp.find(y, 'number')
                    num[1] = q(str((int(sexp.unq(num[1])) + 6 - 1) % 44 + 1))
                else:
                    walk(y)
    walk(s)
    return s


def pins_of(sym):
    """{number: (x, y, angle)} in symbol coordinates (y up)."""
    out = {}

    def walk(x):
        for y in x:
            if isinstance(y, list):
                if y[0] == 'pin':
                    at = sexp.find(y, 'at')
                    out[sexp.unq(sexp.find(y, 'number')[1])] = (float(at[1]), float(at[2]), int(float(at[3])))
                else:
                    walk(y)
    walk(sym)
    return out


def update_project_lib(sym):
    """Put the symbol into the project library (created if need be) and the library into
    sym-lib-table, leaving the rest of both files byte for byte."""
    ref = sexp.parse((SYMDIR / 'CPLD_Microchip.kicad_sym').read_text(encoding='utf-8'))
    version = sexp.find(ref, 'version')[1]
    if not PROJECT_LIB.exists():
        PROJECT_LIB.write_text(f'(kicad_symbol_lib\n  (version {version})\n  (generator "cpld_sch.py")\n)\n',
                               encoding='utf-8')
    table = LIB_TABLE.read_text(encoding='utf-8')
    if '(name rosco_m68k)' not in table:
        entry = '  (lib (name rosco_m68k)(type KiCad)(uri ${KIPRJMOD}/rosco_m68k.kicad_sym)(options "")(descr ""))\n'
        LIB_TABLE.write_text(table[:table.rstrip().rindex(')')] + entry + ')\n', encoding='utf-8')
    text = PROJECT_LIB.read_text(encoding='utf-8')
    start = text.find('(symbol "ATF1502AS-xJx44"')
    if start >= 0:                                     # drop an earlier copy of ours
        depth, i = 0, start
        for i in range(start, len(text)):
            depth += {'(': 1, ')': -1}.get(text[i], 0)
            if depth == 0:
                break
        text = text[:start].rstrip() + '\n' + text[i + 1:].lstrip('\n')
    end = text.rstrip().rindex(')')
    body = '\n'.join('  ' + line for line in sexp.dump(sym).split('\n'))
    text = text[:end].rstrip() + '\n' + body + '\n)\n'
    # the symbol comes from a KiCad 10 library, so the file takes that library's format version
    text = re.sub(r'\(version \d+\)', f'(version {version})', text, count=1)
    PROJECT_LIB.write_text(text, encoding='utf-8')


# ---- sheet items -----------------------------------------------------------------------------
def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def effects(hide=False, justify=None):
    e = ['effects', ['font', ['size', '1.27', '1.27']]]
    if justify:
        e.append(['justify', justify])
    if hide:
        e.append(['hide', 'yes'])
    return e


def symbol(lib_id, ref, value, footprint, at, u, pins, rot=0, ref_at=None, val_at=None, hide_ref=False):
    x, y = at
    s = ['symbol', ['lib_id', q(lib_id)], ['at', fmt(x), fmt(y), str(rot)], ['unit', '1'],
         ['exclude_from_sim', 'no'], ['in_bom', 'no' if ref.startswith('#') else 'yes'],
         ['on_board', 'no' if ref.startswith('#') else 'yes'], ['dnp', 'no'], ['uuid', q(u)]]
    rx, ry = ref_at or (x, y - 3)
    vx, vy = val_at or (x, y + 3)
    s.append(['property', q('Reference'), q(ref), ['at', fmt(rx), fmt(ry), '0'], effects(hide=hide_ref)])
    s.append(['property', q('Value'), q(value), ['at', fmt(vx), fmt(vy), '0'], effects()])
    s.append(['property', q('Footprint'), q(footprint), ['at', fmt(x), fmt(y), '0'], effects(hide=True)])
    s.append(['property', q('Datasheet'), q(''), ['at', fmt(x), fmt(y), '0'], effects(hide=True)])
    s.append(['property', q('Description'), q(''), ['at', fmt(x), fmt(y), '0'], effects(hide=True)])
    for n in pins:
        s.append(['pin', q(n), ['uuid', q(uid(u, 'pin', n))]])
    s.append(['instances', ['project', q('solderdemon_m68k'),
                            ['path', q(f'/{ROOT_UUID}/{SHEET_UUID}'), ['reference', q(ref)], ['unit', '1']]]])
    return s


def label(net, at, angle, shape):
    x, y = at
    just = {0: 'left', 90: 'left', 180: 'right', 270: 'right'}[angle]
    return ['global_label', q(net), ['shape', shape], ['at', fmt(x), fmt(y), str(angle)],
            ['fields_autoplaced', 'yes'], effects(justify=just), ['uuid', q(uid('label', net, fmt(x), fmt(y)))],
            ['property', q('Intersheetrefs'), q('${INTERSHEET_REFS}'), ['at', '0', '0', '0'], effects(hide=True)]]


def no_connect(at):
    return ['no_connect', ['at', fmt(at[0]), fmt(at[1])], ['uuid', q(uid('nc', fmt(at[0]), fmt(at[1])))]]


def text(s, at, size=1.27):
    return ['text', q(s), ['exclude_from_sim', 'no'], ['at', fmt(at[0]), fmt(at[1]), '0'],
            ['effects', ['font', ['size', str(size), str(size)]], ['justify', 'left', 'bottom']],
            ['uuid', q(uid('text', s))]]


class Sheet:
    def __init__(self, libs):
        self.libs = libs                 # lib_id -> symbol definition
        self.items = []
        self.pwr = 900

    def pin_point(self, lib_id, at, num):
        x, y, a = pins_of(self.libs[lib_id])[num]
        return (at[0] + x, at[1] - y), a

    def power(self, net, point):
        self.pwr += 1
        lib = 'power:' + net
        self.items.append(symbol(lib, f'#PWR0{self.pwr}', net, '', point, uid('pwr', net, fmt(point[0]), fmt(point[1])),
                                 ['1'], hide_ref=True,
                                 val_at=(point[0], point[1] - 3.8 if net == 'VCC' else point[1] + 3.8)))

    def part(self, lib_id, ref, value, footprint, at, u, nets, shapes=None):
        """Place a symbol and hang a label, a power symbol or a no-connect on every pin."""
        pins = pins_of(self.libs[lib_id])
        self.items.append(symbol(lib_id, ref, value, footprint, at, u, sorted(pins, key=int)))
        done = set()
        for num in sorted(pins, key=int):
            pt, a = self.pin_point(lib_id, at, num)
            key = (fmt(pt[0]), fmt(pt[1]))
            net = nets.get(num)
            if key in done:                      # stacked power pins share one point
                continue
            done.add(key)
            if net in ('VCC', 'GND'):
                self.power(net, pt)
            elif net is None:
                self.items.append(no_connect(pt))
            else:
                shape = (shapes or {}).get(net, 'passive')
                self.items.append(label(net, pt, (a + 180) % 360, shape))


def main():
    old = sexp.parse(OLD.read_text(encoding='utf-8')) if OLD.exists() else sexp.parse(NEW.read_text(encoding='utf-8'))
    libs = {sexp.unq(s[1]): s for s in sexp.find(old, 'lib_symbols')[1:]}
    keep = ['Device:R', 'Jumper:Jumper_2_Open', 'power:GND', 'power:VCC', 'rosco_m68k-eagle-import:C2,5-3']
    libs = {k: libs[k] for k in keep}
    plcc = plcc_symbol()
    update_project_lib(plcc)
    libs[CPLD_LIB] = rename(sexp.parse(sexp.dump(plcc)), 'ATF1502AS-xJx44', CPLD_LIB)
    conn = lib_symbol('Connector_Generic.kicad_sym', 'Conn_02x05_Odd_Even')
    libs['Connector_Generic:Conn_02x05_Odd_Even'] = rename(conn, 'Conn_02x05_Odd_Even',
                                                           'Connector_Generic:Conn_02x05_Odd_Even')

    sh = Sheet(libs)
    for ref, (pld, u, at) in CHIPS.items():
        pins = cupl_pins(pld)
        nets = {str(n): s for n, s in pins.items()}
        for n in VCC_PINS:
            nets[str(n)] = 'VCC'
        for n in GND_PINS:
            nets[str(n)] = 'GND'
        for n, s in JTAG_PINS.items():
            nets[str(n)] = JTAG_CHAIN[ref].get(n, s)
        shapes = {s: ('output' if s in OUTPUT[ref] else 'bidirectional' if s in OPEN_DRAIN[ref] else 'input')
                  for s in pins.values()}
        shapes.update({s: 'bidirectional' for s in ('JTAG_TDI', 'JTAG_TMS', 'JTAG_TCK', 'JTAG_TDO', 'JTAG_CHAIN')})
        sh.part(CPLD_LIB, ref, 'ATF1502AS-10JU44', PLCC, at, u, nets, shapes)
        sh.items.append(text(f'{ref}: code/pld/cpld/{pld}', (at[0] - 15.24, at[1] + 38.1)))

    sh.part('Connector_Generic:Conn_02x05_Odd_Even', 'J9', 'JTAG',
            'Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical', (243.84, 60.96), uid('J9'),
            {str(k): v for k, v in JTAG_HEADER.items()})
    sh.items.append(text('JTAG: TDI -> IC2 -> IC3 -> TDO (ATDH1150USB / USB-Blaster pinout)', (218.44, 45.72)))

    for i, (ref, u) in enumerate(CAPS):
        at = (30.48 + 15.24 * i, 162.56)
        sh.part('rosco_m68k-eagle-import:C2,5-3', ref, '100nF', CAP_FP, at,
                u or uid(ref), {'1': 'VCC', '2': 'GND'})
    sh.items.append(text('C23/C24 (IC3) and C25/C33 (IC2) sit by the CPLDs; the others decouple the rest of the board',
                         (30.48, 180.34)))

    sh.part('Device:R', 'R8', '4K7', R_FP, (220.98, 111.76), R8, {'1': 'VCC', '2': 'LGEXP'})
    sh.part('Device:R', 'R21', '1K2', R_FP, (243.84, 111.76), R21, {'1': 'VCC', '2': 'DTACK'})
    sh.part('Jumper:Jumper_2_Open', 'JP4', 'Jumper', 'rosco_m68k:1X02', (231.14, 132.08), JP4, {'1': 'LGEXP', '2': 'GND'})
    sh.items.append(text('JP4 fitted: the expansion bus answers /DTACK itself', (215.9, 139.7)))

    title = ['title_block', ['title', q('SolderDemon m68k Classic v2')], ['date', q('2026-09-28')],
             ['rev', q('2.42')], ['company', q('SolderDemon')],
             ['comment', '1', q('OSHWA UK000006 (https://certification.oshwa.org/uk000006.html)')],
             ['comment', '2', q('See https://github.com/roscopeco/rosco_m68k/blob/master/LICENCE.hardware.txt')],
             ['comment', '3', q('Open Source Hardware licenced under CERN Open Hardware Licence')],
             ['comment', '4', q('Copyright 2019-2026 Ross Bamford and Contributors')],
             ['comment', '5', q('SolderDemon modification 2026-09-28; based on rosco_m68k')]]
    doc = ['kicad_sch', ['version', '20231120'], ['generator', q('eeschema')], ['generator_version', q('8.0')],
           ['uuid', q(SHEET_FILE_UUID)], ['paper', q('A4')], title,
           ['lib_symbols'] + [libs[k] for k in sorted(libs)]] + sh.items
    NEW.write_text(sexp.dump(doc) + '\n', encoding='utf-8')
    if OLD.exists():
        OLD.unlink()

    # the root sheet: the sheet is called CPLDs now and lives in CPLDs.kicad_sch
    r = ROOT.read_text(encoding='utf-8')
    r = r.replace('(property "Sheetname" "GALs"', '(property "Sheetname" "CPLDs"')
    r = r.replace('(property "Sheetfile" "GALs.kicad_sch"', '(property "Sheetfile" "CPLDs.kicad_sch"')
    ROOT.write_text(r, encoding='utf-8')
    print('wrote', NEW.name, len(sh.items), 'items')


if __name__ == '__main__':
    main()
