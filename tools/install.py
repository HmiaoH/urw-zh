#!/usr/bin/env python3
"""Install/restore the Steam launcher with hash-checked backups."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from bind import GAME, ROOT, SUPPORTED_SHA256

COMMAND = '    "${URW_BIN_DIR}"/"${URW_BIN}"'
WRAPPER = '''    # BEGIN URW-ZH managed launcher
    URW_ZH_DIR="${URW_APP_LOCATION}/Resources/urw-zh"
    URW_ZH_HASH=$(/usr/bin/shasum -a 256 "${URW_BIN_DIR}/${URW_BIN}" 2>/dev/null)
    URW_ZH_HASH=${URW_ZH_HASH%% *}
    if [ "${URW_ZH_HASH}" = "EXPECTED_HASH" ] && [ -r "${URW_ZH_DIR}/liburw_zh.dylib" ] && [ -r "${URW_ZH_DIR}/data/bindings.json" ]; then
        /usr/bin/env DYLD_INSERT_LIBRARIES="${URW_ZH_DIR}/liburw_zh.dylib${DYLD_INSERT_LIBRARIES:+:${DYLD_INSERT_LIBRARIES}}" "${URW_BIN_DIR}/${URW_BIN}"
    else
        "${URW_BIN_DIR}/${URW_BIN}"
    fi
    # END URW-ZH managed launcher'''.replace('EXPECTED_HASH', SUPPORTED_SHA256)

def digest(data): return hashlib.sha256(data).hexdigest()

def atomic(path, data, mode=0o644):
    fd, tmp = tempfile.mkstemp(prefix='.urw-zh-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(tmp,mode);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def operate(action, app, module, dry_run=False):
    contents=app/'Contents';launcher=contents/'MacOS/UrW'
    backup=contents/'urw-zh-backup';manifest=backup/'manifest.json'
    destination=contents/'Resources/urw-zh'
    current=launcher.read_bytes();state=json.loads(manifest.read_text()) if manifest.exists() else None
    active=state is not None and state['active']
    if action=='status':return dict(active=active,launcher_matches=bool(active and digest(current)==state['installed_sha256']))
    if active:
        if digest(current)!=state['installed_sha256']:raise ValueError('Launcher changed after installation; refusing to overwrite Steam or user changes.')
        original=(backup/'UrW.original').read_bytes()
        if digest(original)!=state['original_sha256']:raise ValueError('Backup hash mismatch; refusing restoration.')
    if action=='uninstall':
        if not active:return {'result':'already uninstalled'}
        if dry_run:return {'result':'would restore verified original launcher'}
        atomic(launcher,original,state['mode'])
        # Retain local config and logs, rather than deleting user changes.
        if destination.exists():destination.rename(backup/('retired-module-'+uuid.uuid4().hex[:8]))
        state['active']=False;atomic(manifest,(json.dumps(state,indent=2)+'\n').encode())
        return {'result':'original launcher restored; module retained in backup directory'}
    binary=contents/'Resources/urw3-bin'
    if digest(binary.read_bytes())!=SUPPORTED_SHA256:raise ValueError('Unsupported game binary; launcher left untouched.')
    if active:return {'result':'already installed'}
    if destination.exists():raise ValueError('Unmanaged urw-zh directory exists; refusing to overwrite it.')
    text=current.decode('utf-8')
    if text.splitlines().count(COMMAND)!=1 or 'BEGIN URW-ZH' in text:raise ValueError('Unrecognized launcher structure; refusing modification.')
    bindings=json.loads((module/'data/bindings.json').read_text())
    if bindings.get('sha256')!=SUPPORTED_SHA256 or not (module/'liburw_zh.dylib').is_file():raise ValueError('Missing or incompatible built module.')
    modified=text.replace(COMMAND,WRAPPER).encode()
    if dry_run:return {'result':'would install module and patch one game launch command','launcher_sha256':digest(current),'installed_sha256':digest(modified)}
    backup.mkdir(exist_ok=True)
    staged=contents/'Resources'/('.urw-zh-stage-'+uuid.uuid4().hex)
    published=False
    try:
        staged.mkdir();shutil.copy2(module/'liburw_zh.dylib',staged/'liburw_zh.dylib');shutil.copytree(module/'data',staged/'data')
        if launcher.read_bytes()!=current:raise ValueError('Launcher changed during preparation; aborting.')
        atomic(backup/'UrW.original',current,launcher.stat().st_mode & 0o777)
        state=dict(active=True,original_sha256=digest(current),installed_sha256=digest(modified),mode=launcher.stat().st_mode & 0o777)
        # Write the recovery record before replacing the launcher.
        atomic(manifest,(json.dumps(state,indent=2)+'\n').encode())
        staged.rename(destination)
        published=True
        atomic(launcher,modified,state['mode'])
    except Exception:
        # Restore only if the launcher still has one of our known states.
        if launcher.read_bytes()==modified:atomic(launcher,current,state['mode'])
        if published and destination.exists():destination.rename(backup/('failed-module-'+uuid.uuid4().hex[:8]))
        if state and manifest.exists():
            state['active']=False;atomic(manifest,(json.dumps(state,indent=2)+'\n').encode())
        raise
    finally:
        if staged.exists():shutil.rmtree(staged)
    return {'result':'installed','backup':str(backup)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['install','uninstall','status'])
    p.add_argument('--app',type=Path,default=GAME);p.add_argument('--module',type=Path,default=ROOT/'build/urw-zh');p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    try:print(json.dumps(operate(a.action,a.app,a.module,a.dry_run),ensure_ascii=False,indent=2))
    except (ValueError,OSError) as e:raise SystemExit(str(e))
