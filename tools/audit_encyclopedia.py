#!/usr/bin/env python3
"""Measure matching coverage of actual native GAME.NFO draw fragments."""
import json
from compile_encyclopedia_review import content_lines
from validate import normalize,load
from bind import ROOT

def audit():
    keys={(r['context'],normalize(r['original'])):r for r in load() if r['status']=='reviewed'}
    pages={};missing=[];fragments=[]
    for line,(topic,text) in content_lines().items():
        page=pages.setdefault(topic,{'total':0,'translated':0})
        for start in range(0,len(text),149):
            original=text[start:start+149].strip()
            if not original or normalize(original) in ('<br>','http://www.unrealworld.fi/wiki','http://www.unrealworld.fi/wiki<br>'):continue
            page['total']+=1
            row=keys.get(('encyclopedia',normalize(original)))
            fragments.append({'topic':topic,'line':line,'original':original,'translated':bool(row)})
            if row:page['translated']+=1
            else:missing.append(fragments[-1])
    return {'pages':pages,'fragments':fragments,'missing':missing,'totals':{'pages':len(pages),'complete_pages':sum(p['total']==p['translated'] for p in pages.values()),'fragments':len(fragments),'translated':sum(p['translated'] for p in pages.values())}}

if __name__=='__main__':
    result=audit();(ROOT/'data/rules/encyclopedia_coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result['totals']));print(json.dumps(result['missing'][:8],ensure_ascii=False))
