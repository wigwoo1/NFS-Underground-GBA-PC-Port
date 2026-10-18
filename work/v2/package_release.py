from pathlib import Path
import shutil,zipfile,sys
out=Path('outputs/nfsug-native-renderer');out.mkdir(exist_ok=True)
src=Path('work/v2/package/NFSUG-Native-Renderer-source');src.mkdir(parents=True,exist_ok=True)
source_only='--source-only' in sys.argv[1:]
for d in ['vendor','tests','v2','camera']:(src/d).mkdir(exist_ok=True)
for name in ['native_span.c','native_span.h','controller.h']:
 shutil.copy2(Path('outputs/nfsug-research')/name,src/name)
camera_sources=[line.strip() for line in Path('work/v2/native-renderer-sources.txt').read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
for name in camera_sources:shutil.copy2(Path('work/camera')/name,src/'camera'/name)
shutil.copy2('work/camera/model_preview.c',src/'camera/model_preview.c')
for header in Path('work/camera').glob('*.h'):shutil.copy2(header,src/'camera'/header.name)
shutil.copy2('work/v2/native-renderer-sources.txt',src/'camera/native-renderer-sources.txt')
for a,b in [('host.c','main.c'),('probe.c','bridge.c')]:
 (src/b).write_text(Path('work',a).read_text().replace('../outputs/nfsug-research/','').replace('work/span-cycles.csv','span-cycles.csv'))
for name in ['gpu.c','gpu.h','hash_region.h','scene.h','texture_pack.c','texture_pack.h','ui_scale.c','ui_scale.h','build_texture_pack.py','texture_hash.py','export_texture_sources.py','export_texture_sources.ps1','make_texture_contact_sheet.ps1','merge_texture_sources.py','audit_texture_sequences.py','regenerate_asphalt_texture.py','regenerate_masonry_texture.py','texture-pack-format.md']:
 shutil.copy2(Path('work/v2')/name,src/'v2'/name)
shutil.copy2('work/v2/test_texture_pack.c',src/'tests/test_texture_pack.c')
shutil.copy2('work/v2/test_ui_scale.c',src/'tests/test_ui_scale.c')
shutil.copy2('work/v2/test_source_region_hash.c',src/'tests/test_source_region_hash.c')
shutil.copy2('work/v2/test_export_texture_sources.py',src/'tests/test_export_texture_sources.py')
shutil.copy2('work/v2/test_export_texture_sources_portable.py',src/'tests/test_export_texture_sources_portable.py')
shutil.copy2('work/v2/test_merge_texture_sources.py',src/'tests/test_merge_texture_sources.py')
shutil.copy2('work/v2/test_audit_texture_sequences.py',src/'tests/test_audit_texture_sequences.py')
shutil.copy2('work/v2/test_regenerate_masonry_texture.py',src/'tests/test_regenerate_masonry_texture.py')
shutil.copy2('work/mgba.zip',src/'vendor/mgba-0.10.5.zip')
shutil.copy2('work/mgba-0.10.5/src/arm/arm.c',src/'vendor/arm.c')
shutil.copy2('work/mgba-0.10.5/LICENSE',src/'vendor/mGBA-LICENSE.txt')
s=Path('work/source-Build.ps1').read_text();start=s.index('$armSource=');end=s.index('$argsConfigure=')
s=s[:start]+"Copy-Item -LiteralPath 'vendor/arm.c' -Destination $armPath -Force\n"+s[end:]
s=s.replace('main.c bridge.c native_span.c','main.c bridge.c v2/gpu.c v2/texture_pack.c v2/ui_scale.c native_span.c @cameraSources').replace('NFSUG-Port-Lab.exe','NFSUG-Native-Renderer.exe')
needle="if($LASTEXITCODE){throw 'Controller mapping tests failed.'}\n"
assert needle in s
s=s.replace(needle,needle+"& \"$CompilerBin/gcc.exe\" \"-B$CompilerBin/\" -O2 -Iv2 tests/test_texture_pack.c v2/texture_pack.c -o build/test_texture_pack.exe\nif($LASTEXITCODE){throw 'Texture-pack loader tests failed.'}\n& ./build/test_texture_pack.exe\nif($LASTEXITCODE){throw 'Texture-pack loader tests failed.'}\n")
s=s.replace(needle,needle+"& \"$CompilerBin/gcc.exe\" \"-B$CompilerBin/\" -O2 -Iv2 tests/test_ui_scale.c v2/ui_scale.c -o build/test_ui_scale.exe\nif($LASTEXITCODE){throw 'UI edge-aware upscaler tests failed.'}\n& ./build/test_ui_scale.exe\nif($LASTEXITCODE){throw 'UI edge-aware upscaler tests failed.'}\n")
marker="Write-Host 'Built build/NFSUG-Native-Renderer.exe. See BUILDING.md for ROM and test commands.'"
region_test="& \"$CompilerBin/gcc.exe\" \"-B$CompilerBin/\" -O2 -Iv2 tests/test_source_region_hash.c -o build/test_source_region_hash.exe\nif($LASTEXITCODE){throw 'Source-region hash tests failed.'}\n& ./build/test_source_region_hash.exe\nif($LASTEXITCODE){throw 'Source-region hash tests failed.'}\n"
assert marker in s
s=s.replace(marker,region_test+marker)
(src/'Build.ps1').write_text(s)
(src/'tests/test_controller.c').write_text(Path('work/test_controller.c').read_text().replace('../outputs/nfsug-research/controller.h','../controller.h'))
if not source_only:shutil.copy2('work/v2/NFSUG-Native-Renderer.exe',out/'NFSUG-Native-Renderer.exe')
for name in ['scene-tests.json','host-test.json','cpu-cadence.json']:shutil.copy2(Path('work/v2')/name,out/name)
shutil.copy2('work/mgba-0.10.5/LICENSE',out/'mGBA-LICENSE.txt')
readme='''# NFSUG Native Renderer â€” experimental 4K build

Launch NFSUG-Native-Renderer.exe. It opens your original ROM at its existing G: location, or asks you to select it if it has moved. No ROM is included or modified. This build has its own snapshot file; the earlier Port Lab build remains separate.

## What works in this version

The road, player car and captured building/scenery strips are drawn by native Windows/OpenGL code into a 3840Ã—2160 render target. The original 3:2 picture occupies 3240Ã—2160 pixels, with 300-pixel side borders. Textures are read from your ROM and game memory. Polygon edges and texture sampling are rasterized at the higher resolution.

This is an intermediate porting milestone. Game logic, physics, audio and asset preparation still execute in mGBA. In Upscaled mode, the 240Ã—160 transparent HUD/text overlay receives an edge-aware 4Ã— Scale2x pass before composition; this preserves source colors and glyph shapes but is not a regenerated high-resolution font or full UI pack. Sky and unsupported drawing paths still rely on the original-resolution image. Original textures and projected coordinates limit detail; the scenery path reconstructs textured strips, so artifacts are possible. This is not a completed native game port or a complete high-precision 3D engine replacement.

## Texture sets

Use **Graphics â†’ Texture set** to choose Original textures or 4K Upscaled textures. The selection is saved in settings.ini beside the executable. The upscaled option is enabled only when a generated pack is installed under textures/4k; if an individual replacement is missing or invalid, that texture falls back to its original ROM image. In Upscaled mode the transparent HUD/text overlay is also edge-aware scaled 4Ã— from its original pixels. This reduces blocky edges, but does not recreate glyph details or make all menus/text native 4K; static high-resolution UI assets and full source coverage remain future work. The sky layer remains a separate original-resolution path. This source package contains capture export, inventory merge, timed-sequence review, pack builder and format tools, but does not include a regenerated texture pack or ROM-derived image assets. A complete asset inventory and generated replacement set are still required.

The game retains its original timing, roughly 14â€“15 new race scenes per second in the tested scene. The window aims to present at 60 Hz, repeating scenes between updates. Correct 60-fps gameplay is still in development. CPU acceleration was tested but changes vehicle motion, so it is not enabled in the player build.

To capture exact ROM-derived source textures encountered in a test run, set `NFSUG_DUMP_TEXTURES=1` before launching. Raw RGBA blobs and a hash/dimension/address inventory are written beside the executable under `texture-source-inventory`. Run `python export_texture_sources.py <texture-source-inventory> <new-output-folder>` to validate the hashes and produce reviewable PNGs; use `python merge_texture_sources.py <new-merged-folder> <export-a> <export-b>` to hash-deduplicate separate exports while preserving provenance. Both tools keep coverage marked incomplete. Do not mark a replacement pack complete until every required texture has been audited and has a regenerated counterpart.

## Controls

- Xbox RT or A: accelerate / confirm; LT or B: brake / back.
- Left stick or D-pad: steer / navigate.
- LB or X: GBA L; RB or Y: GBA R.
- Menu: Start; View: Select.
- Keyboard: arrows, Z/A button, X/B button, A/L button, S/R button, Enter/Start, Backspace/Select.
- F3: compare 4K geometry with the original image.
- F11: fullscreen; Escape: leave fullscreen.
- F5/F8: save/load a snapshot next to the executable.
- Space: pause/resume. Losing focus pauses the game.
- F1: controls. F2: optional earlier native span experiment, disabled by default; it has separate timing limitations.

If 4K framebuffer creation is unsupported, the host falls back to the original renderer. The title shows the active view. Xbox mappings are tested in code; a physical controller has not been tested by the agent.

## Validation

A 600-frame graphics run on an AMD Radeon RX 7900 XTX completed with zero OpenGL errors, a 3840Ã—2160 framebuffer and 303 captured primitives in the last frame. An independent 600-frame capture-on/capture-off comparison matched every original framebuffer and sampled vehicle state. Loading a snapshot clears old geometry. These checks cover the tested race sequence, not every track, car, effect or menu transition.

See ENGINE-NOTES.md for the recovered interfaces, current timing findings and next work. Source and the corresponding modified mGBA file are included in NFSUG-Native-Renderer-source.zip. The original ROM is required and excluded from the archive.
'''
(out/'README.md').write_text(readme,encoding='utf-8');(src/'README.md').write_text(readme,encoding='utf-8')
notes=Path('outputs/nfsug-research/ENGINE-NOTES.md').read_text()+'''

# Native GPU milestone (v2)

Earlier status statements above describe v1. V2 adds high-resolution road/car/scenery rasterization while retaining mGBA execution.

## Recovered geometry interfaces

- Road polygon entry 030032F0: r0 material, r1 state, r2 additional UV; fifth stack argument selects affine/perspective. State +6C points to 24-byte projected vertices, +F2 start index, +F4 count. Vertices contain screen X/Y, reciprocal depth at word 3 and UV at words 4/5. Material +24 texture stride shift, +26 height, +28 texture pointer. Paired palette-index storage means source stride is twice the effective texture width and effective height is half the material height. See scene_capture in bridge.c for exact normalized projective coordinates.
- Clipped car polygon capture 03003D74: r9 material, r4 polygon. Polygon fields +0 XY array, +4 UV array, +8 XY indices, +0C UV indices, +14 vertex count. UV uses 32768 normalization; car skin can be RAM-backed and is refreshed each draw.
- Scenery column entries 030053E8 and 03005320 (palette-remapped shade). r0 span state, r1 column destination, r2 starting V, r3 height. State +4 top Y 14-fractional-bit, +12 texture shift, +16 height, +20 shade base, +24 mip flag, +28 mip offset, +36 texture, +42 shade offset, +44 dV, +52 U. Each GBA column writes duplicated palette pixels. Native strips reconnect adjacent projected endpoints and use projective texture coordinates. Transparent index zero is preserved. This recovers drawing inputs, not full world-space building meshes.
- Display page is DISPCNT bit 4. Native geometry has two page buffers. State loads discard both. GPU overlay compares palette-decoded mode-4 VRAM with the final GBA image to retain HUD/sky compositing.
- OpenGL target is 3840x2160, game viewport 3240x2160. Ear clipping triangulates recovered polygons. Fixed-function projective texture coordinates use s,t,q. Original textures use nearest sampling.

## Timing investigation

Main update/render entry 08004E78 receives game state 030000C0. State +3C points to vehicles with stride A4. Vehicle +0C/+14 appear world X/Z and +2C speed. More field validation is needed.

At 08000C0C the loop reads timer 2 through 0806F908, storing its count at 03006044. It divides 25500 by that count, clamps the result to 10..100 and stores the estimated frame rate at 03005D88. Consumers occur near 08005C54, 0801DC8C, 080203F4, 08022818 and 080249BC (literal addresses).

080227F6 calls vehicle routine 08007540 with this rate as its fifth argument. At 0800757A that argument is shifted by 8, passed to reciprocal routine 0800ACB4, then capped at 3072. The reciprocal routine normalizes into ROM lookup table 08627700; that table contains floor(16777216/(index+1)). This is a concrete time-step path, but other per-frame behavior and timer measurement still need separation before changing simulation cadence safely.

600-VBlank CPU-credit experiments measured ~14.33, 30.46 and 53.85 page changes/sec for 1x/2x/4x. All showed the same elapsed race clock but different vehicle motion. 8x page-flip sampling aliases and is not a reliable update-rate measurement. These are research observations, not a 60-fps solution. nf_speed remains an experimental bridge API and is unused by the default host.

## Next engineering work

Trace each vehicle update against elapsed hardware cycles, recover remaining frame-dependent input/physics/camera operations, then compare trajectories under a fixed simulation step. Replace emulated asset/scene preparation incrementally with native C. Recover world-space mesh/camera inputs to remove projected-coordinate quantization and scenery strip approximations. Validate more race scenes and menu transitions before expanding coverage claims.
'''
(out/'ENGINE-NOTES.md').write_text(notes,encoding='utf-8');(src/'ENGINE-NOTES.md').write_text(notes,encoding='utf-8')
(src/'BUILDING.md').write_text('''# Build

Windows x64, MinGW-w64 GCC, CMake and PowerShell are required. Run:

```powershell
./Build.ps1 -CompilerBin 'C:/path/to/w64devkit/bin' -CmakeExe 'C:/path/to/cmake.exe'
./build/NFSUG-Native-Renderer.exe --rom 'G:/path/to/game.gba'
```

The vendor zip is upstream mGBA 0.10.5; vendor/arm.c is the corresponding modified instruction dispatcher, installed by Build.ps1 before compiling. It adds ARM capture/native hooks, optional Thumb tracing and experimental CPU-cycle scaling (default factor 1). MPL notices remain in the modified file. The script builds the host and research DLLs and runs controller-mapping, texture-pack-loader, UI upscaler, and source-region hash tests. No ROM or game assets are bundled. The host's Graphics menu stores its texture preference in settings.ini. A regenerated pack can be built with the packaged builder; see v2/texture-pack-format.md for the source-hash manifest and installation location. The package also includes Python capture-export and source-inventory merge tools with fixture tests.

Hidden graphics test: `./build/NFSUG-Native-Renderer.exe --test 600 --state path/to/progress.state --capture build/capture.ppm`. Omit --state for boot testing. The host writes host-test.json beside the executable. A test runs held accelerator; it does not certify physical controller input or audio.
''')
print(out.resolve())
