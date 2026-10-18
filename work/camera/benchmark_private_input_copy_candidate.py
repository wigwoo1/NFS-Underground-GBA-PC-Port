from pathlib import Path
import sys,time,statistics,json,gc
sys.path.insert(0,str(Path('work/camera').resolve()))
from multiprocessing.shared_memory import SharedMemory
from owned_shared_input_read_copy_candidate import copy_private
assert gc.isenabled()
size=8711849;memory=SharedMemory(create=True,size=size);expected=(bytes(range(256))*((size+255)//256))[:size];memory.buf[:size]=expected
rows=[]
try:
 for repeat in range(40):
  row={}
  for name in (('baseline','candidate') if repeat%2==0 else ('candidate','baseline')):
   begin=time.perf_counter_ns();payload=bytes(memory.buf[:size]) if name=='baseline' else copy_private(memory,size);end=time.perf_counter_ns()
   assert payload==expected;row[name]=(end-begin)/1e6;del payload
  rows.append(row)
finally:memory.close();memory.unlink()
out=dict(result='PASS_EXACT_ALTERNATING_PRIVATE_COPY_BENCHMARK',pairs=len(rows),bytes=size,normal_gc=gc.isenabled(),medians_ms={k:statistics.median(x[k] for x in rows) for k in ('baseline','candidate')},rows=rows,scope='Component elapsed copy performance, includes allocation/scheduling; not live improvement proof.')
Path('outputs/nfsug-native-renderer/camera-research/native-child-copy-benchmark-20261009.json').write_text(json.dumps(out,indent=2));print(out['medians_ms'])
