"""Measure exact scanline-owned HUD block repetition without discarding state."""
from pathlib import Path
import json,sys
prefix=Path(sys.argv[1]);reports=[]
for path in sorted(prefix.parent.glob(prefix.name+'*-hud.bin')):
 data=path.read_bytes();stride=34944;assert len(data)==160*stride
 blocks=[data[i*stride:(i+1)*stride] for i in range(160)];pool=[];indices=[];headers=[]
 for row in blocks:
  headers.append(row[:128]);payload=row[128:]
  if payload not in pool:pool.append(payload)
  indices.append(pool.index(payload))
 rebuilt=b''.join(h+pool[i] for h,i in zip(headers,indices));assert rebuilt==data
 compact=160*(128+4)+sum(len(v) for v in pool)
 reports.append(dict(file=str(path),rows=160,full_bytes=len(data),unique_obj_palette_oam_blocks=len(pool),exact_pool_bytes=compact,saved_bytes=len(data)-compact,full_reconstruction_exact=True))
assert reports
out=dict(result='HUD_EXACT_BLOCK_REPETITION',reports=reports,scope='Retained fixture byte proof only; no live compressed owner or renderer integration.')
Path(str(prefix)+'-hud-repetition.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
