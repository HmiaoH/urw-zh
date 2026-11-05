#!/usr/bin/env python3
"""Compile reviewed complete paragraphs for existing paragraph hooks.
This makes entries eligible for matching, not proof of in-game coverage.
Encyclopedia remains staged until link layout is adapted.
"""
import json
from bind import ROOT
from coverage import read_rows
from check_drafts import check
from validate import validate,load

def compile_rows(rows):
    result=[]
    for row in rows:
        if row['status']!='reviewed':continue
        eligible=row['source'].startswith('gameinfo/') or row['source'].startswith('RNDCAMP.')
        if not eligible:continue
        result.append(dict(id='paragraph-'+row['id'],source=row['source'],source_id=row['id'],context='showtext' if row['context'].endswith(':title') else 'paragraph',original=row['original'].encode('cp437').decode('latin1'),translation=row['translation'],status='reviewed',runtime_verified=False,allow_break_variation=row['source'].startswith('RNDCAMP.') and row['context'].endswith(':body')))
        if row['source'].startswith('RNDCAMP.') and row['context'].endswith(':title'):
            result.append(dict(id='scenario-header-'+row['id'],source=row['source'],source_id=row['id'],context='showtext',original='Scenario: '+row['original'],translation='开局：'+row['translation'],status='reviewed',runtime_verified=False))
    return result
if __name__=='__main__':
    drafts=read_rows(ROOT/'data/drafts');errors=check(read_rows(ROOT/'data/catalog'),[r for r in drafts if r['status']=='reviewed'])
    if errors: raise SystemExit('\n'.join(errors))
    rows=compile_rows(drafts)
    existing=[r for r in load() if not r['id'].startswith(('paragraph-','scenario-header-'))]
    errors=validate(existing+rows)
    if errors:raise SystemExit('\n'.join(errors))
    (ROOT/'data/translations/resource_paragraphs.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(rows)} reviewed paragraph entries compiled; runtime coverage still requires observation')
