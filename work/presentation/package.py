from pathlib import Path
import csv,json,statistics,zipfile,shutil
out=Path('outputs/nfsug-native-renderer');src=Path('work/v2/package/NFSUG-Native-Renderer-source')
r=list(csv.DictReader(open('work/presentation/default-frames.csv')))[15:];t=[float(x['seconds'])for x in r];ds=[b-a for a,b in zip(t,t[1:])];new=sum(a['hash']!=b['hash']for a,b in zip(r,r[1:]));report={'seconds':t[-1]-t[0],'changing_rendered_images':new,'changing_image_fps':new/(t[-1]-t[0]),'median_ms':statistics.median(ds)*1000,'p95_ms':sorted(ds)[int(len(ds)*.95)]*1000,'mode60_active_all_frames':all(x['mode60']=='1'for x in r),'scope':'1000x600 region of the rendered 4K framebuffer during a paced test, with readback overhead. Does not measure monitor scanout or establish identical user-visible behavior.'};(out/'presentation-audit.json').write_text(json.dumps(report,indent=2));print(report)
for a,b in [('host.c','main.c'),('probe.c','bridge.c')]:
 (src/b).write_text(Path('work',a).read_text().replace('../outputs/nfsug-research/','').replace('work/span-cycles.csv','span-cycles.csv'))
for n in ['gpu.c','gpu.h']:shutil.copy2(Path('work/v2')/n,src/'v2'/n)
(src/'Build.ps1').write_text((src/'Build.ps1').read_text().replace('NFSUG-60Hz-Lab.exe','NFSUG-60Hz-Active.exe'))
notes='''# 60-Hz Active build

Launch NFSUG-60Hz-Active.exe. The experiment is ON by default during races; there is no need to press F4. F4 switches to original timing and back. Demos/menus keep their original simulation timing. Physics differences described in 60HZ-LAB.md remain unresolved.

The title now reports motion fps based on changes to presented captured geometry, separately from display fps. The startup-diagnostic.log also records the mode and both rates. This makes it possible to distinguish an inactive experiment from performance or presentation issues. The agent has not reproduced the user's report of slow motion with the experiment active; this build does not claim to fix an unidentified camera bug.

An optional --audit-frames file.csv hashes a 1000x600 region of the actual 4K framebuffer at each presentation. The paced test measured approximately 59 changing rendered images per second. The original GBA refresh is 59.73 Hz, while the Windows presentation loop targets 60 Hz; occasional repeated frames and timing jitter remain possible. Rendered-image measurements are not monitor scanout measurements.

The corresponding source is NFSUG-60Hz-Active-source.zip. --original-timing starts with the experiment disabled. F3 remains the rendering comparison key. The synchronized renderer and startup fallback are retained.
'''
(out/'60HZ-ACTIVE.md').write_text(notes);(src/'60HZ-ACTIVE.md').write_text(notes);shutil.copy2(out/'presentation-audit.json',src/'tests/presentation-audit.json')
with zipfile.ZipFile(out/'NFSUG-60Hz-Active-source.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in src.rglob('*'):
  if p.is_file() and not any(x in ('build','deps') for x in p.relative_to(src).parts):z.write(p,p.relative_to(src.parent))
