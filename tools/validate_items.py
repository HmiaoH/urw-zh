#!/usr/bin/env python3
"""Validate the separately scoped inventory composition lexicon."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GROUPS = ('bases', 'plurals', 'quality', 'material', 'state', 'suffix')
def validate_items(data):
    errors = []
    if not isinstance(data, dict) or data.get('schema') != 1:
        return ['items: unsupported schema']
    for group in GROUPS:
        pairs = data.get(group)
        if not isinstance(pairs, dict) or not pairs or len(pairs) > 2000:
            errors.append(f'items: invalid {group} map')
            continue
        for key, value in pairs.items():
            if not all(isinstance(s, str) and 0 < len(s) <= 240 and not any(c in s for c in '\n\r\t<>') for s in (key, value)):
                errors.append(f'items: invalid {group} entry {key!r}')
                continue
            if key != key.lower() or (group != 'suffix' and key != key.strip()):
                errors.append(f'items: noncanonical key {key!r}')
            if group == 'suffix' and not key.startswith(' '):
                errors.append(f'items: suffix must have a boundary: {key!r}')
            if group == 'plurals' and (value in pairs or value == key):
                errors.append(f'items: chained or cyclic plural {key!r}')
    return errors
if __name__ == '__main__':
    data = json.loads((ROOT/'data/items.json').read_text())
    errors = validate_items(data)
    if errors: raise SystemExit('\n'.join(errors))
    print(', '.join(f'{g}: {len(data[g])}' for g in GROUPS))
