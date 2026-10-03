#!/usr/bin/env python3
"""Crop transparent margins from the six Adaptive Behavior button icons."""

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "static/results/behavior/icons"
SOURCES = {
    "fabric-sofa.png": Path("/Users/csy/csy/ZeroCOI/page/obj_render/fabric_sofa.png"),
    "leather-sofa.png": Path("/Users/csy/csy/ZeroCOI/page/obj_render/leather_sofa.png"),
    "chair.png": Path("/Users/csy/csy/ZeroCOI/page/obj_render/chair.png"),
    "male-wild-dog.png": Path("/Users/csy/csy/ZeroCOI/page/dog_render/male_wild_dog.png"),
    "female-wild-dog.png": Path("/Users/csy/csy/ZeroCOI/page/dog_render/female_wild_dog.png"),
    "male-arctic-wolf.png": Path("/Users/csy/csy/ZeroCOI/page/dog_render/male_arctic_wolf.png"),
}


def crop_icon(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGBA")
    box = image.getchannel("A").getbbox()
    if box is None:
        raise RuntimeError(f"No visible pixels found in {source}")
    left, top, right, bottom = box
    padding = max(6, round(max(right - left, bottom - top) * 0.04))
    box = (
        max(0, left - padding),
        max(0, top - padding),
        min(image.width, right + padding),
        min(image.height, bottom + padding),
    )
    image.crop(box).save(destination, optimize=True)
    print(f"{source.name}: {image.size} -> {box[2] - box[0]}x{box[3] - box[1]}")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, source in SOURCES.items():
        crop_icon(source, OUTPUT / name)


if __name__ == "__main__":
    main()
