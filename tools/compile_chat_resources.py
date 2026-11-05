#!/usr/bin/env python3
"""Compile reviewed CHATMSG display lines without changing resource routing."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from validate import PARAM, normalize, validate

ROOT = Path(__file__).resolve().parents[1]
RESOURCE = 'messages/urw_chat.txt'
PREFIX = re.compile(r'(?:(:\(|:\||:\)) |(many): )?')
SELF_INTRODUCTION = re.compile(r"(?:I'm|They call me|My name is|I am called|I'm known as) <[a-z_]+>\.")
TOKEN = re.compile(r'<([a-z_]+)>|%s')
UNSUPPORTED = re.compile(r'[<>{}\[\]%\x00-\x1f]')
VARIABLES = {
    'plr_identity', 'plr_bad_name', 'plr_name', 'reptitle_trading',
    'reptitle_trading_ind', 'reptitle_tra_ind', 'reptitle_stealing',
    'reptitle_mischief_ind', 'reptitle_help_ind',
}
RUMOR_TOPICS = {'.WOM_BAD_INFO.', '.WOM_BAD_NEWS.', '.WOM_BAD_RUMORS.'}
REVIEW_FILE = 'data/rules/chat_reviewed.json'
GENERATED_FILE = ROOT / 'data/translations/generated_chat_resources.json'
AMBIGUITY_REASON = 'Multiple text slots can match more than one split in the current display matcher.'


def split_line(raw):
    prefix, separator, body = raw.partition('-')
    parsed = PREFIX.fullmatch(prefix)
    if not separator or not parsed or not body or body[0].isspace():
        raise ValueError(f'Unsupported chat row: {raw!r}')
    emotion, selector = parsed.groups()
    return body, {':(': 'negative', ':)': 'positive'}.get(emotion, 'neutral'), selector, prefix


def compile_body(source, target, topic, selector):
    if SELF_INTRODUCTION.fullmatch(source):
        raise ValueError('Unconstrained self-introduction')
    matches = list(TOKEN.finditer(source))
    if UNSUPPORTED.search(TOKEN.sub('', source) + TOKEN.sub('', target)):
        raise ValueError('Unsupported message expression')
    if Counter(m.group() for m in matches) != Counter(m.group() for m in TOKEN.finditer(target)):
        raise ValueError('Translation changed the source slots')
    if any(not source[left.end():right.start()].strip() for left, right in zip(matches, matches[1:])):
        raise ValueError('Adjacent unconstrained slots')
    if matches and not any(c.isalpha() for c in TOKEN.sub('', source)):
        raise ValueError('Template needs a literal text anchor')
    if any(m.group(1) is not None and m.group(1) not in VARIABLES for m in matches):
        raise ValueError('Unverified chat variable')
    c_slots = sum(m.group() == '%s' for m in matches)
    if topic in RUMOR_TOPICS:
        if c_slots != 1 or len(matches) != 1 or selector not in (None, 'many'):
            raise ValueError('Invalid rumor argument')
    elif c_slots or selector:
        raise ValueError('Unverified chat selector or printf argument')

    def convert(text, source_side):
        seen = Counter()

        def substitute(match):
            name = match.group(1) or 'rumor_subject'
            seen[name] += 1
            suffix = f'_{seen[name]}' if seen[name] > 1 else ''
            return '{' + name + suffix + (':text}' if source_side else '}')

        return TOKEN.sub(substitute, text)

    return convert(source, True), convert(target, False), 'template' if matches else 'exact'


def check_resource(rows, path):
    lines = path.read_text(encoding='cp437').splitlines()
    section = None
    by_line = {r['line']: r for r in rows}
    if len(by_line) != len(rows):
        raise ValueError('Duplicate chat resource line')
    for number, raw in enumerate(lines, 1):
        if raw.startswith('.'):
            section = raw.rstrip()
        if number not in by_line:
            prefix, separator, body = raw.partition('-')
            if section and separator and body and PREFIX.fullmatch(prefix):
                raise ValueError(f'{path}:{number}: chat line is absent from catalog')
            continue
        row = by_line.pop(number)
        # The catalog trims trailing resource whitespace. The display lookup
        # normalizes whitespace on both sides of the generated key.
        if raw.rstrip() != row['original'] or section != row['section']:
            raise ValueError(f'{path}:{number}: source body or section differs from catalog')
    if by_line:
        raise ValueError(f'{path}: source ends before catalog lines {sorted(by_line)}')


def existing_translations():
    return [row for path in sorted(GENERATED_FILE.parent.glob('*.json'))
            if path != GENERATED_FILE for row in json.loads(path.read_text())]


def compile_chat(catalog, review, resource_path=None, *, existing=()):
    existing_exact = {
        normalize(r['original']): r['translation'] for r in existing
        if r.get('context') == 'npc-talk' and r.get('kind', 'exact') == 'exact'
        and r.get('status') == 'reviewed' and r.get('translation')
    }
    if review.get('status') != 'reviewed' or review.get('development_only', True):
        raise ValueError('Only reviewed chat rows may be activated')
    source_rows = [r for r in catalog if r.get('source') == RESOURCE]
    source_ids = {r['id'] for r in source_rows}
    reviewed = {r['source_id']: r for r in review['rows']}
    if (not source_rows or len(source_ids) != len(source_rows) or len(reviewed) != len(review['rows'])
            or source_ids != reviewed.keys()):
        raise ValueError('Review must cover each chat resource ID exactly once')
    if resource_path is not None:
        check_resource(source_rows, resource_path)
    rows = []
    for row in sorted(source_rows, key=lambda r: r['line']):
        source_id, section, line = row['id'], row['section'], row['line']
        selected = reviewed[source_id]
        if (selected['line'], selected['section'], selected['original']) != (line, section, row['original']):
            raise ValueError(f'{source_id}: review does not match source row')
        try:
            source, emotion, selector, prefix = split_line(row['original'])
            target, _, _, target_prefix = split_line(selected['translation'])
            if prefix != target_prefix:
                raise ValueError('Translation changed the routing prefix')
            topic = section[:section.index('.', 1) + 1]
            original, translation, kind = compile_body(source, target, topic, selector)
        except ValueError as error:
            raise ValueError(f'{RESOURCE}:{line}: {error}') from error
        if len(PARAM.findall(original)) > 1:
            if selected.get('exclusion_reason') != AMBIGUITY_REASON:
                raise ValueError(f'{RESOURCE}:{line}: multiple text slots require explicit exclusion')
            continue
        if selected.get('exclusion_reason'):
            raise ValueError(f'{RESOURCE}:{line}: unexpected exclusion')
        if kind == 'exact' and normalize(original) in existing_exact:
            if normalize(existing_exact[normalize(original)]) != normalize(translation):
                raise ValueError(f'{RESOURCE}:{line}: conflicts with existing reviewed display text')
            continue
        evidence = {
            'source_id': source_id, 'resource': RESOURCE, 'section': section,
            'line': line, 'emotion': emotion, 'selector': selector,
            'prefix': prefix, 'production': 'CHATMSG (0x1001b9495, 0x1001b9659)',
        }
        if topic in RUMOR_TOPICS:
            evidence['formatted_display'] = 'sprintf (0x10018f681), CrTalk (0x10018f689)'
        rows.append({
            'id': hashlib.sha256(f'chat-display\t{source_id}'.encode()).hexdigest()[:20],
            'source': REVIEW_FILE.removeprefix('data/'), 'context': 'npc-talk',
            'original': original, 'translation': translation, 'kind': kind,
            'status': 'reviewed', 'runtime_verified': False, 'evidence': evidence,
        })
    match_keys = {(r['kind'], PARAM.sub('{text}', normalize(r['original']))) for r in rows}
    if len(match_keys) != len(rows):
        raise ValueError('Duplicate chat display match shape')
    errors = validate(rows)
    if errors:
        raise ValueError('\n'.join(errors))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource', type=Path, help='also verify against the CP437 game file')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'data/catalog/messages.json').read_text())
    review = json.loads((ROOT / REVIEW_FILE).read_text())
    rows = compile_chat(catalog, review, args.resource, existing=existing_translations())
    GENERATED_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    counts = Counter(row['kind'] for row in rows)
    print(f'{len(rows)} chat entries ({counts["exact"]} exact, {counts["template"]} templates); {len(review["rows"]) - len(rows)} reviewed rows covered by existing entries or excluded')


if __name__ == '__main__':
    main()
