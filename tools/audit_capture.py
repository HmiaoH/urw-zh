#!/usr/bin/env python3
"""Find proposed binary exclusions that have actually reached drawing hooks.
A capture proves a draw-call input, not that pixels were successfully rendered.
"""
import argparse,json
from pathlib import Path
from bind import ROOT
from coverage import read_rows
from validate import normalize
DRAW_CONTEXTS={'showtext','renshow','textput','rentext','newtext','newshow','paragraph','message'}
def audit(rows,captures):
    seen={normalize(r['original']) for r in captures if r['context'] in DRAW_CONTEXTS}
    conflicts=[]
    for row in rows:
        if not row.get('exclusion_reason'):continue
        original=row['original']
        keys={normalize(original)}
        try:keys.add(normalize(original.encode('cp437').decode('latin1')))
        except UnicodeError:pass
        if keys & seen:conflicts.append(row)
    return conflicts
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--log',type=Path,default=ROOT/'build/urw-zh/logs/captured.jsonl');args=parser.parse_args()
    captures=[json.loads(s) for s in args.log.read_text().splitlines()]
    rows=audit(read_rows(ROOT/'data/drafts'),captures)
    for r in rows:print(r['id'],repr(r['original']),r['exclusion_reason'])
    print(f'{len(rows)} proposed exclusions also observed at draw hooks; require review')
    raise SystemExit(bool(rows))
