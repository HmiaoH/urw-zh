#!/usr/bin/env python3
"""Compile reviewed Luna fragment batches; source/links/control codes must remain valid.

Review the bilingual drafts before running. This command does not translate text.
Native resource metadata is excluded from both publication and coverage counts.
"""
import json,re,hashlib
from pathlib import Path
from bind import ROOT,GAME
from validate import normalize,validate,load
from validate_hypertext import validate_hypertext
OUTPUT=ROOT/'data/translations/encyclopedia_complete.json'

def content_lines():
    lines=(GAME/'Contents/Resources/GAME.NFO').read_bytes().decode('cp437').splitlines()
    result={};topic=None;skip_next=False
    for number,line in enumerate(lines,1):
        if skip_next:skip_next=False;continue
        if line.startswith('%'):skip_next=True;continue
        if line.startswith('.') and line.endswith('.'):
            topic=line;continue
        if line.startswith('***'):topic=None;continue
        if not topic or not line.strip() or line.startswith('//'):continue
        result[number]=(topic,line)
    return result

def compile_review():
    native=content_lines()
    existing=[r for p in sorted((ROOT/'data/translations').glob('*.json')) if p!=OUTPUT for r in json.loads(p.read_text())]
    keys={(r['context'],normalize(r['original'])):r for r in existing}
    out=[];titles={};stats={'metadata_excluded':0,'source_fragments':0,'published_fragments':0}
    for path in sorted((ROOT/'data/drafts').glob('encyclopedia_luna_*.json')):
        for row in json.loads(path.read_text()):
            line=row['evidence']['line'];entry=native.get(line)
            if not entry:
                stats['metadata_excluded']+=1;continue
            topic,text=entry;chunk=row['evidence']['chunk'];original=text[(chunk-1)*149:chunk*149].strip()
            if original!=row['original'] or topic!=row['evidence']['topic']:
                raise ValueError(f"Source mismatch {row['id']}")
            if row.get('title_translation'):
                titles.setdefault(topic,(row['title_translation'],row.get('summary_translation','')))
            if not row.get('translation'):raise ValueError(f"Empty draft {row['id']}")
            stats['source_fragments']+=1
            key=('encyclopedia',normalize(original))
            if key in keys:continue
            copy={k:v for k,v in row.items() if k not in ('title_translation','summary_translation')}
            copy['status']='reviewed';copy['runtime_verified']=False
            errors=validate([copy])+validate_hypertext([copy])
            if errors:raise ValueError('\n'.join(errors))
            keys[key]=copy;out.append(copy);stats['published_fragments']+=1
    extra=ROOT/'data/rules/encyclopedia_titles.json'
    for row in json.loads(extra.read_text()):titles[row['topic']]=(row['title'],row['summary'])
    for topic in {t for t,_ in native.values()}:
        if topic in titles:continue
        aliases=topic.strip('.').split('.')
        title=next((keys[('encyclopedia-title',a)]['translation'] for a in aliases if ('encyclopedia-title',a) in keys),'')
        summary=next((keys[('encyclopedia-summary',a)]['translation'] for a in aliases if ('encyclopedia-summary',a) in keys),'')
        if title:titles[topic]=(title,summary)
    for topic,(title,summary) in sorted(titles.items()):
        for alias in topic.strip('.').split('.'):
            for context,translation in [('encyclopedia-title',title),('encyclopedia-summary',summary),('showtext',title)]:
                if not translation:continue
                # Do not replace established context-sensitive translations.
                originals=[alias]
                if context=='showtext':
                    legacy=alias.encode('cp437').decode('latin1')
                    if legacy!=alias:originals.append(legacy)
                for original in originals:
                    key=(context,normalize(original))
                    if key in keys:continue
                    r=dict(id=hashlib.sha256((context+'\t'+original).encode()).hexdigest()[:20],source='GAME.NFO',context=context,original=original,translation=translation,status='reviewed',runtime_verified=False,evidence={'topic':topic})
                    keys[key]=r;out.append(r)
    errors=validate(existing+out)+validate_hypertext(out)
    if errors:raise ValueError('\n'.join(errors))
    OUTPUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    stats['published_rows']=len(out);stats['new_topic_titles']=len(titles)
    print(json.dumps(stats,ensure_ascii=False))
    return out

if __name__=='__main__':compile_review()
