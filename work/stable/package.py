from pathlib import Path
import json,zipfile,shutil
out=Path('outputs/nfsug-native-renderer');src=Path('work/v2/package/NFSUG-Native-Renderer-source')
(src/'bridge.c').write_text(Path('work/probe.c').read_text().replace('../outputs/nfsug-research/','').replace('work/span-cycles.csv','span-cycles.csv'))
(src/'Build.ps1').write_text((src/'Build.ps1').read_text().replace('NFSUG-4K-Scene-Renderer.exe','NFSUG-4K-Synchronized.exe'))
notes='''# Synchronized 4K renderer

Use NFSUG-4K-Synchronized.exe. The earlier page-freshness fix remains, and the startup/menu direct display path remains.

The flicker investigation found that nf_overlay compared the completed GBA framebuffer against the current DISPCNT page after runFrame. The game can flip pages before that call returns. Comparing unrelated images marked most of the original frame as a HUD overlay and drew it on top of the 4K geometry.

The bridge now latches geometry at scanline zero and builds each overlay row immediately after the original renderer draws that scanline, using that row's actual video page and palette. The host receives a separate immutable visible-geometry copy rather than the live page under construction.

In the 600-frame driving comparison, maximum opaque overlay coverage fell from 35,101/38,400 pixels (91.4%) to 4,489/38,400 (11.7%). After warmup neither version had missing geometry; this identified incorrect overlays as the cause of the apparent resolution switching in that sequence. Original framebuffer and sampled vehicle-state equivalence still passes with capture enabled. Startup with audio, demo-to-menu checkpoints and a 600-frame GPU race test also pass. Other visual artifacts may remain; this does not certify all tracks or effects.

## Motion remains unfinished

There are still roughly 14–15 new race scenes per second in the tested workload. Presenting repeated frames around 60 Hz is not 60-fps camera movement or gameplay. This build does not add interpolation or a 60-Hz simulation. Earlier CPU-speed experiments changed vehicle motion and were not shipped as a solution. The next engine work requires validated time-step handling in physics/camera updates and independently generated intermediate views. This patch addresses the resolution flicker only.

Source: NFSUG-4K-Synchronized-source.zip. Older notes in the source archive are historical. Existing progress.state remains compatible; F3 selects original rendering for comparison.
'''
(out/'SYNCHRONIZED-RENDERER.md').write_text(notes);(src/'SYNCHRONIZED-RENDERER.md').write_text(notes)
for a,b in [('work/stable/scanout-tests.json','scanout-tests.json'),('work/stable/race-test.json','synchronized-race-test.json'),('work/stable/startup-test.json','synchronized-startup-test.json'),('work/v2/scene-tests.json','synchronized-equivalence.json')]:
 shutil.copy2(a,out/b);shutil.copy2(a,src/'tests'/b)
with zipfile.ZipFile(out/'NFSUG-4K-Synchronized-source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in src.rglob('*'):
  if p.is_file() and not any(x in ('build','deps') for x in p.relative_to(src).parts):z.write(p,p.relative_to(src.parent))
print('Packaged synchronized renderer and matching source.')
