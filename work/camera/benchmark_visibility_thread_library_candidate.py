"""Matched serial builder construction; native rendering qualified separately."""
import gc,time,json,statistics,weakref
from pathlib import Path
import owned_visibility_thread_library_install_candidate as candidate
from owned_model_record_builder import ModelRecordBuilder
rom=bytes(0x647700);rows=[]
for trial in range(8):
 mode='original' if trial%2==0 else 'thread_local';init=candidate.original if mode=='original' else ModelRecordBuilder.__init__
 gc.collect();samples=[];refs=[]
 for i in range(50):
  obj=ModelRecordBuilder.__new__(ModelRecordBuilder);begin=time.perf_counter_ns();init(obj,rom);samples.append(time.perf_counter_ns()-begin)
  assert obj.rom is rom and obj.reciprocal.raw[:-1]==rom[0x627700:0x647700] and obj._scene_memory==[]
  refs.append(weakref.ref(obj.lib));obj=None
 gc.collect();dead=sum(x() is None for x in refs)
 assert dead==(50 if mode=='original' else 0),(mode,dead)
 rows.append(dict(mode=mode,median_ns=statistics.median(samples),dead_library_refs=dead))
out=dict(result='PASS_VISIBILITY_MATCHED_CONSTRUCTION_LIFETIME',rows=rows,median_original_ns=statistics.median(x['median_ns'] for x in rows if x['mode']=='original'),median_thread_local_ns=statistics.median(x['median_ns'] for x in rows if x['mode']=='thread_local'),scope='Eight alternating serial trials of50 private builder constructions, same ROM, collections outside timed constructor. Read-only wrappers retained perthread, private buffers validated. No live cadence/GC benefit proof.')
Path('work/camera/prototype-runs/visibility-thread-library-cost-20261009.json').write_text(json.dumps(out,indent=2));print(out)
