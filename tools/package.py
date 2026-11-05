#!/usr/bin/env python3
"""Build a game-free macOS localization installer archive."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from bind import ROOT, SUPPORTED_SHA256

NAME = 'URW-ZH-3.89.1-macOS-x86_64'
out = ROOT/'build/release'
stage = out/NAME
if stage.exists():
    shutil.rmtree(stage)
(stage/'tools').mkdir(parents=True)
module = ROOT/'build/urw-zh'
shutil.copy2(module/'liburw_zh.dylib', stage/'liburw_zh.dylib')
shutil.copytree(module/'data', stage/'data')
(stage/'data/config.json').write_text('{"enabled": true, "capture": false}\n')
for name in ('install.py', 'steam_launch.py'):
    shutil.copy2(ROOT/'tools'/name, stage/'tools'/name)
# Portable constants only: no development paths or game extraction tooling.
(stage/'tools/bind.py').write_text('from pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nGAME=Path.home()/"Library/Application Support/Steam/steamapps/common/UnRealWorld/UrW.app"\nSUPPORTED_SHA256='+repr(SUPPORTED_SHA256)+'\n')
(stage/'tools/manage.py').write_text('''import argparse
from pathlib import Path
import subprocess
from bind import GAME, ROOT
from install import operate as module_action
from steam_launch import operate as steam_action, options

p=argparse.ArgumentParser()
p.add_argument('action', choices=['install','uninstall'])
p.add_argument('--app', type=Path, default=GAME)
p.add_argument('--config', type=Path)
a=p.parse_args()
for process in ('steam_osx','urw3-bin'):
    if subprocess.run(['pgrep','-x',process],capture_output=True).returncode==0:
        raise SystemExit('请先正常退出 UnReal World 和原生 macOS Steam，再运行安装或卸载。')
if not a.app.exists():
    raise SystemExit('找不到默认 Steam 游戏路径；可使用 --app 指定 UrW.app。')
record=a.app/'Contents/urw-zh-backup/steam-options.json'
if a.config:
    config=a.config
elif record.exists():
    import json
    config=Path(json.loads(record.read_text())['config'])
else:
    candidates=[]
    for path in (Path.home()/'Library/Application Support/Steam/userdata').glob('*/config/localconfig.vdf'):
        try: options(path.read_text()); candidates.append(path)
        except (ValueError,OSError): pass
    if len(candidates)!=1:
        raise SystemExit('未能唯一识别 Steam 账户；请运行 tools/manage.py 并用 --config 指定 localconfig.vdf。')
    config=candidates[0]
if a.action=='install':
    # Validate both surfaces before modifying either one.
    old,_=options(config.read_text())
    if old and not record.exists():
        raise SystemExit('已有自定义启动选项，保留原值；请手动合并后安装。')
    module_action('install',a.app,ROOT,dry_run=True)
    was_active=module_action('status',a.app,ROOT)['active']
    print(module_action('install',a.app,ROOT))
    try: print(steam_action('install',config,a.app))
    except Exception:
        if not was_active: module_action('uninstall',a.app,ROOT)
        raise
    print('安装完成。请打开 Steam，点击 UnReal World 的开始游戏。')
else:
    module_action('uninstall',a.app,ROOT,dry_run=True)
    print(steam_action('uninstall',config,a.app))
    print(module_action('uninstall',a.app,ROOT))
    print('卸载完成，原启动选项与应用启动脚本已恢复。')
''')
for filename, action in [('安装汉化.command','install'),('卸载汉化.command','uninstall')]:
    path=stage/filename
    path.write_text('''#!/bin/bash
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
    echo "需要 Python 3；请安装后再运行。"
else
    python3 tools/manage.py ACTION
fi
result=$?
echo "按回车关闭窗口。"
read -r
exit "$result"
'''.replace('ACTION',action))
    path.chmod(0o755)
(stage/'使用说明.txt').write_text('''URW 3.89.1 macOS 简体中文汉化安装包

适用：Steam macOS x86_64 3.89.1，Apple Silicon 需 Rosetta。
需要系统可用的 Python 3。本包未进行 Apple Developer ID 签名或公证。

1. 正常退出游戏与原生 macOS Steam。
2. 解压后双击“安装汉化.command”。
3. 安装完成后，从 Steam 库点击 UnReal World 的“开始游戏”。

卸载：退出游戏与 Steam 后，双击“卸载汉化.command”。
安装器保留原启动脚本和该游戏的原启动选项，卸载时按当前状态校验后恢复；
不会用整份旧 Steam 配置覆盖新的设置。重复安装不覆盖现有汉化配置。
升级汉化包请先卸载旧版再安装新版。
备份位置：UrW.app/Contents/urw-zh-backup。

自定义游戏路径或多个 Steam 账户：
python3 tools/manage.py install --app "/路径/UrW.app" --config "/路径/localconfig.vdf"
卸载时将 install 换成 uninstall。

英文切换：把 UrW.app/Contents/Resources/urw-zh/data/config.json
中的 enabled 改为 false，再退出重启游戏。capture 默认为 false。
游戏版本 SHA-256 不匹配时，启动入口保留原版英文启动。

本包不包含游戏本体、游戏美术音频、角色存档或调试日志。
只改变显示，保留英文输入、名字与快捷键；未实施高清渲染改写。
汉化仍有漏译及低分辨率显示限制，不代表完整游戏验收通过。
''')
(stage/'第三方与字体说明.txt').write_text('''本包需要用户自行购买安装 UnReal World；游戏及其素材权利归原权利人。
本汉化为非官方显示适配，未获声明为官方产品。
中文使用 macOS 自带苹方字体，通过 CoreText 调用；本包不复制或分发 Apple 字体。
SDL2 由已安装的游戏提供，本包不另行分发 SDL2。
翻译词表中包含用于匹配的原文；原文权利归原游戏权利人。
此包为当前本机用户测试安装包，不附带对第三方素材的再分发授权。
''')
files={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob('*')) if p.is_file()}
(stage/'manifest.json').write_text(json.dumps(dict(game_sha256=SUPPORTED_SHA256,files=files),indent=2)+'\n')
archive=out/(NAME+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in sorted(stage.rglob('*')):
        if path.is_file(): z.write(path,str(Path(NAME)/path.relative_to(stage)))
(archive.with_suffix('.zip.sha256')).write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(archive)
