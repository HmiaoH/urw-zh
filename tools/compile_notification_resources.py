#!/usr/bin/env python3
"""Compile reviewed resource messages for matching the expanded Note buffer."""

import argparse
import json
import re
from collections import Counter

from validate import PARAM, ROOT, load, normalize, validate


CATALOG = ROOT / 'data/catalog/messages.json'
RULES = ROOT / 'data/rules/notifications_reviewed.json'
OUTPUT = ROOT / 'data/translations/generated_notifications.json'

SOURCES = {'messages/urw_msg.txt', 'messages/urw_combat.txt'}
COLOR_PREFIXES = '!#&+:=>?_'
SOUND = re.compile(r'^\{(FIRE|BURP)\}')
VARIABLE = re.compile(r'<([a-z_]+)>')
SLOTS = {
    'npc_desc': 'creature', 'npc_defdesc': 'creature', 'npc_ind': 'creature',
    'item': 'item', 'item_def': 'item', 'item_ind': 'item',
    'item_raw': 'item', 'raw_item': 'item', 'the_item': 'item',
    'item_container': 'item', 'the_item_container': 'item',
    'item_verbose_def': 'item', 'item_def_verbose': 'item',
    'fullitem': 'item', 'the_fullitem': 'item',
    'items': 'items', 'items_ind': 'items', 'items_nonum': 'items',
    'items_verbose': 'items',
}


def split_prefix(text):
    sound = SOUND.match(text)
    if sound:
        text = text[sound.end():]
    color = text[:1] if text[:1] in COLOR_PREFIXES else ''
    return sound[0] if sound else '', color, text[len(color):]


def compile_rule(source, target):
    original = source['original']
    if source['source'] not in SOURCES or source['syntax'] != 'game-message-expression':
        raise ValueError('unsupported message source')
    if not original.isascii() or any(c in original + target for c in '[]%\r\n\x00'):
        raise ValueError('unsupported expression')
    sound, color, body = split_prefix(original)
    target_sound, target_color, translated_body = split_prefix(target)
    if (sound, color) != (target_sound, target_color):
        raise ValueError('control prefix differs from source')
    for text in (body, translated_body):
        if re.search(r'[{}<>]', VARIABLE.sub('', text)) or text.startswith(('*', '@')):
            raise ValueError('unrecognized control or slot')
    variables = VARIABLE.findall(body)
    if Counter(variables) != Counter(VARIABLE.findall(translated_body)):
        raise ValueError('slot mismatch')
    if not translated_body or Counter(re.findall(r'[0-9]+', body)) != Counter(re.findall(r'[0-9]+', translated_body)):
        raise ValueError('empty translation or changed literal numbers')
    if variables:
        if len(variables) != 1 or variables[0] not in SLOTS:
            raise ValueError('only one documented text slot is supported')
        if len(re.findall(r'[A-Za-z]+', VARIABLE.sub('', body))) < 3:
            raise ValueError('insufficient literal anchors around slot')
        slot = SLOTS[variables[0]]
        body = VARIABLE.sub('{' + slot + ':text}', body)
        translated_body = VARIABLE.sub('{' + slot + '}', translated_body)

    # Note uppercases the leading ASCII letter unless _NOTEMOD_alkuok
    # suppresses it. A leading dynamic value is already captured as displayed.
    variants = [body]
    if re.match(r'[a-z]', body):
        variants.append(body[0].upper() + body[1:])
    return [
        dict(
            id='notification-' + source['id'] + ('-capitalized' if i else ''),
            source=source['source'],
            source_id=source['id'],
            section=source['section'],
            line=source['line'],
            context='message',
            original=color + variant,
            translation=translated_body,
            kind='template' if variables else 'exact',
            status='reviewed',
            runtime_verified=False,
        )
        for i, variant in enumerate(variants)
    ]


def compile_rules(rules, catalog, existing):
    if rules['status'] != 'reviewed':
        raise ValueError('reviewed notification rules required')
    sources = {row['id']: row for row in catalog}
    occupied = {
        (normalize(row['original']), row.get('kind', 'exact')): row
        for row in existing
        if row['status'] == 'reviewed' and row['context'] in ('message', '*')
    }
    rows = []
    seen = set()
    for rule in rules['entries']:
        source_id = rule['source_id']
        if source_id in seen:
            raise ValueError(f'duplicate notification source {source_id}')
        seen.add(source_id)
        source = sources[source_id]
        if source['original'] != rule['original']:
            raise ValueError(f'source changed for {source_id}')
        for row in compile_rule(source, rule['translation']):
            key = (normalize(row['original']), row['kind'])
            if key in occupied:
                prior = occupied[key]
                if prior['translation'] != row['translation']:
                    raise ValueError(f'conflicting notification for {row["original"]!r}')
                continue
            occupied[key] = row
            rows.append(row)
    anchors = []
    for row in rows:
        if row['kind'] == 'template':
            original = normalize(row['original'])
            slot = PARAM.search(original)
            head, tail = original[:slot.start()], original[slot.end():]
            for other_head, other_tail in anchors:
                # Reject a shared boundary with a shorter compatible literal on
                # the other side, which would swallow part of the specific rule.
                shared_head = head == other_head and (tail.endswith(other_tail) or other_tail.endswith(tail))
                shared_tail = tail == other_tail and (head.startswith(other_head) or other_head.startswith(head))
                if shared_head or shared_tail:
                    raise ValueError(f'overlapping notification template for {row["original"]!r}')
            anchors.append((head, tail))
    errors = validate([row for row in existing if row['context'] in ('message', '*')] + rows)
    if errors:
        raise ValueError('\n'.join(errors))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='check the committed output without rewriting it')
    args = parser.parse_args()
    existing = [row for row in load() if not row['id'].startswith('notification-')]
    rows = compile_rules(json.loads(RULES.read_text()), json.loads(CATALOG.read_text()), existing)
    rendered = json.dumps(rows, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != rendered:
            raise SystemExit('Generated notification resources are stale')
    else:
        OUTPUT.write_text(rendered)
    print(f'{len(rows)} reviewed notification entries. In-game coverage remains unverified.')


if __name__ == '__main__':
    main()
