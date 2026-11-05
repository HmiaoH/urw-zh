import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate_hypertext import validate_hypertext
class HypertextTest(unittest.TestCase):
 def test_labels_cannot_change_targets(self):
  row={'id':'sample','context':'encyclopedia','translation':'用于[[HUNTING|狩猎]]的[[KNIFE|刀]]','link_targets':['HUNTING','KNIFE']}
  self.assertEqual(validate_hypertext([row]),[])
  row['translation']='用于[[HUNTING|狩猎]]的[[SWORD|刀]]'
  self.assertTrue(validate_hypertext([row]))
 def test_malformed_link(self):
  self.assertTrue(validate_hypertext([{'id':'broken','context':'encyclopedia','translation':'[[KNIFE|刀','link_targets':['KNIFE']}]))
 def test_nonexistent_topic(self):
  self.assertTrue(validate_hypertext([{'id':'unknown','context':'encyclopedia','translation':'[[NONEXISTENT TOPIC|主题]]','link_targets':['NONEXISTENT TOPIC']}]))
