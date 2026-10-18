import ctypes as C,gc,time,json,statistics,weakref,sys,subprocess
from pathlib import Path
if len(sys.argv)>1:
 mode=sys.argv[1]
 if mode=='fixed':
  from owned_endpoint_road_fixed_types_candidate import private_state,Edges,Stream
 refs=[];times=[];data=bytes(range(256))
 for trial in range(20):
  gc.collect();begin=time.perf_counter_ns()
  for i in range(1000):
   if mode=='fixed':a=private_state(data);b=Edges();c=Stream()
   else:a=C.create_string_buffer(data,256);b=C.create_string_buffer(1664);c=C.create_string_buffer(1536)
   if i==0:refs.extend(weakref.ref(type(x)) for x in (a,b,c))
   a=b=c=None
  times.append(time.perf_counter_ns()-begin)
 gc.collect();print(json.dumps(dict(mode=mode,median_1000_ns=statistics.median(times),dead_type_refs=sum(x() is None for x in refs))))
else:
 rows=[json.loads(subprocess.check_output([sys.executable,__file__,m],text=True)) for m in ('original','fixed','fixed','original')]
 assert all(x['dead_type_refs']==(60 if x['mode']=='original' else 0) for x in rows)
 out=dict(result='PASS_ROAD_FIXED_TYPE_LIFETIME_COST',rows=rows,scope='Isolated children avoid type-cache contamination;20 collections outside1000-call batches. Fresh private buffers every visit, three fixed type definitions retained. Component cost only, no live cadence benefit.')
 Path('work/camera/prototype-runs/road-fixed-types-cost-20261009.json').write_text(json.dumps(out,indent=2));print(out)
