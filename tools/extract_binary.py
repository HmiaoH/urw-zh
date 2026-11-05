#!/usr/bin/env python3
"""Keep all binary candidates, including internal strings, out of coverage denominator."""
import json
from bind import ROOT
from extract import extract
if __name__=='__main__':
    (ROOT/'research/batches').mkdir(parents=True,exist_ok=True)
    (ROOT/'data/catalog').mkdir(parents=True,exist_ok=True)
    rows=[dict(r,scope='unclassified-binary',runtime_verified=False) for r in extract() if r['context']=='binary']
    (ROOT/'data/catalog/binary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    # Text with spaces includes messages, dialogue, labels and debugging output.
    # This is a review queue, NOT a determination of player-visible scope.
    prose=[r for r in rows if ' ' in r['original'] and len(r['original'])>12]
    batches=[[] for _ in range(3)]
    for r in prose:min(batches,key=lambda b:sum(len(x['original']) for x in b)).append(r)
    for i,b in enumerate(batches,1):
        (ROOT/f'research/batches/binary-{i}.json').write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
    print(len(rows),'unclassified candidates;',[(len(b),sum(len(r['original']) for r in b)) for b in batches],'review batches')
