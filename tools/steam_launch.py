#!/usr/bin/env python3
"""Manage URW-only Steam launch options. Run while native Steam is closed."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from bind import GAME, SUPPORTED_SHA256
from install import atomic


def app_block(text):
    tokens = list(re.finditer(r'"(?:\\.|[^"\\])*"|[{}]', text))
    stack = []
    pending = None
    for i, token in enumerate(tokens):
        value = token.group()
        if value == '{':
            stack.append((pending, token.end()))
            pending = None
        elif value == '}':
            name, start = stack.pop()
            if name == '351700' and stack and stack[-1][0].lower() == 'apps':
                return start, token.start()
            pending = None
        elif i + 1 < len(tokens) and tokens[i + 1].group() == '{':
            pending = json.loads(value)
    raise ValueError('URW app settings block not found')


def options(text):
    start, end = app_block(text)
    match = re.search(r'"LaunchOptions"\s*("(?:\\.|[^"\\])*")', text[start:end], re.I)
    return (json.loads(match[1]) if match else None,
            (start + match.start(), start + match.end()) if match else (end, end))


def replace_options(text, value):
    old, (start, end) = options(text)
    replacement = '' if value is None else '"LaunchOptions"\t\t' + json.dumps(value, ensure_ascii=False)
    if start == end and replacement:
        replacement = '\n\t\t\t\t\t\t' + replacement + '\n\t\t\t\t\t'
    return text[:start] + replacement + text[end:]


def operate(action, config, app=GAME):
    if subprocess.run(['pgrep', '-x', 'steam_osx'], capture_output=True).returncode == 0:
        raise ValueError('Quit native Steam before changing launch options')
    backup = app/'Contents/urw-zh-backup'
    backup.mkdir(exist_ok=True)
    record = backup/'steam-options.json'
    wrapper = backup/'steam-launch.sh'
    text = config.read_text()
    old, _ = options(text)
    state = json.loads(record.read_text()) if record.exists() else None
    if state and state['active']:
        if str(config.resolve()) != state['config'] or old != state['installed']:
            raise ValueError('Steam launch options changed; refusing overwrite')
        if action == 'install':
            return {'result': 'already installed'}
        atomic(config, replace_options(text, state['original']).encode(), config.stat().st_mode & 0o777)
        state['active'] = False
        atomic(record, (json.dumps(state, indent=2)+'\n').encode())
        return {'result': 'original Steam launch options restored'}
    if action == 'uninstall':
        return {'result': 'already uninstalled'}
    if old:
        raise ValueError('Existing launch options need explicit integration; left unchanged')
    # Keep this small wrapper in the retained backup directory, so uninstalling
    # the module still leaves Steam able to start the original executable.
    script = '''#!/bin/bash
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MODULE="$ROOT/Resources/urw-zh"
if [ "$#" -eq 0 ]; then exit 64; fi
HASH=$(/usr/bin/shasum -a 256 "$1" 2>/dev/null || true)
HASH=${HASH%% *}
if [ "$HASH" = "EXPECTED" ] && [ -r "$MODULE/liburw_zh.dylib" ] && [ -r "$MODULE/data/bindings.json" ]; then
    export DYLD_INSERT_LIBRARIES="$MODULE/liburw_zh.dylib${DYLD_INSERT_LIBRARIES:+:$DYLD_INSERT_LIBRARIES}"
fi
exec "$@"
'''.replace('EXPECTED', SUPPORTED_SHA256)
    atomic(wrapper, script.encode(), 0o755)
    launch = '"' + str(wrapper) + '" %command%'
    state = dict(active=True, config=str(config.resolve()), original=old, installed=launch)
    atomic(backup/'localconfig.before-steam-options.vdf', text.encode(), 0o600)
    atomic(record, (json.dumps(state, indent=2)+'\n').encode(), 0o600)
    atomic(config, replace_options(text, launch).encode(), config.stat().st_mode & 0o777)
    return {'result': 'installed', 'launch_options': launch}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'uninstall'])
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(operate(args.action, args.config), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as e:
        raise SystemExit(str(e))
