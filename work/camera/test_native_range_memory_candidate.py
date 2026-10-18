import sys,time,statistics,json,ctypes as C
from pathlib import Path
sys.argv=['fixture','work/camera/prototype-runs/child-scene-1791637661169682300']
setup=Path('work/camera/test_geometry_process_codec_component.py').read_text().split('from owned_progressive_source_samples_candidate import')[0]
exec(compile(setup,'range_capture','exec'));history.close()
from owned_closed_scene_memory import ClosedSceneMemory
from owned_native_range_memory_candidate import NativeRangeMemory,native,Range
rows={False:[],True:[]};reference=tuple(ClosedSceneMemory(s.graph,rom) for s in scenes)
for iteration in range(16):
 for selected in ((False,True) if iteration%2==0 else (True,False)):
  begin=time.perf_counter_ns();values=tuple((NativeRangeMemory if selected else ClosedSceneMemory)(s.graph,rom) for s in scenes);rows[selected].append((time.perf_counter_ns()-begin)/1e6)
  for old,new in zip(reference,values):
   assert (old._ranges,old._starts,old.owned_byte_count)==(new._ranges,new._starts,new.owned_byte_count)
   assert all(new.read(a,len(data))==old.read(a,len(data)) for a,data in old._ranges)
g=scenes[0].graph.graph;blobs=(g.context,g.geometry,g.offsets,g.materials);output=(Range*1)();C.memset(output,0x5a,C.sizeof(output));before=bytes(output)
args=tuple(v for blob in blobs for v in (blob,len(blob)))
assert native(*args,output,1)==-1 and bytes(output)==before
bad=list(args);bad[3]-=1
assert native(*bad,output,1)==-1 and bytes(output)==before
rejections=2
for index,value in ((1,100),(5,len(g.offsets)-1),(7,len(g.materials)-1)):
 bad=list(args);bad[index]=value
 assert native(*bad,output,1)==-1 and bytes(output)==before
 rejections+=1
context=bytearray(g.context);struct.pack_into('<I',context,84,0xfffffff0)
bad=list(args);bad[0]=bytes(context)
assert native(*bad,output,1)==-1 and bytes(output)==before
rejections+=1
out=dict(result='PASS_NATIVE_RANGE_MEMORY_COMPONENT',rounds=16,constructors=64,median_pair_ms={str(k):statistics.median(v) for k,v in rows.items()},exact_ranges_and_reads=True,capacity_and_truncation_rejected_without_write=True,rejections=rejections,scope='Captured two-scene complete constructor and reads; native collector only, original merge/read unchanged. No malformed address/face/overlay broader guards, full4K or live qualification yet.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/native-range-memory-component.json').write_text(json.dumps(out,indent=2));print(out)
