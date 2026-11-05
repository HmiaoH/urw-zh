"""Export statically verified navigation dialogue candidates for UrW 3.89.1."""

import hashlib
import json
import struct
from bind import SUPPORTED_SHA256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "build/UrW-ZH-Test.app/Contents/MacOS/urw3-bin"
IMAGE_BASE = 0x100000000
CSTRING_START = 0x1001E7EB0
CSTRING_END = CSTRING_START + 0x4DD94
CULTURE_TABLE = 0x10023C850
DIRECTION_TABLE = 0x10023ED20


def pointer_table(image, address, count):
    entries = []
    for index, pointer in enumerate(
        struct.unpack_from(f"<{count}Q", image, address - IMAGE_BASE)
    ):
        if not CSTRING_START <= pointer < CSTRING_END:
            raise ValueError(f"Unexpected cstring pointer at {address:#x}[{index}]")
        offset = pointer - IMAGE_BASE
        value = image[offset : image.index(b"\0", offset, CSTRING_END - IMAGE_BASE)]
        entries.append(
            {
                "index": index,
                "address": hex(pointer),
                "source_bytes_hex": value.hex(),
                "source": value.decode("ascii", errors="backslashreplace"),
            }
        )
    return entries


def main():
    image = BINARY.read_bytes()
    if hashlib.sha256(image).hexdigest() != SUPPORTED_SHA256:
        raise ValueError("Unsupported URW binary")
    directions = pointer_table(image, DIRECTION_TABLE, 8)
    cultures = pointer_table(image, CULTURE_TABLE, 14)
    if [entry["source"] for entry in directions] != [
        "east", "north-east", "north", "north-west", "west",
        "south-west", "south", "south-east",
    ]:
        raise ValueError("Unexpected _Ilmansuunta table")
    if cultures[7]["source"] != "kuikka-tribe":
        raise ValueError("Unexpected _CULTURE_ADJECTIVE table")
    for entry, target in zip(directions, [
        "东", "东北", "北", "西北", "西", "西南", "南", "东南",
    ]):
        entry["target"] = target
    cultures[7]["target"] = "库伊卡部族"

    distances = []
    for unit, singular, addresses, target_unit in [
        ("kilometers", "kilometer", ["0x1000ba384", "0x1000ba3ae",
            "0x1000ba3d7", "0x1000ba475"], "公里"),
        ("miles", "mile", ["0x1000ba3f7", "0x1000ba41d",
            "0x1000ba43c", "0x1000ba499"], "英里"),
    ]:
        for source, target, address in zip(
            [
                f"about {{amount:uint}} {unit}",
                f"less than a {singular}",
                f"half a {singular}",
                f"just a couple of {unit}",
            ],
            [f"约{{amount}}{target_unit}", f"不到一{target_unit}",
                f"半{target_unit}", f"只有几{target_unit}"],
            addresses,
        ):
            distances.append(
                {"source": source, "target": target, "source_instruction": address}
            )

    output = {
        "version": 1,
        "game_version": "3.89.1",
        "binary_sha256": hashlib.sha256(image).hexdigest(),
        "development_only": True,
        "source_family": "hardcoded-native",
        "display_context": "npc-talk",
        "producer": "PARSE_EtsimassahPci",
        "evidence": {
            "direction_table": hex(DIRECTION_TABLE),
            "direction_lookup": "0x100187d0d",
            "culture_table": hex(CULTURE_TABLE),
            "culture_lookup": "0x100187da1",
            "distance_flags_9": "0x1001b6307",
            "distance_no_walk_branch": "0x1000ba4b6",
            "distance_away_suffix": "0x1000ba6c8",
            "region_description": "0x1001b6190",
        },
        "maps": {
            "direction": directions,
            "culture": cultures,
            "place_type": [
                {"source": "settlement", "target": "一处聚落",
                    "source_instructions": ["0x10018d7ea", "0x10018d828"]},
                {"source": "lake", "target": "一片湖泊",
                    "source_instructions": ["0x10018d869"]},
                {"source": "cave", "target": "一处洞穴",
                    "source_instructions": ["0x10018d8d7"]},
            ],
            "distance": distances,
        },
        "templates": [
            {
                "source": "There is a {type:place_type} in the {direction:direction} at the region called {place:text}.",
                "target": "在{direction}方名叫 {place} 的地区有{type}。",
                "source_instructions": ["0x100187d30", "0x1001b624f"],
                "display_call": "0x100187d54",
            },
            {
                "source": "There is a {type:place_type} in the {direction:direction} here at {place:text}.",
                "target": "就在这一带的 {place}，往{direction}方有{type}。",
                "source_instructions": ["0x100187d30", "0x1001b625f"],
                "display_call": "0x100187d54",
            },
            {
                "source": "It is {distance:distance} away.",
                "target": "离这里{distance}。",
                "source_instructions": ["0x100187d67", "0x1000ba6c8"],
                "display_call": "0x100187d7e",
            },
            {
                "source": "It is {culture:culture} village.",
                "target": "那是{culture}的村庄。",
                "source_instructions": ["0x100187dac"],
                "display_call": "0x100187dc7",
                "require_mapped_value": True,
            },
        ],
        "observed_english_examples": [
            'There is a settlement in the south-west at the region called Nuokkukallio "Nodcliff".',
            "It is just a couple of miles away.",
            "It is kuikka-tribe village.",
        ],
    }
    path = ROOT / "build/dialogue-rule-candidates.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(path)


if __name__ == "__main__":
    main()
