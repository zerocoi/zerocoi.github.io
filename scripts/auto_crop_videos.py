#!/usr/bin/env python3
"""Conservatively remove persistent near-white margins from result videos.

The detector samples multiple frames, takes the union of all visible content,
adds a safety margin, and expands the box to 16:9 before encoding. Originals
are never modified.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "static/results/videos"
OUTPUT_DIR = ROOT / "static/results/videos-cropped"
SAMPLE_WIDTH = 320
SAMPLE_FPS = 15
WHITE_THRESHOLD = 240
SAFETY_FRACTION = 0.05


def find_ffmpeg() -> Path:
    configured = os.environ.get("FFMPEG")
    if configured:
        return Path(configured)
    candidates = list((ROOT / ".tools/imageio_ffmpeg/binaries").glob("ffmpeg-*"))
    if candidates:
        return candidates[0]
    executable = shutil.which("ffmpeg")
    if executable:
        return Path(executable)
    raise SystemExit("FFmpeg was not found. Set FFMPEG=/path/to/ffmpeg.")


def video_size(ffmpeg: Path, source: Path) -> tuple[int, int]:
    probe = subprocess.run(
        [str(ffmpeg), "-hide_banner", "-i", str(source)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    ).stderr
    match = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", probe)
    if not match:
        raise RuntimeError(f"Could not read dimensions for {source.name}")
    return int(match.group(1)), int(match.group(2))


def sampled_bounds(ffmpeg: Path, source: Path, width: int, height: int) -> tuple[float, float, float, float]:
    sample_height = max(2, round((height * SAMPLE_WIDTH / width) / 2) * 2)
    command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-vf", f"fps={SAMPLE_FPS},scale={SAMPLE_WIDTH}:{sample_height}",
        "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1",
    ]
    raw = subprocess.check_output(command)
    frame_size = SAMPLE_WIDTH * sample_height * 3
    frame_count = len(raw) // frame_size
    if frame_count == 0:
        raise RuntimeError(f"No frames decoded from {source.name}")

    min_x, min_y = SAMPLE_WIDTH, sample_height
    max_x = max_y = -1
    row_minimum = max(2, round(SAMPLE_WIDTH * 0.006))
    column_minimum = max(2, round(sample_height * 0.006))

    for frame_index in range(frame_count):
        frame = memoryview(raw)[frame_index * frame_size:(frame_index + 1) * frame_size]
        row_counts = [0] * sample_height
        column_counts = [0] * SAMPLE_WIDTH
        for y in range(sample_height):
            row_offset = y * SAMPLE_WIDTH * 3
            for x in range(SAMPLE_WIDTH):
                offset = row_offset + x * 3
                if min(frame[offset], frame[offset + 1], frame[offset + 2]) < WHITE_THRESHOLD:
                    row_counts[y] += 1
                    column_counts[x] += 1

        active_rows = [y for y, count in enumerate(row_counts) if count >= row_minimum]
        active_columns = [x for x, count in enumerate(column_counts) if count >= column_minimum]
        if active_rows and active_columns:
            min_x = min(min_x, active_columns[0])
            max_x = max(max_x, active_columns[-1])
            min_y = min(min_y, active_rows[0])
            max_y = max(max_y, active_rows[-1])

    if max_x < min_x or max_y < min_y:
        return 0.0, 0.0, float(width), float(height)

    scale_x, scale_y = width / SAMPLE_WIDTH, height / sample_height
    x0, x1 = min_x * scale_x, (max_x + 1) * scale_x
    y0, y1 = min_y * scale_y, (max_y + 1) * scale_y
    x0 -= width * SAFETY_FRACTION
    x1 += width * SAFETY_FRACTION
    y0 -= height * SAFETY_FRACTION
    y1 += height * SAFETY_FRACTION
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(width, x1), min(height, y1)

    return x0, y0, x1 - x0, y1 - y0


def even_crop(
    bounds: tuple[float, float, float, float], width: int, height: int
) -> tuple[int, int, int, int]:
    """Round a safe floating-point box outwards to encoder-compatible values."""
    x0, y0, box_width, box_height = bounds
    crop_x = max(0, int(x0) // 2 * 2)
    crop_y = max(0, int(y0) // 2 * 2)
    x1 = min(width, (int(x0 + box_width + 1) + 1) // 2 * 2)
    y1 = min(height, (int(y0 + box_height + 1) + 1) // 2 * 2)
    return crop_x, crop_y, x1 - crop_x, y1 - crop_y


def encode(ffmpeg: Path, source: Path, destination: Path, crop: tuple[int, int, int, int]) -> None:
    x, y, width, height = crop
    command = [
        str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
        "-vf", f"crop={width}:{height}:{x}:{y}",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(destination),
    ]
    subprocess.run(command, check=True)


def scene_key(source: Path) -> str:
    stem = source.stem
    for suffix in ("_animate", "_david", "_tst"):
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break
    return "stand" if stem == "stand_up" else stem


def main() -> None:
    ffmpeg = find_ffmpeg()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, object]] = {}
    sources = sorted(SOURCE_DIR.glob("*.mp4"))
    if not sources:
        raise SystemExit(f"No MP4 files found in {SOURCE_DIR}")

    detected: dict[Path, tuple[int, int, tuple[float, float, float, float]]] = {}
    for source in sources:
        width, height = video_size(ffmpeg, source)
        bounds = sampled_bounds(ffmpeg, source, width, height)
        detected[source] = (width, height, bounds)

    # The four methods in each carousel slide share one exact crop. The crop is
    # the union of their independently detected content boxes, so alignment is
    # perfect and no method-specific motion is lost.
    grouped = {scene_key(source) for source in sources}
    group_crops: dict[str, tuple[int, int, int, int]] = {}
    for key in grouped:
        members = [values for source, values in detected.items() if scene_key(source) == key]
        dimensions = {(width, height) for width, height, _ in members}
        if len(dimensions) != 1:
            raise RuntimeError(f"Videos in group {key!r} do not share one resolution")
        width, height = next(iter(dimensions))
        x0 = min(bounds[0] for _, _, bounds in members)
        y0 = min(bounds[1] for _, _, bounds in members)
        x1 = max(bounds[0] + bounds[2] for _, _, bounds in members)
        y1 = max(bounds[1] + bounds[3] for _, _, bounds in members)
        group_crops[key] = even_crop((x0, y0, x1 - x0, y1 - y0), width, height)
    print("Group crops:", ", ".join(f"{key}={value}" for key, value in sorted(group_crops.items())))

    for source in sources:
        width, height, bounds = detected[source]
        crop = group_crops[scene_key(source)]
        destination = OUTPUT_DIR / source.name
        encode(ffmpeg, source, destination, crop)
        x, y, crop_width, crop_height = crop
        removed = 1 - (crop_width * crop_height) / (width * height)
        manifest[source.name] = {
            "source": [width, height],
            "crop": [crop_width, crop_height, x, y],
            "area_removed_percent": round(removed * 100, 1),
        }
        print(f"{source.name}: crop={crop_width}:{crop_height}:{x}:{y} ({removed:.1%} removed)")

    (OUTPUT_DIR / "crop-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
