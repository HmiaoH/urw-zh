import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from compile_chat_options import GENERATED_FILE, REVIEW_FILE, compile_options, existing_translations, static_calls


class ChatOptionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'data/catalog/binary.json').read_text())
        cls.review = json.loads((ROOT / 'data' / REVIEW_FILE).read_text())

    def test_reviewed_manifest_matches_generated_display_entries(self):
        rows = compile_options(self.catalog, self.review, existing=existing_translations())
        self.assertEqual(rows, json.loads(GENERATED_FILE.read_text()))
        self.assertEqual({r['context'] for r in rows}, {'showtext', 'player-talk'})
        by_context = {(r['context'], r['original']): r['translation'] for r in rows}
        option = '"I have something for you..."'
        self.assertEqual(by_context['showtext', option], '“我有东西要给你……”')
        self.assertEqual(by_context['player-talk', option], '“我有东西要给你……”')
        self.assertIn(('showtext', 'Offer an item'), by_context)
        self.assertNotIn(('player-talk', 'Offer an item'), by_context)
        self.assertNotIn(('showtext', '"Who are you?"'), by_context)
        routes = {c['route'] for r in self.review['rows'] for c in r['calls']}
        for row in rows:
            self.assertEqual(row['kind'], 'exact')
            self.assertFalse(row['runtime_verified'])
            self.assertFalse(routes.intersection((row['original'], row['translation'])))
            self.assertFalse(any(key.startswith('route') for key in row['evidence']))

    def test_rejects_mismatched_routes_and_unsupported_targets(self):
        review = copy.deepcopy(self.review)
        review['rows'][0]['calls'][0]['route'] = '[FAKE ROUTE]'
        with self.assertRaisesRegex(ValueError, 'routing key differs'):
            compile_options(self.catalog, review)
        for target, error in (
            ('“给你。[DELIVER]”', 'unsupported option body'),
            ('“给你。|DELIVER”', 'unsupported option body'),
            ('“给你。%s”', 'unsupported option body'),
            ('1.给你。', 'unsupported option body'),
            ('给你。', 'changed quote wrapper'),
        ):
            with self.subTest(target=target):
                review = copy.deepcopy(self.review)
                review['rows'][0]['translation'] = target
                with self.assertRaisesRegex(ValueError, error):
                    compile_options(self.catalog, review)

    def test_static_extraction_checks_register_order_and_zero_hotkey(self):
        body = json.dumps('"I would like to pay my debt."')
        asm = (
            f'000000010017b0b6\tleaq\t0x909e9(%rip), %rsi ## literal pool for: {body}\n'
            '000000010017b0bd\tleaq\t0x90a01(%rip), %rdx ## literal pool for: "[PAY DEBT]"\n'
            '000000010017b0c4\txorl\t%edi, %edi\n'
            '000000010017b0c6\tcallq\t__Z13AddChatOptioniPcS_\n'
        )
        self.assertEqual(static_calls(asm), {
            '0x10017b0c6': (
                ('0x10020baa6', '"I would like to pay my debt."'),
                ('0x10020bac5', '[PAY DEBT]'),
            ),
        })
        self.assertEqual(static_calls(asm.replace('xorl\t%edi, %edi', 'movl\t$0x31, %edi')), {})
        self.assertEqual(static_calls(asm.replace('xorl\t%edi, %edi', 'movq\t%rdx, %rsi')), {})
        self.assertEqual(static_calls(asm.replace(', %rdx', ', %rsi')), {})

    def test_binary_evidence_when_disassembly_is_available(self):
        path = ROOT / 'build/disassembly.txt'
        if not path.is_file():
            self.skipTest('Local game disassembly unavailable')
        rows = compile_options(self.catalog, self.review, existing=existing_translations(),
                               disassembly=path.read_text())
        self.assertEqual(rows, json.loads(GENERATED_FILE.read_text()))


if __name__ == '__main__':
    unittest.main()
