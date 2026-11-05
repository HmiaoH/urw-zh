#!/usr/bin/env python3
"""Check drafts against immutable catalog; never promote review status automatically."""
import argparse,collections,json,re
from bind import ROOT
from coverage import read_rows
from validate import validate

TOKENS=re.compile(r'</?[^<>]+>|\[[^\[\]:]+:|https?://[^\s<>]+|(?<![A-Za-z0-9])\d+(?:[.,]\d+)*(?![A-Za-z0-9])')
def check(catalog,drafts):
    errors=validate(drafts);sources={r['id']:r for r in catalog}
    for row in drafts:
        label=row.get('id');source=sources.get(label)
        if source is None:
            errors.append(f'{label}: absent from source catalog');continue
        for key,value in source.items():
            if key not in ('translation','status') and row.get(key)!=value:
                errors.append(f'{label}: source field modified: {key}')
        if not row.get('translation'): continue
        # Message selectors and tag expressions are routing/substitution syntax.
        before=collections.Counter(TOKENS.findall(source['original']))
        after=collections.Counter(TOKENS.findall(row['translation']))
        if before!=after: errors.append(f'{label}: protected tokens changed: missing={dict(before-after)}, added={dict(after-before)}')
        if row.get('syntax')=='game-message-expression':
            for char in '[]':
                if source['original'].count(char)!=row['translation'].count(char):
                    errors.append(f'{label}: message bracket changed: {char}')
            control=re.match(r'^(?::[()|]|[!&@#_=+:]+)',source['original'])
            if control and not row['translation'].startswith(control[0]):
                errors.append(f'{label}: leading message control changed')
    return errors
def check_complete(catalog,drafts):
    indexed={r['id']:r for r in drafts};errors=[]
    for source in catalog:
        row=indexed.get(source['id'])
        if row is None or not (row.get('translation') or row.get('exclusion_reason')):
            errors.append(f"{source['id']}: no translation or classification")
        elif row.get('exclusion_reason'):
            if row.get('translation') or source.get('scope')!='unclassified-binary':
                errors.append(f"{source['id']}: invalid exclusion of translated/resource text")
    return errors

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--require-complete',action='store_true');args=parser.parse_args()
    drafts=read_rows(ROOT/'data/drafts');errors=check(read_rows(ROOT/'data/catalog'),drafts)
    if args.require_complete: errors+=check_complete(read_rows(ROOT/'data/catalog'),drafts)
    for error in errors: print(error)
    print(f'{sum(bool(r.get("translation")) for r in drafts)}/{len(drafts)} draft records translated; {len(errors)} errors')
    raise SystemExit(bool(errors))
