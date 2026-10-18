"""Measure source-frame changes in a fixed screen region.

This hidden audit does not establish skybox identity, display pacing, monitor
scanout, or native sky reconstruction. The default region is a historical
candidate; verify its contents visually for each camera/track state.
"""
from __future__ import annotations

import argparse
import ctypes as C
import hashlib
import json
import os
import struct
import time
from pathlib import Path

WIDTH, HEIGHT = 240, 160
DEFAULT_REGION = (70, 12, 21, 19)
ROM_NAME = "Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba"
LEGACY_ROM = Path(r"G:\EXTRA DATA DRIVE\Desktop\Emulators\GBA\GBA ROMS\Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba")


def hash_region(pixels, x, y, width, height):
    value = 2166136261
    for row in range(y, y + height):
        for col in range(x, x + width):
            value = ((value ^ int(pixels[row * WIDTH + col])) * 16777619) & 0xFFFFFFFF
    return value


def parse_region(value):
    try:
        region = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("region must be four integers: X,Y,W,H") from exc
    if len(region) != 4:
        raise argparse.ArgumentTypeError("region must be four integers: X,Y,W,H")
    x, y, width, height = region
    if x < 0 or y < 0 or width < 1 or height < 1 or x + width > WIDTH or y + height > HEIGHT:
        raise argparse.ArgumentTypeError(f"region must fit inside {WIDTH}x{HEIGHT}")
    return region


