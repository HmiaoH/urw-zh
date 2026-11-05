#!/usr/bin/env python3
"""Change the built module's display language; reopen views or restart to redraw caches."""
import argparse,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('language',choices=['zh','en'])
p.add_argument('--module',type=Path,default=ROOT/'build/urw-zh')
args=p.parse_args();path=args.module/'data/config.json'
config=json.loads(path.read_text());config['enabled']=args.language=='zh'
tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,path)
print('Display language updated; reopen the view or restart the game for cached panels.')
