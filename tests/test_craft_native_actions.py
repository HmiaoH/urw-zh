import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from bind import GAME, SUPPORTED_SHA256


class NativeCraftActionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'data/rules/craft_native_actions.json'
        cls.actions = json.loads(path.read_text())['rows']

    def test_every_native_action_has_display_and_recipe_translations(self):
        translations = {
            (row['context'], row['original'])
            for path in (ROOT / 'data/translations').glob('*.json')
            for row in json.loads(path.read_text())
            if row['status'] == 'reviewed' and row.get('translation')
        }
        names = {row['name'] for row in self.actions}
        self.assertEqual(len(self.actions), 90)
        self.assertEqual(len(names), len(self.actions))
        self.assertEqual(len({row['instruction'] for row in self.actions}), len(self.actions))
        for context in ('showtext', 'craft-recipe'):
            missing = names - {name for candidate, name in translations if candidate == context}
            self.assertFalse(missing, f'{context} missing native actions: {sorted(missing)}')

    def test_source_addresses_match_supported_binary_when_installed(self):
        path = GAME / 'Contents/Resources/urw3-bin'
        if not path.is_file():
            self.skipTest('supported UrW executable is not installed')
        binary = path.read_bytes()
        if hashlib.sha256(binary).hexdigest() != SUPPORTED_SHA256:
            self.skipTest('installed UrW executable has a different build hash')
        # This build's __TEXT has vmaddr 0x100000000 and fileoff zero.
        base = 0x100000000
        for row in self.actions:
            with self.subTest(name=row['name']):
                instruction = int(row['instruction'], 16) - base
                literal = int(row['literal'], 16) - base
                self.assertEqual(binary[instruction:instruction + 3], b'\x48\x8d\x05')
                displacement, = struct.unpack_from('<i', binary, instruction + 3)
                self.assertEqual(instruction + 7 + displacement, literal)
                end = binary.index(b'\0', literal)
                self.assertEqual(binary[literal:end].decode('ascii'), row['name'])
