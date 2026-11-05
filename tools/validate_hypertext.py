"""Keep rendered labels separate from immutable encyclopedia targets."""
import re
import json
from pathlib import Path
LINK = re.compile(r'\[\[([A-ZÄÖÅ0-9 / .\'-]+)\|([^\[\]\n]+)\]\]')
def validate_hypertext(rows):
    manifest=Path(__file__).resolve().parents[1]/'data/rules/encyclopedia_topics.json'
    known=set(json.loads(manifest.read_text())['topics'])
    errors=[]
    for row in rows:
        if row.get('context')!='encyclopedia': continue
        text=row.get('translation','')
        targets=[m[0] for m in LINK.findall(text)]
        remainder=LINK.sub('',text)
        if '[[' in remainder or ']]' in remainder or targets!=row.get('link_targets',[]):
            errors.append(f"{row['id']}: malformed or changed encyclopedia targets")
        if any(len(t.encode('cp437'))>=200 for t in targets):
            errors.append(f"{row['id']}: oversized encyclopedia target")
        if any(t not in known for t in targets):
            errors.append(f"{row['id']}: unknown encyclopedia target")
    return errors
