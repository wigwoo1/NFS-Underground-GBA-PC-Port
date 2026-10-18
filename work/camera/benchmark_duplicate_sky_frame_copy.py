"""Producer duplicate frame copy benchmark: exact current immutable bytes."""
import ctypes as C,time,json,statistics
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-stall-exact-capture-20261008')
rows=[]
for name in ('older','newer'):
 owned=(cp/'scene-inputs'/f'{name}.frame.bin').read_bytes();native=C.create_string_buffer(owned);times=[]
 for i in range(120):
  start=time.perf_counter_ns();duplicate=C.string_at(native,len(owned));end=time.perf_counter_ns();assert duplicate==owned
  if i>=20:times.append((end-start)/1e6)
 rows.append(dict(endpoint=name,bytes=len(owned),copies_verified=120,median_duplicate_copy_ms=statistics.median(times),max_duplicate_copy_ms=max(times)))
r=dict(result='PASS',rows=rows,scope='Avoided duplicate immutable byte copy only; does not verify sky attachment/rendering/live cadence. Regenerated path uses adapted output instead of original input.')
(cp/'duplicate-sky-frame-copy.json').write_text(json.dumps(r,indent=2));print(r)
