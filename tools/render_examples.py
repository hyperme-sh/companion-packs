"""Render an example pack's editable artwork and original voice lines."""

import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def render(pack):
    source = pack / "source"
    settings = json.loads((source / "render.json").read_text(encoding="utf-8"))
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    for filename, pose in settings["frames"].items():
        svg = ET.parse(source / "mascot.svg").getroot()
        for layer in svg.iter():
            if "data-pose" in layer.attrib:
                layer.set("display", "inline" if layer.attrib["data-pose"] == pose else "none")
        subprocess.run(
            ["rsvg-convert", "--format=png", "--output", str(pack / filename)],
            input=ET.tostring(svg, encoding="utf-8"),
            check=True,
        )
    voice = settings["voice"]
    for filename, words in voice["lines"].items():
        subprocess.run(
            [
                "espeak-ng", "-v", voice["variant"], "-p", str(voice["pitch"]),
                "-s", str(voice["speed"]), "-a", "75", "-z",
                "-w", str(pack / filename), "--", words,
            ],
            check=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packs", nargs="+", type=Path)
    for pack in parser.parse_args().packs:
        render(pack)
