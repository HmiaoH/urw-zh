#!/usr/bin/env python3
import subprocess
from bind import ROOT,GAME
subprocess.run(['python3','-m','unittest','discover','-s','tests'],cwd=ROOT,check=True)
out=ROOT/'build/urw-zh/runtime-tests'
frameworks=GAME/'Contents/Frameworks'
link=ROOT/'build/Frameworks'
if not link.exists(): link.symlink_to(frameworks,target_is_directory=True)
subprocess.run(['clang++','-std=c++17','-arch','x86_64','-mmacosx-version-min=11.0','-fobjc-arc',str(ROOT/'tests/runtime_test.mm'),'-o',str(out),'-framework','Foundation','-framework','CoreText','-framework','CoreGraphics',str(frameworks/'SDL2.framework/Versions/A/SDL2'),'-Wl,-rpath,'+str(frameworks)],check=True)
subprocess.run([str(out)],check=True)
for name in ('dialogue_extra','profile_armor_look','blacksmith_dialogue'):
    test_out=ROOT/'build'/f'{name}-tests'
    subprocess.run(['clang++','-std=c++17','-fobjc-arc','-framework','Foundation',str(ROOT/'tests'/f'{name}.mm'),'-o',str(test_out)],cwd=ROOT,check=True)
    subprocess.run([str(test_out)],cwd=ROOT,check=True)
