import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from compile_item_rules import compile_rules, game_plural


class CompileItemRulesTest(unittest.TestCase):
    def setUp(self):
        self.rules = json.loads((ROOT / "data/items.json").read_text(encoding="utf-8"))

    def test_game_plural(self):
        for base, plural in {
            "knife": "knives",
            "staff": "staves",
            "block of birch wood": "blocks of birch wood",
            "berry": "berries",
            "branch": "branches",
            "boots": "boots",
            "goose/geese": "geese",
            "leaf": "leaves",
            "axe": "axes",
            "bear tooth": "bear teeth",
        }.items():
            with self.subTest(base=base):
                self.assertEqual(game_plural(base), plural)

    def test_compiles_only_reviewed_bases(self):
        self.rules["bases"]["goose/geese"] = "鹅"
        before = copy.deepcopy(self.rules)
        result = compile_rules(self.rules)
        self.assertEqual(self.rules, before)
        self.assertEqual(result["plurals"]["geese"], "goose/geese")
        self.assertEqual(result["plurals"]["staves"], "staff")
        self.assertEqual(result["plurals"]["blocks of wood"], "block of wood")
        self.assertEqual(result["plurals"]["dresses"], "dress")
        self.assertNotIn("boots", result["plurals"])
        self.assertNotIn("widget", result["bases"])
        self.assertNotIn("widgets", result["plurals"])
        self.assertEqual(compile_rules(result), result)

    def test_conflicting_generated_and_explicit_alias(self):
        self.rules["plurals"]["staves"] = "branch"
        with self.assertRaisesRegex(ValueError, "Conflicting plural alias 'staves'"):
            compile_rules(self.rules)

    def test_conflicting_generated_aliases(self):
        self.rules["bases"]["staff/staves"] = "杖"
        with self.assertRaisesRegex(ValueError, "Conflicting plural alias 'staves'"):
            compile_rules(self.rules)

    def test_alias_cannot_shadow_reviewed_base(self):
        self.rules["bases"]["staves"] = "杖"
        with self.assertRaisesRegex(ValueError, "shadows a reviewed base"):
            compile_rules(self.rules)
