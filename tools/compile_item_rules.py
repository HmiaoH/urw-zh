#!/usr/bin/env python3
"""Compile reviewed item names into forward plural aliases for URW 3.89.1."""
import argparse
import copy
import json
from pathlib import Path

from validate_items import validate_items


def game_plural(name):
    """Mirror mon(char*) for reviewed lowercase English names."""
    if "/" in name:
        return name.partition("/")[2]
    if name.endswith(("fe", "staff")):
        return name[:-2] + "ves"
    if len(name) >= 2 and name.endswith("f") and name[-2] in "lraeiou":
        return name[:-1] + "ves"
    if "tooth" in name and name.endswith("ooth"):
        return name[:-4] + "eeth"
    if "lock of " in name:
        return name.replace("lock of ", "locks of ", 1)
    if name.endswith("x") or (len(name) >= 3 and name.endswith("ch")):
        return name + "es"
    if len(name) >= 3 and name.endswith("ry"):
        return name[:-1] + "ies"
    if not name or name.endswith("s"):
        return name
    return name + "s"


def compile_rules(data):
    errors = validate_items(data)
    if errors:
        raise ValueError("\n".join(errors))

    compiled = copy.deepcopy(data)
    bases = compiled["bases"]
    aliases = compiled["plurals"]

    def register(alias, base):
        if alias == base:
            return
        if alias in bases:
            raise ValueError(f"Plural alias {alias!r} for {base!r} shadows a reviewed base")
        previous = aliases.get(alias)
        if previous is not None and previous != base:
            raise ValueError(f"Conflicting plural alias {alias!r}: {previous!r} and {base!r}")
        aliases[alias] = base

    for alias, base in sorted(aliases.items()):
        register(alias, base)
    for base in sorted(bases):
        if base.isascii():
            register(game_plural(base), base)

    errors = validate_items(compiled)
    if errors:
        raise ValueError("\n".join(errors))
    return compiled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Use a separate path for compiled rules")
        compiled = compile_rules(json.loads(args.input.read_text(encoding="utf-8")))
        args.output.write_text(json.dumps(compiled, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
