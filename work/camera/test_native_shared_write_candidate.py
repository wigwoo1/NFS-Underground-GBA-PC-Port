import json,time,statistics,sys
from pathlib import Path
from owned_shared_blob import SharedBlobOwner,_HEADER
from owned_shared_payload import write_payload as original,read_payload
from owned_native_shared_write_candidate import write_payload as native
report=json.loads(Path(sys.argv[1]).read_text());row=report['world_preparation_stage_samples'][-1]
# Real captured endpoint byte owners, supplemented with explicit offset/empty spans.
folder=Path(report['live_preparation_profiles'][0]['capture'])
files=list(folder.glob('*.bin'));assert files
payload={'captured':tuple(p.read_bytes() for p in files),'offsets':(memoryview(b'prefix-tail')[7:],memoryview(b'')), 'metadata':(1,None,True,.25)}
owner=SharedBlobOwner(64*1024*1024);timings={'original':[],'native':[]};checks=0
try:
 for i in range(24):
  for name,writer in (('original',original),('native',native)) if i%2==0 else (('native',native),('original',original)):
   begin=time.perf_counter_ns();descriptor=writer(owner.memory,payload,3,1);timings[name].append(time.perf_counter_ns()-begin)
   decoded=read_payload(descriptor,3,owner.memory)
   assert decoded['captured']==payload['captured'] and decoded['offsets']==(b'tail',b'');checks+=1
   snapshot=bytes(owner.memory.buf[:_HEADER.size+descriptor[3]])
   if name=='original':expected=snapshot
   else:
    original(owner.memory,payload,3,1);assert snapshot==bytes(owner.memory.buf[:len(snapshot)]);checks+=1
 # Native exporter releases all mapping references before close; decoded bytes survive reuse.
 native(owner.memory,{'replacement':b'new'},3,2);assert decoded['offsets']==(b'tail',b'')
finally:owner.close()
out=dict(result='PASS_NATIVE_SHARED_WRITE_CAPTURED_PARITY',checks=checks,payload_bytes=descriptor[3],median_ms={k:statistics.median(v)/1e6 for k,v in timings.items()},scope='Alternating captured binary payload writes, excludes metadata reconstruction/live scheduling; no cadence claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