def main():
    project = Path(__file__).resolve().parents[2]
    project_rom = project.parent / ROM_NAME
    default_rom = project_rom if project_rom.is_file() else LEGACY_ROM
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, default=project / "work" / "nfsprobe.dll")
    parser.add_argument("--runtime-dir", type=Path, help="directory containing MinGW runtime DLLs used by the probe")
    parser.add_argument("--state", type=Path, default=project / "work" / "race.state")
    parser.add_argument("--rom", type=Path, default=default_rom)
    parser.add_argument("--region", type=parse_region, default=DEFAULT_REGION, metavar="X,Y,W,H",
                        help="fixed source-screen sample; visually verify it before interpreting as sky")
    parser.add_argument("--frames", type=int, default=600)
    parser.add_argument("--capture-dir", type=Path, help="optional directory for source-frame PPM checkpoints")
    parser.add_argument("--capture-every", type=int, default=60, help="emulated updates between PPM checkpoints")
    args = parser.parse_args()

    if args.frames < 1 or args.capture_every < 1 or not args.dll.is_file() or not args.state.is_file() or not args.rom.is_file():
        parser.error("DLL, ROM, and state must exist and --frames must be positive")

    dll_hash = hashlib.sha256(args.dll.read_bytes()).hexdigest()
    # Python 3.8+ no longer searches PATH for dependent DLLs on Windows.
    # Keep these directory handles alive for the lifetime of the loaded core.
    dll_directories = []
    runtime_handles = []
    if os.name == "nt":
        candidates = [args.dll.parent]
        if args.runtime_dir is not None:
            candidates.append(args.runtime_dir)
        candidates.extend(Path(entry) for entry in os.environ.get("PATH", "").split(os.pathsep) if entry)
        seen = set()
        for directory in candidates:
            try:
                normalized = str(directory.resolve()).casefold()
                if normalized not in seen and directory.is_dir():
                    dll_directories.append(os.add_dll_directory(str(directory)))
                    seen.add(normalized)
            except (OSError, ValueError):
                continue
        # Some MinGW-built probe DLLs depend on libgcc and winpthreads. Load
        # these explicitly because Windows may not resolve PATH dependencies
        # for a DLL loaded by Python, even after AddDllDirectory.
        for name in ("libwinpthread-1.dll", "libgcc_s_seh-1.dll"):
            for directory in candidates:
                candidate = directory / name
                if candidate.is_file():
                    runtime_handles.append(C.CDLL(str(candidate)))
                    break
    core = C.CDLL(str(args.dll))
    core.nf_init.argtypes = [C.c_char_p, C.c_char_p]
    core.nf_init.restype = C.c_int
    core.nf_state.argtypes = [C.c_char_p, C.c_int]
    core.nf_state.restype = C.c_int
    core.nf_pixels.restype = C.c_void_p
    core.nf_frame.argtypes = [C.c_uint]
    core.nf_scene_enable.argtypes = [C.c_int]
    core.nf_read.argtypes = [C.c_uint, C.c_int]
    core.nf_read.restype = C.c_uint
    core.nf_close.argtypes = []

    if not core.nf_init(str(args.rom).encode(), b""):
        raise RuntimeError("mGBA bridge failed to initialize the supplied ROM")
    try:
        if not core.nf_state(str(args.state).encode(), 0):
            raise RuntimeError("failed to load the read-only race state")
        core.nf_scene_enable(1)
        x, y, width, height = args.region
        roi_hashes, frame_hashes, blue_counts, page_flips = [], [], [], 0
        change_updates, page_flip_updates, frame_change_updates = [], [], []
        previous_page = core.nf_read(0x04000000, 2) & 16
        previous_frame = None
        started = time.perf_counter()
        previous_roi = None
        if args.capture_dir is not None:
            args.capture_dir.mkdir(parents=True, exist_ok=True)
        for update in range(1, args.frames + 1):
            core.nf_frame(1)
            pixels = C.cast(core.nf_pixels(), C.POINTER(C.c_uint32 * (WIDTH * HEIGHT))).contents
            roi = hash_region(pixels, x, y, width, height)
            roi_hashes.append(roi)
            if previous_roi is not None and roi != previous_roi:
                change_updates.append(update)
            previous_roi = roi
            frame_hash = hash_region(pixels, 0, 0, WIDTH, HEIGHT)
            frame_hashes.append(frame_hash)
            if previous_frame is not None and frame_hash != previous_frame:
                frame_change_updates.append(update)
            previous_frame = frame_hash
            blue = 0
            for row in range(y, y + height):
                for col in range(x, x + width):
                    pixel = int(pixels[row * WIDTH + col])
                    r, g, b = pixel & 255, (pixel >> 8) & 255, (pixel >> 16) & 255
                    blue += int(b > r + 25 and b > g + 5 and b > 80)
            blue_counts.append(blue)
            if args.capture_dir is not None and update % args.capture_every == 0:
                path = args.capture_dir / f"source-{update:06d}.bmp"
                row_bytes = (WIDTH * 3 + 3) & ~3
                bmp_pixels = bytearray(row_bytes * HEIGHT)
                for row in range(HEIGHT):
                    target_row = HEIGHT - 1 - row
                    for col in range(WIDTH):
                        pixel = int(pixels[row * WIDTH + col])
                        offset = target_row * row_bytes + col * 3
                        bmp_pixels[offset] = (pixel >> 16) & 255
                        bmp_pixels[offset + 1] = (pixel >> 8) & 255
                        bmp_pixels[offset + 2] = pixel & 255
                with path.open("wb") as capture:
                    capture.write(b"BM")
                    capture.write(struct.pack("<IHHI", 54 + len(bmp_pixels), 0, 0, 54))
                    capture.write(struct.pack("<IiiHHIIiiII", 40, WIDTH, HEIGHT, 1, 24, 0, len(bmp_pixels), 2835, 2835, 0, 0))
                    capture.write(bmp_pixels)
            page = core.nf_read(0x04000000, 2) & 16
            if page != previous_page:
                page_flips += 1
                page_flip_updates.append(update)
            previous_page = page
        elapsed = time.perf_counter() - started
    finally:
        core.nf_close()

    roi_changes = sum(a != b for a, b in zip(roi_hashes, roi_hashes[1:]))
    frame_changes = sum(a != b for a, b in zip(frame_hashes, frame_hashes[1:]))
    flip_set = set(page_flip_updates)
    roi_change_set = set(change_updates)
    frame_change_set = set(frame_change_updates)
    blue_total = width * height
    report = {
        "scope": "source framebuffer updates only; fixed screen region is not semantic sky identification, host pacing, monitor scanout, or native sky validation",
        "candidate_region_xywh": list(args.region),
        "candidate_region_semantics": "fixed screen rectangle; visually validate for each saved state because buildings may occlude it",
        "dll_sha256": dll_hash,
        "state_path": str(args.state),
        
        "region_blue_pixels_first_frame": blue_counts[0],
        "region_pixels": blue_total,
        "region_blue_fraction_min": min(blue_counts) / blue_total,
        "region_blue_fraction_max": max(blue_counts) / blue_total,
        "emulated_updates": args.frames,
        "wall_seconds": round(elapsed, 6),
        "source_frame_unique_hashes": len(set(frame_hashes)),
        "source_frame_adjacent_changes": frame_changes,
        "region_unique_hashes": len(set(roi_hashes)),
        "region_adjacent_changes": roi_changes,
        "region_adjacent_repeats": max(0, args.frames - 1 - roi_changes),
        "region_change_update_indices_first_40": change_updates[:40],
        "region_changes_on_page_flip": len(roi_change_set & flip_set),
        "region_changes_off_page_flip": len(roi_change_set - flip_set),
        "source_frame_changes_on_page_flip": len(frame_change_set & flip_set),
        "source_frame_changes_off_page_flip": len(frame_change_set - flip_set),
        "page_flip_update_indices_first_40": page_flip_updates[:40],
        "region_change_interval_min": min((b - a for a, b in zip(change_updates, change_updates[1:])), default=None),
        "region_change_interval_max": max((b - a for a, b in zip(change_updates, change_updates[1:])), default=None),
        "capture_dir": str(args.capture_dir) if args.capture_dir is not None else None,
        "page_flips": int(page_flips),
        "first_12_region_hashes": [f"{value:08x}" for value in roi_hashes[:12]],
        "last_12_region_hashes": [f"{value:08x}" for value in roi_hashes[-12:]],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
