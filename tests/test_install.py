import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import install

class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        self.app=root/'Game.app';self.contents=self.app/'Contents'
        (self.contents/'MacOS').mkdir(parents=True);(self.contents/'Resources').mkdir()
        self.launcher=self.contents/'MacOS/UrW';self.original=('#!/bin/bash\n'+install.COMMAND+'\n').encode();self.launcher.write_bytes(self.original);self.launcher.chmod(0o755)
        (self.contents/'Resources/urw3-bin').write_bytes(b'test binary')
        self.module=root/'module';(self.module/'data').mkdir(parents=True)
        self.sha=install.digest(b'test binary');(self.module/'data/bindings.json').write_text(json.dumps({'sha256':self.sha}));(self.module/'liburw_zh.dylib').write_bytes(b'test module')
        self.override=patch.object(install,'SUPPORTED_SHA256',self.sha);self.override.start()
    def tearDown(self):self.override.stop();self.temp.cleanup()
    def run_action(self,action,**kw):return install.operate(action,self.app,self.module,**kw)
    def test_install_repeat_restore(self):
        self.run_action('install');installed=self.launcher.read_bytes()
        self.assertIn(b'BEGIN URW-ZH',installed)
        self.run_action('install');self.assertEqual(installed,self.launcher.read_bytes())
        self.run_action('uninstall');self.assertEqual(self.original,self.launcher.read_bytes())
        self.assertEqual(self.launcher.stat().st_mode & 0o777,0o755)
        self.run_action('uninstall');self.run_action('install')
    def test_dry_run(self):
        self.run_action('install',dry_run=True);self.assertEqual(self.original,self.launcher.read_bytes());self.assertFalse((self.contents/'urw-zh-backup').exists())
    def test_updated_launcher(self):
        self.run_action('install');self.launcher.write_bytes(b'updated by Steam')
        with self.assertRaises(ValueError):self.run_action('uninstall')
        self.assertEqual(self.launcher.read_bytes(),b'updated by Steam')
    def test_corrupt_backup(self):
        self.run_action('install');(self.contents/'urw-zh-backup/UrW.original').write_bytes(b'bad backup')
        with self.assertRaises(ValueError):self.run_action('uninstall')
    def test_unknown_binary(self):
        (self.contents/'Resources/urw3-bin').write_bytes(b'new version')
        with self.assertRaises(ValueError):self.run_action('install')
        self.assertEqual(self.original,self.launcher.read_bytes())
    def test_publication_failure(self):
        original_atomic=install.atomic
        def fail(path,data,mode=0o644):
            if path==self.launcher:raise OSError('simulated write failure')
            original_atomic(path,data,mode)
        with patch.object(install,'atomic',side_effect=fail):
            with self.assertRaises(OSError):self.run_action('install')
        self.assertEqual(self.original,self.launcher.read_bytes())
        self.assertFalse((self.contents/'Resources/urw-zh').exists())
        self.run_action('install')

if __name__=='__main__':unittest.main()
