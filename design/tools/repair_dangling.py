"""Remove DRC-reported loose copper so cpld_route.py can reconnect affected nets."""
from pathlib import Path
import sys

import pcbnew as pcb

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cpld_board as cb
from check_board import check


def main():
    report = check(cb.BOARD)
    uuids = {item['uuid'] for issue in report['violations']
             if issue['type'] in ('track_dangling', 'via_dangling')
             for item in issue['items']}
    board = pcb.LoadBoard(str(cb.BOARD))
    removed = []
    for track in list(board.GetTracks()):
        if track.m_Uuid.AsString() in uuids:
            removed.append(track.GetNetname())
            cb.remove(board, track)
    assert len(removed) == len(uuids), (removed, uuids)
    cb.save(board)
    print('Removed loose copper on:', ', '.join(removed))


if __name__ == '__main__':
    main()
