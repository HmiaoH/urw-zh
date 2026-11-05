import json
import re
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))

from compile_notification_resources import CATALOG, OUTPUT, RULES, compile_rule, compile_rules
from validate import PARAM, REF, load


class NotificationResourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG.read_text())
        cls.sources = {row['section']: row for row in cls.catalog}
        cls.rules = json.loads(RULES.read_text())
        cls.existing = [row for row in load() if not row['id'].startswith('notification-')]
        cls.generated = compile_rules(cls.rules, cls.catalog, cls.existing)

    def test_generated_catalog_is_current(self):
        self.assertEqual(self.generated, json.loads(OUTPUT.read_text()))
        self.assertEqual(len(self.generated), len(self.rules['entries']) - 2)
        self.assertTrue(all(row['context'] == 'message' for row in self.generated))
        self.assertTrue(all(not row['runtime_verified'] for row in self.generated))
        self.assertNotIn('!That is not a door or gate.', [row['original'] for row in self.generated])

    def test_sound_removed_but_color_preserved(self):
        row, = compile_rule(self.sources['.EAT_FULL.'], '{BURP}=嗝！你吃饱了。')
        self.assertEqual(row['original'], '=Burp! Your stomach is full.')
        self.assertEqual(row['translation'], '嗝！你吃饱了。')
        self.assertEqual(row['kind'], 'exact')
        with self.assertRaisesRegex(ValueError, 'control prefix'):
            compile_rule(self.sources['.EAT_FULL.'], '=嗝！你吃饱了。')

    def test_case_alias_for_literal_and_no_alias_for_dynamic_name(self):
        source = self.sources['.CAN_WADE.'] | {'original': ':the water is shallow.'}
        rows = compile_rule(source, ':这里的水很浅。')
        self.assertEqual([row['original'] for row in rows], [':the water is shallow.', ':The water is shallow.'])
        row, = compile_rule(self.sources['.NPC_WITHDRAWS.'], '<npc_defdesc>让开了。')
        self.assertEqual(row['original'], '{creature:text} withdraws from your way.')

    def test_slot_samples_match_uniquely_and_preserve_full_value(self):
        samples = {
            'item': 'the fine pot of rye porridge',
            'items': '03 crude arrows',
            'creature': 'Kimmo "Ash" the Sartolais woodsman',
        }
        templates = []
        for row in self.generated:
            if row['kind'] != 'template':
                continue
            param, = PARAM.finditer(row['original'])
            head, tail = row['original'][:param.start()], row['original'][param.end():]
            pattern = re.compile(re.escape(head) + r'([^\r\n]{1,256}?)' + re.escape(tail))
            templates.append((row, pattern, head, tail, param.group(1)))

        for row, pattern, head, tail, name in templates:
            value = samples[name]
            with self.subTest(source=row['original']):
                source = head + value + tail
                matched = [p.fullmatch(source) for _, p, *_ in templates]
                match, = [m for m in matched if m]
                expanded = REF.sub(lambda _: match.group(1), row['translation'])
                self.assertEqual(match.group(1), value)
                self.assertEqual(expanded.count(value), 1)
                self.assertIsNone(pattern.fullmatch(head + tail))
                self.assertIsNone(pattern.fullmatch(head + 'x' * 257 + tail))

    def test_rejects_unreviewed_native_grammar(self):
        source = self.sources['.CAN_WADE.']
        for original in ('[PC:Hello.]', '!You found %s.', '{UNKNOWN}Hello.',
                         '+You dropped <unknown>.', '+You gave <item> to <npc_desc>.'):
            with self.subTest(original=original), self.assertRaises(ValueError):
                compile_rule(source | {'original': original}, original)
        with self.assertRaisesRegex(ValueError, 'slot mismatch'):
            compile_rule(self.sources['.BAD_MELEE_WEAPON.'], '!这件物品不能用来攻击。')
        with self.assertRaisesRegex(ValueError, 'changed literal numbers'):
            compile_rule(source | {'original': '+You collected 03 stones.'}, '+你收集了3块石头。')

    def test_rejects_overlapping_templates(self):
        sources = [self.sources['.EAT_COMPLETE.'], self.sources['.EAT_PARTIAL.']]
        entries = [
            dict(source_id=row['id'], original=row['original'], translation=target)
            for row, target in zip(sources, (':你吃完了<item_verbose_def>。', ':你吃完了部分<item_raw>。'))
        ]
        with self.assertRaisesRegex(ValueError, 'overlapping notification'):
            compile_rules({'status': 'reviewed', 'entries': entries}, self.catalog, [])

    def test_rejects_catalog_drift_and_conflicting_exact(self):
        entry = next(row for row in self.rules['entries'] if row['original'] == '!That is not a door or gate.')
        with self.assertRaisesRegex(ValueError, 'source changed'):
            rules = {'status': 'reviewed', 'entries': [entry | {'original': '!Old text.'}]}
            compile_rules(rules, self.catalog, self.existing)
        with self.assertRaisesRegex(ValueError, 'conflicting notification'):
            rules = {'status': 'reviewed', 'entries': [entry | {'translation': '!这里没有门。'}]}
            compile_rules(rules, self.catalog, self.existing)


if __name__ == '__main__':
    unittest.main()
