# NFSUG regenerated texture pack (NFGX v1)

The optional replacement pack lives beside the player executable at
`textures/4k/`. The host exposes it as **Graphics → Texture set → 4K Upscaled
textures** only when the exact `pack.ready` marker exists. The user's choice is
stored in `settings.ini` beside the executable; the original ROM and saves are
not modified.

Each replacement is named by the 16-digit lowercase hexadecimal FNV-1a-64 hash
of its source texture. Hash input is the source width and height as two
little-endian uint32 values, followed by the exact decoded RGBA8 bytes in
row-major order. The file is `<hash>.rgba` and contains:

| Offset | Size | Meaning |
| --- | ---: | --- |
| 0 | 4 | ASCII `NFGX` |
| 4 | 4 | uint32 little-endian version (`1`) |
| 8 | 4 | uint32 little-endian replacement width |
| 12 | 4 | uint32 little-endian replacement height |
| 16 | 8 | uint64 little-endian source hash |
| 24 | width × height × 4 | row-major RGBA8 pixels |

The loader requires exact payload length, a matching source hash, replacement
dimensions no smaller than the source, and dimensions no larger than 4096 in
either axis. Invalid or missing replacements fall back to the original decoded
texture. Original textures use nearest filtering; loaded replacements use
linear filtering. The native 4K framebuffer is a separate rendering target. The
renderer also supports exact-hash regenerated replacements for complete 240x160
menu/UI frames and transparent HUD overlays. These UI assets must be at least
3240x2160 (the active 1.5:1 game viewport inside a 3840x2160 output); smaller
4x assets are not accepted as complete 4K UI replacements. A matched menu frame
replaces the full low-resolution frame. A matched transparent HUD image is
alpha-composited over the native scene. A changed or uncaptured frame/overlay
safely uses the original pixels with the existing 4x edge-aware scaler. This is
state-by-state coverage, not a guarantee that every menu, text glyph, HUD value,
or animation has been regenerated.

When Upscaled mode is enabled, the renderer enumerates the pack's `.rgba`
filenames once into a sorted source-hash index, then validates and preloads
matching payloads into RAM (capped at 1 GiB). With an OpenGL context active, it
also uploads validated images before showing the game window (GPU-preload cap:
1 GiB). Draws can then bind the prewarmed image rather than performing a first-
use GPU upload. Missing, oversized, invalid, over-cap, or failed GPU assets keep
the original-texture fallback; assets not prewarmed remain lazy and may still
cause a first-use upload. Changing mode can synchronously perform this work, so
the option's visible interaction and a full realistic pack still require timing
tests. The cache assumes the pack remains immutable while the player is open.

This reduces first-draw work for eligible assets; it does not prove full-scene
60-Hz pacing. That gate still needs a representative multi-texture pack, longer
visible original-timing runs, and target-display testing.

## Building a pack

Export each distinct in-game source texture as an exact RGBA PNG and prepare a
regenerated/upscaled RGBA PNG for it, retaining transparent pixels. Put both
images in a directory and create a UTF-8 JSON manifest:

```json
{
  "format": "NFSUG-UPCALED-TEXTURE-SOURCES-1",
  "complete": true,
  "textures": [
    { "source": "source/example.png", "upscaled": "upscaled/example.png" }
  ]
}
```

Every replacement must be at least twice the source width and height. Run
`python build_texture_pack.py manifest.json <player-folder>/textures` from the
source package. The builder stages the complete directory and publishes the
ready marker with one directory rename. It refuses to overwrite an existing
pack; move an old pack aside before installing a rebuilt one. The `complete`
field is a manifest assertion, not an automatic audit of all ROM assets. The
project still needs a full texture inventory and production-quality regenerated
assets before the mode can promise that every pixelated texture is replaced.

## Capturing source textures

For an opt-in diagnostic run, set `NFSUG_DUMP_TEXTURES=1` before starting the
player. Each distinct decoded source image encountered by the native polygon
renderer is stored as raw row-major RGBA8 at
`texture-source-inventory/<hash>.rgba`; `source-inventory.tsv` records the
matching dimensions, original address and polygon kind. New diagnostic captures
also append renderer stride and shade, then process ID and renderer draw
serial. The nine-field form preserves the full texture-cache identity and the
first rendered frame that used each hash. The exporter remains compatible with
legacy five-field rows and seven-field process/draw rows. The capture is disabled
by default because file output can disturb frame pacing. A hash is written only
once per capture directory: `stride` and `shade` therefore describe the first
renderer cache entry that exposed those pixels, not every cache entry that may
later reuse identical content. `shade` is the source shade-table address (zero
when no table is used), not a brightness level. These fields aid attribution;
replacement lookup remains keyed by decoded source hash. Run
`python export_texture_sources.py <capture-folder> <new-output-folder>` to
verify each FNV source key and produce PNGs plus an inventory JSON marked
`complete: false`. This marker is intentionally conservative: a capture from
one saved race does not cover other cars, tracks, menus, or effects. Combine and
deduplicate captures from relevant game states with:

