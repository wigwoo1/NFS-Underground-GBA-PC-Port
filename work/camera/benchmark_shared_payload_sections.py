import pickle,time,json,struct
from pathlib import Path
from owned_shared_blob import SharedBlobOwner,_HEADER,_MAGIC,read_shared_blob
from owned_shared_payload import write_payload,read_payload
owner=SharedBlobOwner(16*1024*1024);payload={'tails':[bytes(range(256))*32768],'samples':[(.5,(b'prefix',0,b'camera',None,b'',{'roads':12}))]};times=[[],[]];checks=0;serial=0
try:
 for repeat in range(12):
  for mode in (repeat%2,1-repeat%2):
   serial+=1;a=time.perf_counter_ns()
   if mode==0:
    blob=pickle.dumps(payload,protocol=5);owner.memory.buf[_HEADER.size:_HEADER.size+len(blob)]=blob;_HEADER.pack_into(owner.memory.buf,0,_MAGIC,1,serial,len(blob));descriptor=(owner.memory.name,1,serial,len(blob));result=pickle.loads(read_shared_blob(descriptor,1))
   else:descriptor=write_payload(owner.memory,payload,1,serial);result=read_payload(descriptor,1)
   times[mode].append((time.perf_counter_ns()-a)/1e6);assert result==payload;checks+=1
finally:owner.close()
out=dict(result='PASS',exact_comparisons=checks,whole_pickle_total_ms=sum(times[0]),raw_sections_total_ms=sum(times[1]),scope='Alternating8MBsameprocess transport/write/copy/decode component; excludes IPC/child scheduling and live60fps')
Path('work/camera/shared-payload-section-benchmark.json').write_text(json.dumps(out,indent=2));print(out)
