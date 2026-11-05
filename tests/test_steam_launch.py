import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import steam_launch as steam

VDF='"root" { "apps" { "351700" { "Playtime" "6" } "123" { "LaunchOptions" "keep" } } }'
class SteamLaunchTest(unittest.TestCase):
    def test_quoted_path_roundtrip(self):
        value='"/a b/启动.sh" %command%'
        updated=steam.replace_options(VDF,value)
        self.assertEqual(steam.options(updated)[0],value)
        self.assertIn('"LaunchOptions" "keep"',updated)
        self.assertIsNone(steam.options(steam.replace_options(updated,None))[0])
    def test_lifecycle_and_preserve_other_changes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(steam.subprocess,'run') as run:
            run.return_value.returncode=1
            root=Path(tmp);app=root/'Game.app';(app/'Contents').mkdir(parents=True)
            config=root/'localconfig.vdf';config.write_text(VDF)
            steam.operate('install',config,app)
            self.assertEqual(steam.operate('install',config,app)['result'],'already installed')
            config.write_text(config.read_text().replace('"6"','"99"'))
            steam.operate('uninstall',config,app)
            self.assertIsNone(steam.options(config.read_text())[0])
            self.assertIn('"99"',config.read_text())
    def test_user_modified_options_protected(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(steam.subprocess,'run') as run:
            run.return_value.returncode=1
            root=Path(tmp);app=root/'Game.app';(app/'Contents').mkdir(parents=True)
            config=root/'localconfig.vdf';config.write_text(VDF)
            steam.operate('install',config,app)
            config.write_text(steam.replace_options(config.read_text(),'user custom'))
            with self.assertRaises(ValueError):steam.operate('uninstall',config,app)
            self.assertEqual(steam.options(config.read_text())[0],'user custom')
    def test_running_client_protected(self):
        with patch.object(steam.subprocess,'run') as run:
            run.return_value.returncode=0
            with self.assertRaises(ValueError):steam.operate('install',Path('/unused'))
