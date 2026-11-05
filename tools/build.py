#!/usr/bin/env python3
import shutil,subprocess,json
from pathlib import Path
from bind import ROOT,GAME
from validate import load, validate
from validate_items import validate_items
from validate_hypertext import validate_hypertext
from compile_item_rules import compile_rules as compile_item_rules
for compiler in ("compile_dialogue_rules.py","compile_chat_options.py","compile_chat_resources.py","compile_notification_resources.py"):
 subprocess.run(["python3",str(ROOT/"tools"/compiler)],check=True)
errors=validate(load())+validate_hypertext(load())+validate_items(json.loads((ROOT/"data/items.json").read_text()))
if errors: raise SystemExit('\n'.join(errors))
out=ROOT/'build/urw-zh';out.mkdir(parents=True,exist_ok=True)
subprocess.run(['clang++','-std=c++17','-arch','x86_64','-mmacosx-version-min=11.0','-O2','-g','-fobjc-arc','-dynamiclib',str(ROOT/'src/runtime.mm'),'-o',str(out/'liburw_zh.dylib'),'-framework','Foundation','-framework','CoreText','-framework','CoreGraphics','-Wl,-undefined,dynamic_lookup'],check=True)
(out/'data').mkdir(exist_ok=True)
for name in ('config.json','bindings.json','items.json'):
 shutil.copy2(ROOT/'data'/name,out/'data'/name)
(out/'data/items.json').write_text(json.dumps(compile_item_rules(json.loads((ROOT/'data/items.json').read_text())),ensure_ascii=False,indent=2)+'\n')
if (out/'data/translations').exists(): shutil.rmtree(out/'data/translations')
shutil.copytree(ROOT/'data/translations',out/'data/translations')
# Source catalogs and unfinished drafts are development inputs, never runtime payloads.
for name in ('catalog','drafts'):
 if (out/'data'/name).exists(): shutil.rmtree(out/'data'/name)
print(out/'liburw_zh.dylib')