```powershell
python merge_texture_sources.py merged-source-inventory capture-a capture-b
```

The merged inventory keeps a source-hash-deduplicated PNG and per-capture
address/kind provenance. When available, it also retains each capture's
`stride`, `shade`, `first_seen_process_id`, and `first_seen_draw_serial`. Those fields identify the
first renderer draw that observed a hash; they do not assert that the texture is
stable or a distinct skin. Early hashes at a RAM-backed address may be
transient while scene data is loading. Keep the raw records and review the
ordered sequence before generating assets or merging variants. The inventory
always remains `complete: false`; merging captures alone is not a ROM-wide
coverage audit. Review the merged inventory, audit coverage, prepare regenerated
replacements, and only then create the
separate regeneration manifest used by the pack builder. The merge utility's
Python fixture test is `tests/test_merge_texture_sources.py`.

Review timed texture variants without altering or dropping captures:

Run audit_texture_sequences.py with a merged source inventory, a new CSV report,
a settle-after draw serial, and an optional focus rectangle. The review groups
by capture set, process, address, dimensions, kind, stride, and shade so distinct
renderer cache variants are not conflated. Its threshold and focus
are diagnostic choices; a broad early difference is only a human-review flag,
never proof that an asset is transient. Legacy rows without draw serials are
retained and labeled no-draw-provenance. The report never changes inventory or
pack inputs. The fixture test is tests/test_audit_texture_sequences.py.

## UI frame and HUD capture

To collect source images for reviewed menu/HUD regeneration, set
`NFSUG_DUMP_UI_FRAMES=1` before launching. The diagnostic capture records up to
512 unique full-frame source images and 512 unique transparent native-HUD
images per launch into the same `texture-source-inventory` directory as polygon
textures. UI rows use `kind=5` for complete 240x160 menu/non-native frames and
`kind=4` for transparent native-scene overlays; the existing source exporter
retains the kind and verifies the exact RGBA hash. Capture is off by default
because hashing and disk writes can affect frame pacing. It records only states
actually visited and must not be labeled complete automatically.

For each UI capture, regenerate a 3240x2160 RGBA image that preserves layout,
letterboxing, transparency, and the source's intended text/art. Add the source
and replacement to the audited pack manifest like any other exact-hash item.
The runtime activates it only while Upscaled mode is enabled and the current
source hash matches. A dynamic HUD overlay changes its key when any source
pixel changes, so it falls back to the 4x scaler until that exact state has a
reviewed 4K replacement. Coverage still requires human review across menus,
text, HUD values, cars, tracks, and game states; this implementation does not
itself generate artwork or remove pixelation from uncaptured states.
## Current coverage boundary

Polygon texture matching remains keyed by exact decoded RGBA content. Full menu
frames and transparent HUD overlays have a separate exact-source-frame
replacement path when the pack includes a reviewed 3240x2160 asset. Unmatched UI
states still use the 4x edge-aware scaler, and the sky is not automatically
regenerated by this path. This is infrastructure for complete UI coverage, not
evidence that every menu, label, HUD value, or sky pixel has been replaced.
## Bounded lazy full-menu residency

A complete menu-frame replacement that was not included in the bulk GPU-prewarm set can now be loaded on demand by exact source-frame hash. The runtime keeps only the current full-menu replacement in a separate single-slot GL cache, with a 128 MiB payload ceiling; a new source hash replaces the old texture. This covers menu entries beyond the startup preload budget without retaining all captured menu states at once. Invalid, missing, undersized, over-budget, or failed loads use the existing scaled-original frame. The first encounter still performs synchronous pack lookup/read and texture upload, so visible menu transitions must be profiled before release.

Transparent HUD overlays remain prewarm-only. Their source hash may change during ordinary gameplay; loading each new 4K overlay synchronously could upload a large image every frame. Unsupported or non-prewarmed overlay states continue using the 4x scaler. This is a bounded memory improvement, not a complete HUD/text regeneration strategy, and the existing 1 GiB CPU/GPU bulk-preload limits still apply.
### Verifying lazy menu replacements

The component test test_ui_frame_pack.c writes a synthetic exact-hash 3240x2160 replacement to a temporary ready pack and calls the cached loader after indexing but before bulk preloading. It checks 4K dimensions, exact RGBA samples, the single-frame byte bound, and missing-file fallback after removing the asset. This does not exercise OpenGL upload/reuse or prove visible runtime behavior; those remain separate acceptance gates.
The single-slot state machine is shared between the GPU renderer and the portable ui_scale tests through synchronous loader/uploader/deleter callbacks. The unit test exercises same-hash reuse (one upload), successful source-hash replacement, load/upload failure fallback while keeping the prior valid texture, undersized rejection before upload, failed-candidate cleanup, and final cache clear. These mock callback tests do not substitute for OpenGL pixel readback or visible timing tests.