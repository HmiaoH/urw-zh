import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from compile_chat_resources import compile_body, compile_chat, existing_translations, split_line
from validate import PARAM, REF, load, validate


class ChatResourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'data/catalog/messages.json').read_text())
        cls.review = json.loads((ROOT / 'data/rules/chat_reviewed.json').read_text())

    def test_generation_and_display_slots(self):
        rows = compile_chat(self.catalog, self.review, existing=existing_translations())
        self.assertEqual(rows, json.loads((ROOT / 'data/translations/generated_chat_resources.json').read_text()))
        self.assertEqual(len(rows), 76)
        self.assertEqual(sum(r['kind'] == 'exact' for r in rows), 26)
        self.assertEqual(validate(load()), [])
        self.assertEqual({r['line'] for r in self.review['rows']} -
                         {r['evidence']['line'] for r in rows}, {20, 99, 148})
        review = copy.deepcopy(self.review)
        del next(r for r in review['rows'] if r['line'] == 148)['exclusion_reason']
        with self.assertRaisesRegex(ValueError, 'multiple text slots'):
            compile_chat(self.catalog, review)
        self.assertTrue(all(r['context'] == 'npc-talk' and not r['runtime_verified'] for r in rows))

        for row in rows:
            with self.subTest(line=row['evidence']['line']):
                names = [name for name, _ in PARAM.findall(row['original'])]
                captures = {name: f"Sample {i} - O'Neil" for i, name in enumerate(names)}
                body = PARAM.sub(lambda m: captures[m[1]], row['original'])
                literal = re.split(PARAM, row['original'])[::3]
                match = re.fullmatch(r'([^\r\n]{1,256}?)'.join(map(re.escape, literal)), body)
                self.assertIsNotNone(match)
                self.assertEqual(match.groups(), tuple(captures.values()))
                target = REF.sub(lambda m: captures[m[1]], row['translation'])
                for captured in captures.values():
                    self.assertEqual(target.count(captured), 1)

        rumors = [r for r in rows if 'formatted_display' in r['evidence']]
        self.assertEqual(len(rumors), 6)
        self.assertEqual(sum(r['evidence']['selector'] == 'many' for r in rumors), 3)
        self.assertTrue(all('{rumor_subject:text}' in r['original'] and
                            '{rumor_subject}' in r['translation'] for r in rumors))

    def test_prefixes_and_unsupported_patterns(self):
        self.assertEqual(split_line(':( -Drop it now!')[:3], ('Drop it now!', 'negative', None))
        self.assertEqual(split_line(':) -Thanks - really!')[:3], ('Thanks - really!', 'positive', None))
        self.assertEqual(split_line(':| -Fine.')[:3], ('Fine.', 'neutral', None))
        self.assertEqual(split_line('many: -About %s.')[:3], ('About %s.', 'neutral', 'many'))
        self.assertEqual(split_line('-Hi.')[:3], ('Hi.', 'neutral', None))
        with self.assertRaises(ValueError):
            split_line('unverified: -Some text.')
        for source, target, selector in (
            ('[IN_DIR:<plr_name>]', '<plr_name>', None),
            ('Look at <plr_name> <plr_identity>.', '<plr_name>、<plr_identity>。', None),
            ('Look at <unknown>.', '<unknown>。', None),
            ('Look at <plr_name>.', '看。', None),
            ('Look at %s.', '看看%s。', None),
            ('Look there.', '看那边。', 'many'),
            ("I'm <plr_name>.", '我是<plr_name>。', None),
        ):
            with self.subTest(source=source), self.assertRaises(ValueError):
                compile_body(source, target, '.GREET.', selector)

    def test_review_and_resource_identity(self):
        review = copy.deepcopy(self.review)
        review['rows'][0]['translation'] = ':) -你打算拿什么来换，<reptitle_trading>？'
        with self.assertRaisesRegex(ValueError, 'routing prefix'):
            compile_chat(self.catalog, review)
        review['rows'][0]['line'] += 1
        with self.assertRaisesRegex(ValueError, 'does not match source row'):
            compile_chat(self.catalog, review)
        review['rows'].pop()
        with self.assertRaisesRegex(ValueError, 'exactly once'):
            compile_chat(self.catalog, review)

        row = self.catalog[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'urw_chat.txt'
            lines = ['', row['section'], row['original'] + ' ']
            path.write_text('\n'.join(lines), encoding='cp437')
            review = {**self.review, 'rows': self.review['rows'][:1]}
            self.assertEqual(len(compile_chat([row], review, path)), 1)
            lines[1] = '.WRONG.'
            path.write_text('\n'.join(lines), encoding='cp437')
            with self.assertRaisesRegex(ValueError, 'section differs'):
                compile_chat([row], review, path)


if __name__ == '__main__':
    unittest.main()
