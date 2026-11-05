import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from compile_dialogue_rules import compile_rules
from validate import validate
class DialogueRuleTest(unittest.TestCase):
 def setUp(self):self.rules=json.loads((ROOT/'data/rules/navigation.json').read_text())
 def test_bounded_expansion(self):
  rows=compile_rules(self.rules)
  self.assertEqual(len(rows),57)
  self.assertEqual(validate(rows),[])
  navigation=[r for r in rows if r['original'].startswith('There is a ')]
  self.assertEqual(len(navigation),48)
  self.assertTrue(all('{place:text}' in r['original'] and '{place}' in r['translation'] for r in navigation))
  self.assertTrue(any('about {amount:int} miles' in r['original'] and '{amount}英里' in r['translation'] for r in rows))
 def test_unreviewed_and_unknown_values(self):
  rules=copy.deepcopy(self.rules);rules['development_only']=True
  with self.assertRaises(ValueError):compile_rules(rules)
  rows=compile_rules(self.rules)
  self.assertEqual(sum(' village.' in r['original'] for r in rows),1)
