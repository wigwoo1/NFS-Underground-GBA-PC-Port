import sys,json,time,gc,statistics,hashlib
from pathlib import Path
mode=sys.argv[1]
if mode=='original':from owned_source_segmented_draw_candidate import OwnedSourceDraw
elif mode=='cache':from owned_source_draw_type_reuse_candidate import OwnedSourceDraw
else:raise ValueError(mode)
p=Path('work/camera/prototype-runs/draw-construction-fixture-20261009');frame=(p/'base.bin').read_bytes();items=json.loads((p/'inputs.json').read_text());out={}
for release in (False,True):
 gc.collect();start=[x['collections'] for x in gc.get_stats()];samples=[];owned=None
 for i in range(1050):
  x=items[i%len(items)];begin=time.perf_counter_ns();owned=OwnedSourceDraw(frame,x['camera'],x['models'],x['bounds'],x['count'],*x['sources'],x['alpha'],x['offsets'],x['mask'],x['total']);end=time.perf_counter_ns()
  if i>=50:samples.append(end-begin)
  if release:owned=None
 out[str(release)]=dict(median_ms=statistics.median(samples)/1e6,max_ms=max(samples)/1e6,collections=[x['collections']-v for x,v in zip(gc.get_stats(),start)],samples=len(samples))
print(json.dumps(dict(mode=mode,frame_sha256=hashlib.sha256(frame).hexdigest(),results=out)))
