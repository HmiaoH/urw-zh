import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from check_drafts import check,check_complete
from validate import load,normalize

class CourseTests(unittest.TestCase):
 def test_translation_source_and_control_integrity(self):
  source=json.loads((ROOT/'data/catalog/course_runtime.json').read_text())
  draft=json.loads((ROOT/'data/drafts/course_runtime_luna.json').read_text())
  self.assertEqual(len(source),193)
  self.assertEqual(check(source,draft)+check_complete(source,draft),[])
 def test_both_courses_published(self):
  source=json.loads((ROOT/'data/catalog/course_runtime.json').read_text())
  published={(r['context'],normalize(r['original'])) for r in load() if r['status']=='reviewed' and r['translation']}
  self.assertTrue(all((r['context'],normalize(r['original'])) in published for r in source))
  self.assertEqual(sum(r['part']=='current' for r in source),48)
  self.assertEqual(sum(r['part']=='completed' for r in source),48)
