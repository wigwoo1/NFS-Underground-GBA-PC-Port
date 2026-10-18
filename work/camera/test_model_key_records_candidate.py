import struct,json,threading
from pathlib import Path
from owned_motion_pairs import records as original
from owned_model_key_records_candidate import records,_model_record_cache
from owned_segmented_frame_candidate import SegmentedFrame
folder=Path('work/camera/prototype-runs/fullscene-failure-1791576492416199100')
frames=[(folder/(label+'.frame.bin')).read_bytes() for label in ('older','newer')]
checks=0
for frame in frames:
 expected=original(frame);actual=records(frame)
 assert (actual['refresh'],actual['epoch'],actual['ticks'])==(expected['refresh'],expected['epoch'],expected['ticks'])
 for a,b in zip(actual['records'],expected['records']):
  assert a['kind']==b['kind'] and a['context']==b['context'] and [bytes(x) for x in a['blocks']]==[bytes(x) for x in b['blocks']]
  assert a['key']==b['key'] if a['kind']==3 else a['key'] is None
 # Mutating caller-owned metadata must not poison retained immutable metadata.
 actual['records'][0]['blocks'].clear();actual['records'][0]['kind']=99;actual['records'].clear()
 again=records(frame);assert len(again['records'])==len(expected['records']) and again['records'][0]['kind']==expected['records'][0]['kind']
 gn=struct.unpack_from('<I',frame,8)[0];seg=SegmentedFrame(frame[:40+gn],frame,40+gn)
 assert [(x['kind'],x['key']) for x in records(seg)['records']]==[(x['kind'],x['key']) for x in again['records']]
 checks+=1
for i in range(8):records(bytes(bytearray(frames[i%2])))
assert len(_model_record_cache.entries)==4
main_owners=tuple(id(x[0]) for x in _model_record_cache.entries);child=[]
def worker():
 assert not getattr(_model_record_cache,'entries',[])
 records(frames[0]);child.append(len(_model_record_cache.entries))
t=threading.Thread(target=worker);t.start();t.join();assert child==[1] and main_owners==tuple(id(x[0]) for x in _model_record_cache.entries)
invalid=[]
f=frames[0]
for offset,value in ((0,0),(8,len(f)),(24,0),(32,0),(40,0),(52,11),(56,0x100001)):
 bad=bytearray(f);struct.pack_into('<I',bad,offset,value);invalid.append(bytes(bad))
invalid.append(f[:39])
for bad in invalid:
 try:records(bad)
 except ValueError:pass
 else:raise AssertionError('Malformed frame accepted')
out=dict(result='PASS_MODEL_KEYS_OWNERSHIP_VALIDATION',source_endpoints=checks,invalid_rejected=len(invalid),cache_capacity=4,thread_isolation=True,caller_mutation_isolation=True)
Path('outputs/nfsug-native-renderer/camera-research/model-key-records-regression-20261009.json').write_text(json.dumps(out,indent=2));print(out)
