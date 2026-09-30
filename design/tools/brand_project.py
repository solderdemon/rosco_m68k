"""Final r2.42 step: rename and brand the KiCad project after board generation.

Run with KiCad's Python after polish_board.py. The rosco_m68k library names and
the upstream attribution remain intact. This step is safe to run again.
"""

from pathlib import Path
import re

import pcbnew as pcb
import wx

wx.Log.EnableLogging(False)


KICAD = Path(__file__).resolve().parent.parent / 'kicad'
OLD = 'rosco_m68k'
NEW = 'solderdemon_m68k'
TITLE = 'SolderDemon m68k Classic v2'
COMPANY = 'SolderDemon'
NOTICE = 'SolderDemon modification 2026-09-28; based on rosco_m68k'


def rename_project_file(ext):
    old = KICAD / f'{OLD}{ext}'
    new = KICAD / f'{NEW}{ext}'
    if old.exists() and new.exists():
        raise RuntimeError(f'both project files exist: {old} and {new}')
    if old.exists():
        old.rename(new)
    if not new.exists():
        raise FileNotFoundError(new)
    return new


def edit_schematic(path):
    source = path.read_text(encoding='utf-8')
    result = source.replace(f'(project "{OLD}"', f'(project "{NEW}"')
    result = result.replace('(title "ROSCO_M68K GENERAL PURPOSE MC68010 COMPUTER")',
                            f'(title "{TITLE}")')
    result = result.replace('(company "The Really Old-School Company Limited")',
                            f'(company "{COMPANY}")')
    result = re.sub(r'(\(date ")[^"]*("\))', r'\g<1>2026-09-28\2', result, count=1)
    if f'(comment 5 "{NOTICE}")' not in result:
        result, n = re.subn(r'(?m)^([ \t]*)\(comment 4 ("(?:[^"\\]|\\.)*")\)',
                            lambda m: m.group(0) + '\n' + m.group(1) +
                            f'(comment 5 "{NOTICE}")', result, count=1)
        if n != 1:
            raise RuntimeError(f'missing original copyright notice in {path}')
    if source != result:
        path.write_text(result, encoding='utf-8')


def edit_project(path):
    source = path.read_text(encoding='utf-8')
    result = source.replace(f'{OLD}.kicad_pro', f'{NEW}.kicad_pro')
    result = result.replace(f'{OLD}.kicad_sch', f'{NEW}.kicad_sch')
    result = result.replace(f'{OLD}.net', f'{NEW}.net')
    result = result.replace(f'"name": "{OLD}"', f'"name": "{NEW}"')
    if source != result:
        path.write_text(result, encoding='utf-8')


def edit_board(path):
    print(f'Loading {path.name}', flush=True)
    board = pcb.LoadBoard(str(path))
    print(f'Loaded {path.name}', flush=True)
    title = board.GetTitleBlock()
    changed = False
    for getter, setter, value in (
        (title.GetTitle, title.SetTitle, TITLE),
        (title.GetCompany, title.SetCompany, COMPANY),
        (title.GetDate, title.SetDate, '2026-09-28'),
    ):
        if getter() != value:
            setter(value)
            changed = True
    # pcbnew comment indices are zero-based: index 4 is KiCad's comment 5.
    if title.GetComment(4) != NOTICE:
        title.SetComment(4, NOTICE)
        changed = True
    if title.GetComment(5) == NOTICE:
        title.SetComment(5, '')
        changed = True
    silkscreen = [d for d in board.GetDrawings()
                 if isinstance(d, pcb.PCB_TEXT) and d.GetText() == 'rosco_m68k classic']
    if len(silkscreen) > 1:
        raise RuntimeError('multiple original product labels on board')
    for label in silkscreen:
        label.SetText('SolderDemon m68k')
        changed = True
    if changed:
        print(f'Saving {path.name}', flush=True)
        project = path.with_suffix('.kicad_pro')
        saved_project = project.read_bytes()
        pcb.SaveBoard(str(path), board)
        project.write_bytes(saved_project)  # SaveBoard can overwrite the project's DRC rules.


def main():
    # Rename only the KiCad project trio. rosco_m68k libraries are inherited
    # names used by symbols and footprints and must remain available.
    project = rename_project_file('.kicad_pro')
    schematic = rename_project_file('.kicad_sch')
    board = rename_project_file('.kicad_pcb')
    edit_project(project)
    for sheet in sorted(KICAD.glob('*.kicad_sch')):
        edit_schematic(sheet)
    edit_board(board)
    print(f'Branded {schematic.name}, {board.name}, and their project metadata')


if __name__ == '__main__':
    main()
