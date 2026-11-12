#!/usr/bin/env python3

from pathlib import Path
from PIL import Image
import re
import json
# CHANGE THESE PATHS
INPUT_IMAGES = Path("/home/blaix/Documents/cosmos-transfer1-diffusion-renderer/asset/hesberg_hallway/colmap_images/")

COSMOS_OUTPUT = Path(
    "/home/blaix/Documents/cosmos-transfer1-diffusion-renderer/asset/hesberg_hallway/colmap_inference/"
)

METADATA_FILE = Path(
    "/home/blaix/Documents/cosmos-transfer1-diffusion-renderer/asset/hesberg_hallway/cosmos_input/metadata.json"
)

OUTPUT_ROOT = Path("datasets/hesberg_hallway/base/train")

MATERIALS = {
    "basecolor": "diffusionrenderer_baseColor",
    "roughness": "diffusionrenderer_roughness",
    "metallic": "diffusionrenderer_metallic",
}

with open(METADATA_FILE, "r") as f:
    metadata = json.load(f)

# Original input images, sorted by filename
images = sorted(
    p for p in INPUT_IMAGES.iterdir()
    if p.suffix.lower() in [".png", ".jpg", ".jpeg"]
)

# Find Cosmos output files recursively
def get_cosmos_frames(material):
    pattern = re.compile(
        rf"(\d+)\.(\d+)\.{material}\.jpg$"
    )

    files = []

    for path in COSMOS_OUTPUT.rglob(f"*.{material}.jpg"):
        match = pattern.match(path.name)

        if match:
            chunk = int(match.group(1))
            frame = int(match.group(2))
            files.append((chunk, frame, path))

    return [
        item[2] for item in sorted(files, key=lambda x: (x[0], x[1]))
    ]

def restore_original_resolution(generated, original_name):

    if original_name not in metadata:
        raise RuntimeError(
            f"Missing preprocessing metadata for {original_name}"
        )

    info = metadata[original_name]

    original_w, original_h = info["original_size"]

    left, top, right, bottom = info["padding"]

    resized_w, resized_h = info["resized_size"]

    with Image.open(generated) as img:

        img = img.convert("RGB")

        img = img.crop((
            left,
            top,
            left + resized_w,
            top + resized_h
        ))

        img = img.resize(
            (original_w, original_h),
            Image.Resampling.LANCZOS
        )

        return img

print(f"Found {len(images)} original images")


material_frame_counts = []

for material, output_folder in MATERIALS.items():

    cosmos_frames = get_cosmos_frames(material)

    print(
        f"\nProcessing {material}: "
        f"{len(cosmos_frames)} generated frames"
    )

    if len(cosmos_frames) < len(images):
        raise RuntimeError(
            f"Not enough Cosmos frames for {material}: "
            f"{len(cosmos_frames)} generated vs "
            f"{len(images)} original images"
        )

    if len(cosmos_frames) > len(images):

        padding_frames = len(cosmos_frames) - len(images)

        print(
            f"Discarding {padding_frames} "
            f"final padded frames"
        )

        cosmos_frames = cosmos_frames[:len(images)]

    material_frame_counts.append(len(cosmos_frames))

    destination = OUTPUT_ROOT / output_folder
    destination.mkdir(parents=True, exist_ok=True)

    for original, generated in zip(images, cosmos_frames):

        output_name = f"{original.stem}_{material}.png"

        output_path = destination / output_name

        restored = restore_original_resolution(
            generated,
            original.name
        )

        restored.save(output_path)

    print(f"Saved to {destination}")

# --------------------------------------------------
# FINAL VALIDATION
# --------------------------------------------------

assert len(set(material_frame_counts)) == 1

print("\nConversion complete!")

for folder in MATERIALS.values():

    count = len(list((OUTPUT_ROOT / folder).glob("*.png")))

    print(f"{folder}: {count} images")
