#!/usr/bin/env python3
"""Extract display labels from recipe and flora resources, keeping references untouched."""
import json,re
from bind import ROOT,GAME
from extract_resources import row

def extract():
    root=GAME/'Contents/Resources';rows=[]
    for p in sorted([*root.glob('*_glossary.txt'),*root.glob('flora_*.txt'),root/'ini_skills.txt']):
        source=p.name;section='';seen=set()
        for n,line in enumerate(p.read_bytes().decode('cp437').splitlines(),1):
            if line.lstrip().startswith('//'):continue
            found=[]
            header=re.match(r'^\.([^\.]+)\.',line)
            if header:
                section=header[1];found.append(('name',section))
            found.extend(('name',s) for s in re.findall(r'\[NAME:([^\]]+)\]',line))
            # Braced ingredients and quoted explanations are displayed in crafting UI.
            found.extend(('ingredient',s) for s in re.findall(r'\{([^}]+)\}',line))
            found.extend(('explanation',s.lstrip('+')) for s in re.findall(r"'([^']+)'",line))
            for kind,text in found:
                if (kind,text) in seen:continue
                seen.add((kind,text))
                rows.append(row(source,f'resource-label:{source}:{kind}:{text}',text,line=n,section=section,display_role=kind,encoding='cp437'))
    return rows
if __name__=='__main__':
    rows=extract();(ROOT/'data/catalog/labels.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    print(len(rows),'resource display labels; source identifiers are never modified')
