#!/usr/bin/env python3
"""Read URW 3.89.1 item-name tables and verify the inventory cut call site."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from bind import GAME, SUPPORTED_SHA256, inspect


def analyze(path):
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SUPPORTED_SHA256:
        raise ValueError(f"Unsupported urw3-bin SHA-256: {digest}")
    data, segments, _, symbols = inspect(path)

    def at(address, size):
        for va, _, offset, length in segments:
            if va <= address and address + size <= va + length:
                start = offset + address - va
                return data[start : start + size]
        raise ValueError(f"Unmapped {address:#x} (+{size:#x})")

    def unpack(address, form):
        return struct.unpack(form, at(address, struct.calcsize(form)))

    def c_string(address, limit=128):
        before, sep, _ = at(address, limit).partition(b"\0")
        if not sep:
            raise ValueError(f"No terminator at {address:#x}")
        return before.decode("ascii")

    def switch(address, n):
        return [hex(address + rel) for rel in unpack(address, f"<{n}i")]

    quality_symbols = {
        "weapon": "_laatuluokitus_ase",
        "arrow": "_laatuluokitus_nuoli",
        "clothing": "_laatuluokitus_vaate",
        "container": "_laatuluokitus_astia",
        "food": "_laatuluokitus_ruoka",
        "default": "_laatuluokitus_def",
        "pelt": "_laatuluokitus_talja",
    }
    by_address = {symbols[symbol]: category for category, symbol in quality_symbols.items()}
    quality = {
        category: {
            "address": hex(symbols[symbol]),
            "labels": [c_string(ptr) for ptr in unpack(symbols[symbol], "<5Q")],
        }
        for category, symbol in quality_symbols.items()
    }
    measures = "kourallinen hyppysellinen tukku kasa kera levy kimppu".split()
    plants = "korsi heinakasvi marjapuska marja papu juures siemen jyva lehti kukka viljakasvi sieni kasvi kasvinosa jauhoja".split()
    site = 0x100069389
    opcode, displacement = unpack(site, "<Bi")
    target = site + 5 + displacement
    if opcode != 0xE8 or target != symbols["__Z9strmaxcutPci"]:
        raise ValueError("Inventory cut is not a rel32 call to strmaxcut")
    return {
        "sha256": digest,
        "quality": quality,
        "quality_categories_1_to_7": [by_address[ptr] for ptr in unpack(0x1002381A8, "<7Q")],
        "measure_labels": {key: c_string(symbols[f"_YM_{key}"], 32) for key in measures},
        "plant_labels": {key: c_string(symbols[f"_YM_{key}"], 32) for key in plants},
        "measure_case_targets": switch(0x10004BA28, 9),
        "plant_case_targets_0x1ad_to_0x201": switch(0x10004E6A4, 85),
        "wood_species_case_targets_1_to_6": switch(0x1001B5514, 6),
        "inventory_cut": {
            "site": hex(site),
            "call_bytes": at(site, 5).hex(),
            "target": hex(target),
            "return_address": hex(site + 5),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", nargs="?", type=Path, default=GAME / "Contents/Resources/urw3-bin")
    args = parser.parse_args()
    try:
        print(json.dumps(analyze(args.binary), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
