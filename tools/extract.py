#!/usr/bin/env python3
import hashlib,json,re
from pathlib import Path
from bind import inspect,GAME,ROOT

def entry(text,source,context,**more):
 return dict(id=hashlib.sha256((source+'\0'+context+'\0'+text).encode()).hexdigest()[:20],source=source,context=context,original=text,translation='',status='pending',**more)
def extract():
 b,_,sections,_=inspect(GAME/'Contents/Resources/urw3-bin');a,n,p=sections['__cstring'];records=[]
 offset=0
 for raw in b[p:p+n].split(b'\0'):
  txt=raw.decode('cp437');address=a+offset;offset+=len(raw)+1
  if len(txt)>=2 and re.search(r'[A-Za-z]{2}',txt):
   records.append(entry(txt,'urw3-bin:__cstring','binary',address=hex(address)))
 r=GAME/'Contents/Resources'
 for path in sorted([*r.glob('messages/*.txt'),*r.glob('gameinfo/*.txt'),r/'GAME.NFO',*r.glob('RNDCAMP.*')]):
  ctx='';lines=path.read_bytes().decode('cp437').splitlines()
  for i,line in enumerate(lines,1):
   if line.startswith('.') and '.' in line[1:]:ctx=line.split('.')[1]
   if not line.strip() or line.lstrip().startswith('//') or line.startswith('.') or line.strip()=='***':continue
   if re.search(r'[A-Za-z]{3}',line):records.append(entry(line,str(path.relative_to(r)),ctx,line=i))
 return records
if __name__=='__main__':
 records=extract();(ROOT/'research').mkdir(exist_ok=True);(ROOT/'research/catalog.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('extracted',len(records),'candidate records; binary includes non-display strings requiring review')
