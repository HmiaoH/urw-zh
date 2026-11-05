import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StatusTextTests(unittest.TestCase):
    def test_finite_status_values_use_their_own_display_contexts(self):
        rows = json.loads((ROOT / "data/translations/status_text.json").read_text())
        descriptions = {
            "status-nutrition": {
                "Starving", "Malnourished", "Insufficient", "Scarce", "Temperate",
                "Good", "Nourished", "Well-fed", "Abundant",
            },
            "status-warmth": {
                "Freezing to death", "Freezing", "Numbingly cold", "Bitterly cold",
                "Cold", "Chilly", "Cool", "Comfortably warm", "Warm", "Rather warm",
                "Hot", "Sweaty", "Sweating a lot",
            },
            "status-vigour": {
                "Vigorous", "Lively", "A bit tired", "Tired", "Weary",
                "Extremely tired", "Ready to drop",
            },
        }
        for context, expected in descriptions.items():
            with self.subTest(context=context):
                self.assertEqual({r["original"] for r in rows if r["context"] == context}, expected)
        self.assertFalse(any(
            r["context"] == "showtext" and r["original"] in {"Good", "Hot", "Tired"}
            for r in rows
        ))

    def test_speed_caption_leaves_native_value_slot_unpainted(self):
        rows = json.loads((ROOT / "data/translations/status_text.json").read_text())
        captions = [r for r in rows if r["source"] == "binary:Heading"]
        self.assertEqual({r["original"] for r in captions}, {"Speed:   mi/h", "Speed:   km/h"})
        # The caption begins at x=8. Heading draws the value at x=58 in
        # its own native two-character call, with a width of 16 pixels.
        for row in captions:
            with self.subTest(source=row["original"]):
                for part in row["segments"]:
                    start = 8 + part["offset"]
                    self.assertTrue(start + part["width"] <= 58 or start >= 74)

    def test_condition_notices_have_matching_log_rows(self):
        rows = json.loads((ROOT / "data/translations/status_text.json").read_text())
        translations = {(r["context"], r["original"]): r["translation"] for r in rows}
        for source in [
            ":You are freezing to death!",
            ":You are getting tired.",
            "&You are very hungry.",
            "&You are dying of thirst!",
        ]:
            with self.subTest(source=source):
                self.assertEqual(
                    translations["message", source],
                    translations["paragraph", source[1:]],
                )


if __name__ == "__main__":
    unittest.main()
