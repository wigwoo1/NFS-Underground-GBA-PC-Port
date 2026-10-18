import sys,time,json,statistics
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
from owned_shared_input_read_copy_candidate import copy_private
size=8508532;memory=SharedMemory(create=True,size=size);expected=(bytes(range(256))*((size+255)//256))[:size];memory.buf[:]=expected;times={'baseline':[],'native':[]}
try:
 for repeat in range(12):
  for label in (('baseline','native') if repeat%2==0 else ('native','baseline')):
   begin=time.perf_counter_ns();value=bytes(memory.buf[:size]) if label=='baseline' else copy_private(memory,size);times[label].append((time.perf_counter_ns()-begin)/1e6);assert value==expected
 memory.buf[:]=b'Z'*size;assert value==expected
finally:memory.close();memory.unlink()
result=dict(result='PASS_PRIVATE_COPY_COMPONENT',bytes=size,rounds=12,median_ms={k:statistics.median(v) for k,v in times.items()},scope='Alternating real request-sized private bytes copies, exact parity/detached ownership; no live cadence qualification.')
Path(sys.argv[1]).write_text(json.dumps(result,indent=2));print(result)
