import gc,json,struct,time,statistics,weakref
from pathlib import Path
import owned_motion_pairs as original
import owned_motion_pairs_bytes_candidate as candidate
from owned_segmented_frame_candidate import SegmentedFrame
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-source-context-20261007/failure-snapshot');fixtures=[(root/(n+'.frame.bin')).read_bytes() for n in ('older','newer')];checks=[]
def equal(a,b):
 assert {k:v for k,v in a.items() if k!='records'}=={k:v for k,v in b.items() if k!='records'}
 assert len(a['records'])==len(b['records'])
 for x,y in zip(a['records'],b['records']):
  assert (x['kind'],x['context'],x['key'])==(y['kind'],y['context'],y['key']);assert [bytes(v) for v in x['blocks']]==y['blocks']
for raw in fixtures:
 gn=struct.unpack_from('<I',raw,8)[0];seg=SegmentedFrame(raw[:40+gn],raw,40+gn)
 for f in (raw,seg):
  for keys in (False,True):
   a=original._decode_records(f,keys);b=candidate._decode_records(f,keys);equal(a,b)
   assert all(type(v)is bytes and not gc.is_tracked(v) for r in b['records'] for v in r['blocks'])
   checks.append(dict(segmented=isinstance(f,SegmentedFrame),keys=keys,records=len(b['records']),copied_block_bytes=sum(len(v) for r in b['records'] for v in r['blocks'])))
 ref=weakref.ref(seg);decoded=candidate._decode_records(seg);del f,seg;gc.collect();assert ref() is None
mutable=bytearray(fixtures[0]);a=original._decode_records(mutable);b=candidate._decode_records(mutable);assert all(type(v)is memoryview for r in b['records'] for v in r['blocks'])
bad=[b'',fixtures[0][:-1]]
for offset,value in ((0,0),(24,0),(44,9),(52,11),(56,0x100001)):
 x=bytearray(fixtures[0]);struct.pack_into('<I',x,offset,value);bad.append(bytes(x))
for f in bad:
 for decoder in (original._decode_records,candidate._decode_records):
  try:decoder(f)
  except (ValueError,struct.error):pass
  else:raise AssertionError('Malformed accepted')
bench={}
for name,decoder in (('original',original._decode_records),('candidate',candidate._decode_records)):
 durations=[]
 for i in range(300):
  t=time.perf_counter_ns();decoder(fixtures[i%2]);durations.append((time.perf_counter_ns()-t)/1e6)
 bench[name]=dict(median_ms=statistics.median(durations),max_ms=max(durations))
out=dict(result='PASS',checks=checks,malformed_cases=len(bad),segmented_owner_not_retained=True,mutable_alias_preserved=True,benchmark=bench,scope='Component byte/key/validation/owner parity; copies geometry blocks, bounded four-entry cache unchanged; no live performance or pixel certification')
Path('work/camera/metadata-bytes-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
