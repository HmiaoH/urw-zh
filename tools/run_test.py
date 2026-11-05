#!/usr/bin/env python3
"""Run against an isolated writable home. No existing characters are loaded or copied."""
import argparse,hashlib,os,plistlib,subprocess,shutil
from pathlib import Path
from bind import ROOT,GAME
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--english',action='store_true',help='Run without loading the localization library')
parser.add_argument('--prepare-only',action='store_true')
args=parser.parse_args()
home=ROOT/'build/test-home';home.mkdir(parents=True,exist_ok=True)
resources=GAME/'Contents/Resources'
for p in resources.iterdir():
 dest=home/p.name
 if p.name in ['urw','urw3-bin']:continue
 if dest.is_symlink():
  if dest.resolve()!=p.resolve():raise SystemExit(f'Unexpected test link: {dest}')
  dest.unlink()
 if not dest.exists():
  if p.is_dir():shutil.copytree(p,dest)
  else:shutil.copy2(p,dest)
app=ROOT/'build/UrW-ZH-Test.app/Contents';(app/'MacOS').mkdir(parents=True,exist_ok=True)
binary=app/'MacOS/urw3-bin';source=resources/'urw3-bin'
if not binary.exists() or hashlib.sha256(binary.read_bytes()).digest()!=hashlib.sha256(source.read_bytes()).digest():shutil.copy2(source,binary)
(app/'Info.plist').write_bytes(plistlib.dumps(dict(CFBundleExecutable='urw3-bin',CFBundleIdentifier='local.urw.zh.test',CFBundleName='UrW-ZH-Test',CFBundlePackageType='APPL')))
frameworks=app/'Frameworks'
if not frameworks.exists():frameworks.symlink_to(GAME/'Contents/Frameworks',target_is_directory=True)
print(f'Test app: {app.parent}\nIsolated data: {home}',flush=True)
if args.prepare_only:raise SystemExit(0)
env=dict(os.environ)
env.pop('DYLD_INSERT_LIBRARIES',None)
if not args.english:env['DYLD_INSERT_LIBRARIES']=str(ROOT/'build/urw-zh/liburw_zh.dylib')
raise SystemExit(subprocess.call([str(binary)],cwd=home,env=env))
