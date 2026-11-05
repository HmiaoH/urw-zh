import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from bind import GAME, SUPPORTED_SHA256
import hashlib

class TradeRejectionSources(unittest.TestCase):
    def test_all_native_dynamic_reasons_are_accounted_for(self):
        rows=json.loads((ROOT/'data/rules/trade_rejections.json').read_text())['templates']
        self.assertEqual(len(rows),16)
        self.assertEqual(len({r['original'] for r in rows}),16)
        code=(ROOT/'src/trade_rejection.inc').read_text()
        for row in rows:
            self.assertEqual(row['original'].count('%s'),1)
            self.assertEqual(row['translation'].count('%s'),1)
            self.assertIn(row['translation'].replace('%s','%@'),code)
        path=GAME/'Contents/Resources/urw3-bin'
        if path.exists():
            data=path.read_bytes()
            if hashlib.sha256(data).hexdigest()==SUPPORTED_SHA256:
                for row in rows:self.assertIn(row['original'].encode()+b'\0',data)
