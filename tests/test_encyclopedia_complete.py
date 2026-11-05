import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_encyclopedia import audit
from validate import load,normalize

class EncyclopediaCoverage(unittest.TestCase):
    def test_every_visible_source_fragment_has_a_reviewed_translation(self):
        result=audit()
        self.assertEqual(result['totals']['pages'],308)
        self.assertFalse(result['missing'],result['missing'][:5])
        self.assertEqual(result['totals']['fragments'],2047)

    def test_all_topic_aliases_have_titles_and_previews(self):
        keys={(r['context'],normalize(r['original'])) for r in load() if r['status']=='reviewed' and r.get('translation')}
        for topic in audit()['pages']:
            for alias in topic.strip('.').split('.'):
                for context in ('encyclopedia-title','encyclopedia-summary'):
                    self.assertIn((context,alias),keys)
