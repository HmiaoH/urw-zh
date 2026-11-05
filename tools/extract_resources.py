#!/usr/bin/env python3
"""Extract scenarios and message syntax without modifying game data.
Message rows retain substitution/control syntax as pending source expressions;
these are not runtime-matchable sentences until a separate adapter is verified.
"""
import hashlib,json,re
from bind import ROOT,GAME

def row(source,context,original,**kwargs):
    return dict(id=hashlib.sha256((source+'\0'+context+'\0'+original).encode()).hexdigest()[:20],source=source,context=context,original=original,translation='',status='pending',runtime_verified=False,**kwargs)

def extract():
    root=GAME/'Contents/Resources';scenarios=[];messages=[]
    for p in sorted(root.glob('RNDCAMP.*')):
        lines=p.read_bytes().decode('cp437').splitlines()
        for context,text in [('title',lines[0]),('summary',lines[1]),('body',' '.join(s.strip() for s in lines[3:] if s.strip()))]:
            scenarios.append(row(p.name,f'scenario:{p.name}:{context}',text,image=lines[2],encoding='cp437'))
    for p in sorted((root/'messages').glob('*.txt')):
        if p.name=='guide_values.txt':continue
        section='';source=str(p.relative_to(root))
        for n,line in enumerate(p.read_bytes().decode('cp437').splitlines(),1):
            line=line.strip()
            if not line or line.startswith('//'):continue
            if line.startswith('.'):
                section=line;continue
            if not re.search('[A-Za-z]',line):continue
            messages.append(row(source,f'message-source:{section}:{n}',line,section=section,line=n,kind='exact',syntax='game-message-expression',encoding='cp437'))
    return scenarios,messages

if __name__=='__main__':
    scenarios,messages=extract()
    for name,rows in [('scenarios',scenarios),('messages',messages)]:
        (ROOT/f'data/catalog/{name}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
        print(name,len(rows),'records',sum(len(r['original']) for r in rows),'characters')
