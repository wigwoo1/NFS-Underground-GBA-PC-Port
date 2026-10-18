"""Separate processes prevent fixed types contaminating ctypes weak cache."""
import ctypes as C,gc,time,json,weakref,statistics,sys,subprocess
from pathlib import Path
if len(sys.argv)>1:
 mode=sys.argv[1];fixed=(C.c_uint64*9,C.c_float*4) if mode=='fixed' else None
 refs=[];times=[]
 for trial in range(20):
  gc.collect();start=time.perf_counter_ns()
  for i in range(1000):
   a=(C.c_uint64*9)() if fixed is None else fixed[0]()
   b=(C.c_float*4)(.035,.05,.08,1) if fixed is None else fixed[1](.035,.05,.08,1)
   if i==0:refs.extend((weakref.ref(type(a)),weakref.ref(type(b))))
   assert len(a)==9 and a[0]==0 and len(b)==4
   a=b=None
  times.append(time.perf_counter_ns()-start)
 gc.collect();print(json.dumps(dict(mode=mode,dead_type_refs=sum(x() is None for x in refs),type_refs=len(refs),median_1000_calls_ns=statistics.median(times))))
else:
 rows=[json.loads(subprocess.check_output([sys.executable,__file__,mode],text=True)) for mode in ('dynamic','fixed','fixed','dynamic')]
 assert all(x['dead_type_refs']==40 if x['mode']=='dynamic' else x['dead_type_refs']==0 for x in rows)
 out=dict(result='PASS_FIXED_ABI_TYPE_LIFETIME',rows=rows,scope='Two fixed types, isolated child processes,20 explicit collections outside timed1000-call batches. Demonstrates bounded type retention and avoided collectible type definitions, not live GC/cadence benefit. Fresh arrays still allocated every call.')
 Path('work/camera/prototype-runs/renderer-fixed-types-component-20261009.json').write_text(json.dumps(out,indent=2));print(out)
