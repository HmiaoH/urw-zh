#!/usr/bin/env python3
"""Expand reviewed finite native branches; leave names/numbers as runtime slots."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PARAM=re.compile(r'\{([a-z_]+):([a-z_]+)\}')
def compile_rules(rules):
    if rules.get('status')!='reviewed' or rules.get('development_only',True):
        raise ValueError('Only reviewed rule families may be activated')
    rows=[]
    def expand(source,target,evidence):
        for match in PARAM.finditer(source):
            name,kind=match.groups()
            if kind in ('text','int','uint'):continue
            if kind not in rules['maps']:raise ValueError('Unknown bounded slot '+kind)
            for value in rules['maps'][kind]:
                if not value.get('target'):continue
                expand(source.replace(match.group(),value['source']),target.replace('{'+name+'}',value['target']),evidence)
            return
        source=source.replace(':uint}',':int}')
        rows.append(dict(id=hashlib.sha256(('native-navigation\t'+source).encode()).hexdigest()[:20],source='rules/navigation.json',context='npc-talk',original=source,translation=target,kind='template' if PARAM.search(source) else 'exact',status='reviewed',runtime_verified=False,evidence=evidence))
    for row in rules['templates']:expand(row['source'],row['target'],row['source_instructions'])
    if len({r['original'] for r in rows})!=len(rows):raise ValueError('Conflicting generated sources')
    return rows
if __name__=='__main__':
    rules=json.loads((ROOT/'data/rules/navigation.json').read_text())
    rows=compile_rules(rules)
    (ROOT/'data/translations/generated_navigation.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(rows)} navigation entries from {len(rules["templates"])} native templates')
