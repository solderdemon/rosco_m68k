"""Final r2.42 copper and silkscreen cleanup after routing."""
from pathlib import Path
import sys

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cpld_board as cb


def main():
    board = pcb.LoadBoard(str(cb.BOARD))
    widened = 0
    for track in board.GetTracks():
        if track.Type() == pcb.PCB_TRACE_T and track.GetNetname() == 'VCC' \
                and track.GetWidth() == pcb.FromMM(0.2):
            track.SetWidth(pcb.FromMM(0.3))
            widened += 1
    uart_pin_text = {'TxD', 'RxD\n', 'TX', 'RX', 'T', 'R'}
    removed = []
    for drawing in list(board.GetDrawings()):
        if isinstance(drawing, pcb.PCB_TEXT) and drawing.GetText() in uart_pin_text:
            p = drawing.GetPosition()
            if pcb.ToMM(p.x) > 225 and 100 < pcb.ToMM(p.y) < 106:
                removed.append(drawing.GetText())
                cb.remove(board, drawing)
    assert len(removed) == 2, removed
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    cb.save(board)
    print(f'Widened {widened} VCC segments; removed {len(removed)} crowded UART labels')


if __name__ == '__main__':
    main()
