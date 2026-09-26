"""Upscale low-resolution B-roll with Real-ESRGAN (x2), so it holds up next to the 1080p performance clips.

Usage: python tools/upscale_clips.py <clip.mp4> [<clip.mp4> ...]

Each clip is decoded frame by frame, upscaled 2x (RealESRGAN_x2plus, fp16, tiled), scaled to 1920x1080 with Lanczos and
re-encoded next to the source as <name>_up.mp4 at the source frame rate. The original stays untouched.
REALESRGAN_WEIGHTS points at RealESRGAN_x2plus.pth. With HAL_SCRIPTS set, the run holds HAL's GPU lease, so it never
competes with another GPU job on the machine."""
from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

WEIGHTS = Path(os.environ.get("REALESRGAN_WEIGHTS", "RealESRGAN_x2plus.pth"))


def probe(path: Path) -> tuple[int, int, str]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    stream = json.loads(out)["streams"][0]
    return stream["width"], stream["height"], stream["r_frame_rate"]


def upscale(path: Path, upsampler) -> Path:
    width, height, rate = probe(path)
    out = path.with_name(path.stem + "_up.mp4")
    decoder = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                               stdout=subprocess.PIPE)
    encoder = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width * 2}x{height * 2}",
                                "-r", rate, "-i", "-", "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.4",
                                "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", str(out)],
                               stdin=subprocess.PIPE)
    size = width * height * 3
    while True:
        raw = decoder.stdout.read(size)
        if len(raw) < size:
            break
        frame = np.frombuffer(raw, np.uint8).reshape(height, width, 3)
        result, _ = upsampler.enhance(frame, outscale=2)
        encoder.stdin.write(np.ascontiguousarray(result).tobytes())
    encoder.stdin.close()
    encoder.wait()
    decoder.wait()
    return out


def gpu_slot():
    if not os.environ.get("HAL_SCRIPTS"):
        return contextlib.nullcontext()
    sys.path.insert(0, os.environ["HAL_SCRIPTS"])
    from hal_gpu_lease import gpu_lease

    return gpu_lease("livepeer-hackathon", "Real-ESRGAN x2 upscale of B-roll clips", wait_seconds=600)


def main(paths: list[Path]) -> list[str]:
    import types

    import torchvision.transforms.functional as functional

    # basicsr still imports torchvision.transforms.functional_tensor, which newer torchvision removed
    shim = types.ModuleType("torchvision.transforms.functional_tensor")
    shim.rgb_to_grayscale = functional.rgb_to_grayscale
    sys.modules.setdefault("torchvision.transforms.functional_tensor", shim)
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=2)
    done = []
    with gpu_slot():
        upsampler = RealESRGANer(scale=2, model_path=str(WEIGHTS), model=model, tile=512, tile_pad=10, pre_pad=0, half=True)
        for path in paths:
            done.append(str(upscale(path, upsampler)))
            print("upscaled", path.name, flush=True)
    return done


if __name__ == "__main__":
    print(json.dumps(main([Path(p) for p in sys.argv[1:]]), indent=1))
