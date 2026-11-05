#!/usr/bin/env python3
"""Compile reviewed native chat option bodies for display and player echo."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from validate import normalize, validate

ROOT = Path(__file__).resolve().parents[1]
REVIEW_FILE = 'rules/chat_options_reviewed.json'
GENERATED_FILE = ROOT / 'data/translations/generated_chat_options.json'
ADD_OPTION = re.compile(r'(callq|jmp)\s+__Z13AddChatOptioniPcS_\b')
INSTRUCTION = re.compile(r'^([0-9a-f]{16})\t([a-z][a-z0-9]*)\s*(.*)$')
LITERAL = re.compile(r'0x([0-9a-f]+)\(%rip\), %(rsi|rdx)\s+## literal pool for: (".*")')
ARGUMENT = re.compile(r', %(rsi|rdx|edi|esi|edx|rdi|sil|dl|di|si|dx|dil)\s*$')
ARGUMENT_NAMES = dict.fromkeys(('rsi', 'esi', 'si', 'sil'), 'rsi')
ARGUMENT_NAMES.update(dict.fromkeys(('rdx', 'edx', 'dx', 'dl'), 'rdx'))
ARGUMENT_NAMES.update(dict.fromkeys(('rdi', 'edi', 'di', 'dil'), 'edi'))
ROUTE = re.compile(r'\[[A-Z][A-Z :0-9]*\]')
UNSUPPORTED = re.compile(r'[<>{}\[\]%|\\\x00-\x1f\x7f]|^(?:[0-9]|ESC)\.')


def static_calls(disassembly):
    """Recognize nearby literal loads and a zero hotkey in the same basic block."""
    instructions = []
    calls = {}
    for line in disassembly.splitlines():
        parsed = INSTRUCTION.fullmatch(line)
        if not parsed:
            instructions.clear()
            continue
        address, opcode, operands = parsed.groups()
        if ADD_OPTION.match(f'{opcode} {operands}'):
            args = {}
            for previous, operation, argument in reversed(instructions[-9:]):
                if operation.startswith(('j', 'call', 'ret')):
                    break
                destination = ARGUMENT.search(argument.split('##', 1)[0])
                if destination:
                    args.setdefault(ARGUMENT_NAMES[destination[1]], (previous, operation, argument))
            hotkey = args.get('edi')
            if hotkey and hotkey[1:] == ('xorl', '%edi, %edi'):
                literals = []
                for register in ('rsi', 'rdx'):
                    previous, operation, argument = args.get(register, (0, '', ''))
                    literal = LITERAL.fullmatch(argument) if operation == 'leaq' else None
                    if not literal or literal[2] != register:
                        break
                    # These are seven-byte x86-64 RIP-relative LEA instructions.
                    literals.append((hex(previous + 7 + int(literal[1], 16)), json.loads(literal[3])))
                if len(literals) == 2:
                    calls[hex(int(address, 16))] = tuple(literals)
        instructions.append((int(address, 16), opcode, operands))
    return calls


def existing_translations():
    return [row for path in sorted(GENERATED_FILE.parent.glob('*.json'))
            if path != GENERATED_FILE for row in json.loads(path.read_text())]


def compile_options(catalog, review, *, existing=(), disassembly=None):
    if review.get('status') != 'reviewed' or review.get('development_only', True):
        raise ValueError('Only reviewed chat options may be activated')
    by_address = {row['address']: row for row in catalog if row.get('source') == 'urw3-bin:__cstring'}
    existing_keys = {(r['context'], normalize(r['original'])) for r in existing
                     if r.get('kind', 'exact') == 'exact' and r.get('status') == 'reviewed'
                     and r.get('translation')}
    verified_calls = static_calls(disassembly) if disassembly is not None else None
    rows, seen_calls, seen_bodies = [], set(), set()
    for entry in sorted(review['rows'], key=lambda row: row['address']):
        source, target = entry['original'], entry['translation']
        source_row = by_address.get(entry['address'], {})
        if (source_row.get('id'), source_row.get('original')) != (entry['source_id'], source):
            raise ValueError(f'{entry["address"]}: source differs from binary catalog')
        if (not source.strip() or not target.strip() or UNSUPPORTED.search(source)
                or UNSUPPORTED.search(target) or source.startswith(('DEBUG ', 'FLAGS TO '))):
            raise ValueError(f'{source}: unsupported option body')
        quoted = source.startswith('"') and source.endswith('"')
        if (source.count('"') != 2 * quoted or
                (target.startswith('“') and target.endswith('”')) != quoted or
                target.count('“') != quoted or target.count('”') != quoted or '"' in target):
            raise ValueError(f'{source}: changed quote wrapper')
        key = normalize(source)
        if key in seen_bodies:
            raise ValueError(f'{source}: duplicate option body')
        seen_bodies.add(key)
        calls = entry['calls']
        if not calls:
            raise ValueError(f'{source}: missing callsite evidence')
        for call in calls:
            callsite = call['callsite']
            route = call['route']
            if not ROUTE.fullmatch(route) or by_address.get(call['route_address'], {}).get('original') != route:
                raise ValueError(f'{callsite}: routing key differs from binary catalog')
            if callsite in seen_calls:
                raise ValueError(f'{callsite}: duplicate callsite')
            if verified_calls is not None and verified_calls.get(callsite) != (
                (entry['address'], source), (call['route_address'], route),
            ):
                raise ValueError(f'{callsite}: literal arguments differ from disassembly')
            seen_calls.add(callsite)
        for context in ('showtext', 'player-talk') if quoted else ('showtext',):
            if (context, key) in existing_keys:
                continue
            identity = f'chat-option\t{context}\t{entry["source_id"]}'
            rows.append({
                'id': hashlib.sha256(identity.encode()).hexdigest()[:20],
                'source': REVIEW_FILE, 'context': context, 'original': source,
                'translation': target, 'kind': 'exact', 'status': 'reviewed',
                'runtime_verified': False,
                'evidence': {
                    'source_id': entry['source_id'], 'address': entry['address'],
                    'callsites': sorted(call['callsite'] for call in calls),
                    'display_call': '0x1001503d0' if context == 'showtext' else '0x100191ca2',
                },
            })
    errors = validate(rows)
    if errors:
        raise ValueError('\n'.join(errors))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disassembly', type=Path, help='verify literal arguments against the game disassembly')
    args = parser.parse_args()
    review = json.loads((ROOT / 'data' / REVIEW_FILE).read_text())
    catalog = json.loads((ROOT / 'data/catalog/binary.json').read_text())
    disassembly = args.disassembly.read_text() if args.disassembly else None
    rows = compile_options(catalog, review, existing=existing_translations(), disassembly=disassembly)
    GENERATED_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    counts = Counter(row['context'] for row in rows)
    print(f'{len(rows)} chat option entries ({counts["showtext"]} showtext, {counts["player-talk"]} player-talk)')


if __name__ == '__main__':
    main()
