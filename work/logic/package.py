from pathlib import Path
import json,zipfile,shutil,hashlib
out=Path('outputs/nfsug-native-renderer');src=Path('work/v2/package/NFSUG-Native-Renderer-source')
for a,b in [('host.c','main.c'),('probe.c','bridge.c')]:
 (src/b).write_text(Path('work',a).read_text().replace('../outputs/nfsug-research/','').replace('work/span-cycles.csv','span-cycles.csv'))
for n in ['gpu.c','gpu.h']:shutil.copy2(Path('work/v2')/n,src/'v2'/n)
(src/'Build.ps1').write_text((src/'Build.ps1').read_text().replace('NFSUG-60Hz-Active.exe','NFSUG-Original-Logic-Smooth.exe'))
notes='''# Original logic with experimental motion interpolation

Launch NFSUG-Original-Logic-Smooth.exe. This version keeps the game's original simulation speed and generates intermediate geometry views in the native renderer. The earlier CPU speed-up is disabled and cannot be enabled using F4 in this build.

F4 now toggles geometry interpolation only. F3 compares native 4K with the original image. Existing controller mappings and snapshots remain compatible. The title's source fps remains approximately 15 because the original simulation is intentionally unchanged; display fps is the window presentation rate.

## What changed

The previous 60-Hz update experiment sped up frame-dependent logic. A traced example is the player steering ramp at 080097EE: its accumulator is incremented by the same amount each call, reaching four times the reference value after four refreshes. A research-only correction for that ramp improved it but did not normalize the remaining physics. That correction is not enabled here.

This build instead keeps two completed geometry scenes. It matches compatible primitives by texture, topology, projected position and UV coordinates, then interpolates matched vertex positions and projective texture coordinates over the following scene interval. This creates intermediate views without modifying the game's memory, timers or simulation cadence. Menus and intro retain their existing paths; interpolation is applied during race state 5.

## Validation and limits

A paced five-second rendering audit measured about 59.1 changing rendered images per second while CPU acceleration was off. Separate 300-frame real-time runs with identical inputs and smoothing on/off produced identical EWRAM, IWRAM and VRAM hashes. The 2400-frame startup-with-audio test passed. Reports are included alongside this file.

This is experimental visual interpolation, NOT a true 60-Hz physics engine. It adds roughly one original scene of visual delay (typically 65–75 ms). Unmatched/newly visible primitives and HUD/effects still update at source cadence. Matching and screen-space interpolation can cause popping, deformation or incorrect motion during occlusion and sharp turns. The test confirms simulation preservation for the tested run, not flawless interpolation on every scene or monitor scanout timing.

Use F4 to compare the interpolation with original movement. Native 4K rasterization remains active in either mode. The long-term engine work is still to recover a native camera/scene renderer and decouple it cleanly from fixed simulation steps.

Source: NFSUG-Original-Logic-Smooth-source.zip. Older documentation in the archive is retained as historical research. This file describes current behavior.
'''
(out/'ORIGINAL-LOGIC-SMOOTH.md').write_text(notes);(src/'ORIGINAL-LOGIC-SMOOTH.md').write_text(notes)
for n in ['logic-equivalence.json','interpolation-test.json','steering-tests.json']:
 shutil.copy2(Path('work/logic')/n,out/n);shutil.copy2(Path('work/logic')/n,src/'tests'/n)
with zipfile.ZipFile(out/'NFSUG-Original-Logic-Smooth-source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in src.rglob('*'):
  if p.is_file() and not any(x in ('build','deps') for x in p.relative_to(src).parts):z.write(p,p.relative_to(src.parent))
(out/'smooth-build.json').write_text(json.dumps({'sha256':hashlib.sha256((out/'NFSUG-Original-Logic-Smooth.exe').read_bytes()).hexdigest(),'original_simulation':True,'render_interpolation':True,'true_60hz_physics':False},indent=2))
print('Packaged original-logic interpolation build and corresponding source.')
