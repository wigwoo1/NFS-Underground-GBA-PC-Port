"""Captured consecutive full-frame HUD cache parity, preserving each refresh."""
import ctypes as C,json,hashlib
from pathlib import Path
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());items=r['wall_diagnostic_frames'];assert len(items)>=2
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/hud-borrow-20261008');references=[];checks=[];rgb=C.create_string_buffer(3840*2160*3)
for name in ('owned-gpu-segmented-4k-candidate.dll','owned-gpu-hud-borrow-candidate.dll'):
 d=C.CDLL(str((p/name).resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];assert d.nf_owned_gpu_window(0)==0
 try:
  for index,item in enumerate(items):
   raw=Path(item['regenerated']).read_bytes();f=C.create_string_buffer(raw)
   assert d.nf_owned_gpu_draw(f,len(raw))==0,(name,index)
   assert d.nf_owned_gpu_read(rgb,len(rgb))==0
   digest=hashlib.sha256(rgb.raw).hexdigest()
   if not checks:references.append(digest)
   else:assert digest==references[index],(index,'Complete4K mismatch')
   if name.endswith('hud-borrow-candidate.dll'):
    stats=(C.c_uint64*2)();assert d.nf_hud_visual_cache_stats(stats)
    results.append(dict(refresh=item['refresh'],sha256=digest,hits=stats[0],misses=stats[1]))
 finally:assert d.nf_owned_gpu_close()
 if not checks:checks.append(name);results=[]
assert len({x['refresh'] for x in results})==len(items)
out=dict(result='PASS_CAPTURED_SEQUENCE_4K',checks=results,pixels_per_frame=8294400,scope='Actual consecutive regenerated captured complete frames, direct endpoint renderer draws in persistent separate contexts, complete4KRGB exact against unchanged segmentedGPU. No interpolated source callback or live timing/scanout proof.')
(cp/'captured-sequence-parity.json').write_text(json.dumps(out,indent=2));print(dict(result=out['result'],frames=len(results),cache=results[-1]))
