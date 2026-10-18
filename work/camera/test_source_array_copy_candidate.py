import ctypes as C,time,statistics,json,runpy
from pathlib import Path
from owned_source_array_copy_candidate import clone_array,install,copy_counts
checks=[];timing={}
for t,values in [(C.c_double,[i*.125 for i in range(1728)]),(C.c_uint32,list(range(145))),(C.c_int32,list(range(-6,6)))]:
 a=(t*len(values))(*values);b=clone_array(t,a);assert bytes(a)==bytes(b) and C.addressof(a)!=C.addressof(b);a[0]+=1;assert a[0]!=b[0];checks.append(t.__name__)
assert list(clone_array(C.c_double,(1.,2.,3.)))==[1.,2.,3.]
a=(C.c_double*1728)(*[i*.125 for i in range(1728)])
for name,api in [('baseline',lambda t,x:(t*len(x))(*x)),('bulk',clone_array)]:
 times=[]
 for i in range(220):
  start=time.perf_counter_ns();b=api(C.c_double,a);end=time.perf_counter_ns();assert bytes(a)==bytes(b)
  if i>=20:times.append((end-start)/1e6)
 timing[name]=statistics.median(times)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/combined-sky-reuse-live-20261008');(cp/'private-array-copy.json').write_text(json.dumps(dict(result='PASS',private_copy_types=checks,timing_median_ms=timing,scope='Native private copies retain bytes and mutation independence; component benchmark only.'),indent=2));print(timing)
install();before=copy_counts['bulk'];runpy.run_path('work/camera/test_segmented_original_gpu_parity.py',run_name='__main__');assert copy_counts['bulk']>before;print('Verified candidate bulk-copy calls during full-scene oracle:',copy_counts['bulk']-before)

