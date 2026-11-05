#!/usr/bin/env python3
"""Extract complete player-visible resource sections; retain routing metadata separately."""
import hashlib,json,re
from bind import ROOT,GAME

def sections(path,source):
    result=[]
    for block in path.read_bytes().decode('cp437').split('***'):
        lines=[s.strip() for s in block.splitlines() if s.strip() and not s.lstrip().startswith('//')]
        if not lines: continue
        header=lines.pop(0)
        if not header.startswith('.'):
            raise ValueError(f'{source}: unexpected section header {header!r}')
        metadata=[]
        for i,line in enumerate(lines):
            if line.startswith('%POP'):
                metadata=lines[i:];lines=lines[:i];break
        body=' '.join(lines)
        if not body: continue
        topic=header.strip('.')
        result.append(dict(id=hashlib.sha256((source+'\0'+topic+'\0'+body).encode()).hexdigest()[:20],source=source,context=f'resource:{source}:{topic}',original=body,translation='',status='pending',aliases=header,metadata=metadata,encoding='cp437',runtime_verified=False))
    return result

if __name__=='__main__':
    (ROOT/'research/batches').mkdir(parents=True,exist_ok=True)
    (ROOT/'data/catalog').mkdir(parents=True,exist_ok=True)
    resource=GAME/'Contents/Resources'
    rows=sections(resource/'GAME.NFO','GAME.NFO')+sections(resource/'gameinfo/urw_scrinfo.txt','gameinfo/urw_scrinfo.txt')
    out=ROOT/'data/catalog/sections.json';out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    batches=[[] for _ in range(3)]
    for row in sorted(rows,key=lambda r:len(r['original']),reverse=True):
        min(batches,key=lambda b:sum(len(r['original']) for r in b)).append(row)
    for i,batch in enumerate(batches,1):
        (ROOT/f'research/batches/sections-{i}.json').write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(rows)} complete sections; {sum(len(r["original"]) for r in rows)} source characters; batches {[len(b) for b in batches]}')
