import copy
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validate_items', ROOT/'tools/validate_items.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ItemRulesTest(unittest.TestCase):
    def setUp(self):
        self.rules=json.loads((ROOT/'data/items.json').read_text())
    def test_shipped_rules(self):
        self.assertEqual(module.validate_items(self.rules), [])
    def test_bad_shapes(self):
        for group in module.GROUPS:
            rules=copy.deepcopy(self.rules);rules[group]=[]
            self.assertTrue(module.validate_items(rules))
    def test_cycles_and_controls(self):
        self.rules['plurals']['arrow']='arrows'
        self.assertTrue(module.validate_items(self.rules))
        del self.rules['plurals']['arrow']
        self.rules['bases']['unsafe']='<red>危险'
        self.assertTrue(module.validate_items(self.rules))
