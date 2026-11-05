#!/usr/bin/env python3
"""Report source translation and runtime verification independently."""
import json
from collections import Counter
from pathlib import Path
from bind import ROOT
from validate import validate

def read_rows(directory):
    return [r for p in sorted(directory.glob('*.json')) for r in json.loads(p.read_text())]

def source_id(row):
    evidence=row.get('evidence')
    return row.get('source_id') or (evidence.get('source_id') if isinstance(evidence,dict) else None) or row['id']

def report():
    catalog=read_rows(ROOT/'data/catalog')
    evidence=ROOT/'data/runtime_verified.json'
    verified={r['source_id'] for r in json.loads(evidence.read_text()) if r['result']=='passed'} if evidence.exists() else set()
    drafts=read_rows(ROOT/'data/drafts')
    active=read_rows(ROOT/'data/translations')
    translated={source_id(r):r for r in drafts+active if r.get('translation')}
    groups={}
    for row in catalog:
        if row.get('scope')=='unclassified-binary':continue
        group=groups.setdefault(row['source'],Counter(total=0,translated=0,reviewed=0,runtime_verified=0))
        group['total']+=1
        candidate=translated.get(row['id'])
        if candidate:
            group['translated']+=1
            group['reviewed']+=candidate['status']=='reviewed'
            group['runtime_verified']+=row['id'] in verified
    return dict(scope='Catalogued resource text only; binary candidates are excluded until classified, and dynamic runtime outputs are not fully covered.',resources=groups,unclassified_binary_candidates=sum(r.get('scope')=='unclassified-binary' for r in catalog),binary_translation_queue=dict(passthrough=sum(r.get('scope')=='unclassified-binary' and r.get('translation')==r['original'] for r in drafts),translated=sum(r.get('scope')=='unclassified-binary' and bool(r.get('translation')) for r in drafts),proposed_exclusions=sum(r.get('scope')=='unclassified-binary' and bool(r.get('exclusion_reason')) for r in drafts),untouched_candidates=len({r['id'] for r in catalog if r.get('scope')=='unclassified-binary'}-{r['id'] for r in drafts if r.get('translation') or r.get('exclusion_reason')})),catalogued_resource_totals={k:sum(g[k] for g in groups.values()) for k in ('total','translated','reviewed','runtime_verified')},runtime_dictionary=dict(records=len(active),exact_records=sum(r.get('kind','exact')=='exact' for r in active),dynamic_template_records=sum(r.get('kind')=='template' for r in active),translated=sum(bool(r.get('translation')) and r['translation']!=r['original'] for r in active),passthrough=sum(r.get('translation')==r['original'] for r in active)),draft_validation_errors=validate(drafts))

if __name__=='__main__':
    print(json.dumps(report(),ensure_ascii=False,indent=2))
