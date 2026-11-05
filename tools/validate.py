#!/usr/bin/env python3
"""Validate reviewed display translations before they enter a build."""
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAM = re.compile(r'\{([A-Za-z][A-Za-z0-9_]*):(int|number|text)\}')
REF = re.compile(r'\{([A-Za-z][A-Za-z0-9_]*)\}')
PRINTF = re.compile(r'%(?:\d+\$)?[-+#0 ]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|ll|[hljztL])?[diuoxXfFeEgGaAcsp%]')

def normalize(text):
    text = ' '.join(text.split())
    return re.sub(r'\s*(</?[A-Za-z]+>)\s*', r'\1', text).strip()

def validate(rows):
    errors, ids, keys = [], set(), {}
    for i, row in enumerate(rows):
        label = row.get('id', str(i))
        def fail(message): errors.append(f'{label}: {message}')
        if not all(isinstance(row.get(k), str) and row[k] for k in ('id','source','context','original','status')):
            fail('missing required string field'); continue
        if label in ids: fail('duplicate ID')
        ids.add(label)
        original, translation = row['original'], row.get('translation', '')
        if row['status'] not in ('pending','draft','reviewed'): fail('unknown review status')
        if not isinstance(translation, str): fail('translation must be a string'); continue
        if not translation:
            if row['status'] == 'reviewed': fail('reviewed translation is empty')
            continue
        if '\x00' in original + translation: fail('embedded NUL')
        if row.get('allow_break_variation') and (row['context']!='paragraph' or not row['source'].startswith('RNDCAMP.') or '<' in original):
            fail('break variation is limited to complete plain scenario paragraphs')
        kind = row.get('kind', 'exact')
        if kind not in ('exact','template'): fail('unknown match kind')
        if 'segments' in row:
            parts=row['segments']; end=0; combined=''
            if kind!='exact' or row['context'] not in ('showtext','renshow') or not original.isascii():
                fail('segments require an ASCII exact source in a supported drawing context')
            if not isinstance(parts,list) or not 1<=len(parts)<=16:
                fail('invalid segment list')
            else:
                for part in parts:
                    if not isinstance(part,dict) or not isinstance(part.get('text'),str) or not part['text'] or type(part.get('offset')) is not int or type(part.get('width')) is not int:
                        fail('invalid segment'); continue
                    offset,width=part['offset'],part['width']
                    if offset<end or width<16 or offset+width>len(original)*8: fail('overlapping or out-of-bounds segment')
                    end=offset+width; combined+=part['text']
                if normalize(combined)!=normalize(translation): fail('segments do not preserve the full translation')
        key = (row['context'], normalize(original), kind)
        if key in keys:
            if normalize(keys[key]) != normalize(translation):
                fail('conflicting translations for normalized key')
        else:
            keys[key] = translation
        if kind == 'template':
            params = PARAM.findall(original)
            names = [p[0] for p in params]
            if not params or len(names) != len(set(names)): fail('template requires unique typed parameters')
            if row['context'] == '*': fail('dynamic template requires explicit context')
            if collections.Counter(names) != collections.Counter(REF.findall(translation)): fail('template parameter mismatch')
            if re.search(r'[{}]', PARAM.sub('',original) + REF.sub('',translation)): fail('invalid parameter syntax')
        # These resources contain literal prose percentages, never printf format strings.
        prose = row['source'] == 'GAME.NFO' or row['source'].startswith(('RNDCAMP.', 'gameinfo/'))
        if not prose and collections.Counter(PRINTF.findall(original)) != collections.Counter(PRINTF.findall(translation)): fail('printf placeholder mismatch')
        if collections.Counter(re.findall(r'</?[A-Za-z]+>',original)) != collections.Counter(re.findall(r'</?[A-Za-z]+>',translation)): fail('control tag mismatch')
        for key in row.get('preserve', []):
            if original.count(key) != translation.count(key): fail(f'protected token changed: {key}')
    return errors

def load(path=ROOT/'data/translations'):
    return [row for p in sorted(path.glob('*.json')) for row in json.loads(p.read_text())]

if __name__ == '__main__':
    rows = load(); errors = validate(rows)
    for error in errors: print(error)
    print(f'{len(rows)} entries, {len(errors)} errors')
    raise SystemExit(bool(errors))
