"""Sampled root binding versus independent structural ownership reference."""
from pathlib import Path
import ctypes as C,json,struct,collections
from scene_segments import scene_segments
p=Path('work/camera');d=C.CDLL(str((p/'sampled-root-binding-test.dll').resolve()));f=d.nf_sampled_root_binding;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
r=json.loads((p/'texture-provenance-wide-tests.json').read_text());traces={x['serial']:x for x in r['dispatch_samples']}
def pack(rows,width):return (C.c_uint32*(len(rows)*width))(*(v for row in rows for v in (row if row is not None else [0]*width)))
def reference(queue,rows,t):
 parents,blocks=scene_segments(rows,t['commands'],t['origins'],t['wall_passes']);calls=[]
 for phase in range(2):
  for qi in reversed(range(len(queue))):
   record=queue[qi]
   if record[2]>>16&(0x88 if phase else 8):continue
   calls.append((qi,phase,*record))
 bindings=[]
 for call in calls:
  region=call[2]&65535;phase=call[1]
  sampled=sum(c[1]==phase and c[2]&65535==region for c in calls)
  matches=[i for i,row in enumerate(rows) if parents[i] is None and row[5]==phase and row[0]&65535==region]
  if sampled>1 or len(matches)>1:status=3;owner=4294967295
  elif not matches:status=2;owner=4294967295
  else:
   owner=matches[0];status=4 if any(s['kind'] in ('child','model') for s in blocks[owner]) else 1
  bindings.append((*call,owner,status))
 removed=[i for i,row in enumerate(rows) if parents[i] is None and not any(c[1]==row[5] and c[2]&65535==row[0]&65535 for c in calls)]
 return bindings,removed
size=2+64*8+256;scenes=total=0
for sample in r['region_invocation_samples']:
 rows=sample['records'];t=traces[sample['scene']]
 queue=[tuple(row[:4]) for row in reversed(rows) if row[8]==0 and row[5]==0]
 # Captured eligible roots reconstruct a control schedule, not merged queue state.
 raw=b''.join(struct.pack('<4I',*q) for q in queue);a=pack(rows,9);c=pack(t['commands'],6);o=pack(t['origins'],12);wp=pack(t['wall_passes'],3);out=(C.c_uint32*size)()
 assert f(raw,len(queue),a,len(rows),c,len(t['commands']),o,wp,out),sample['scene']
 expected,removed=reference(queue,rows,t)
 assert out[0]==len(expected) and out[1]==len(removed)
 assert [tuple(out[2+i*8:10+i*8]) for i in range(out[0])]==expected
 assert list(out[514:514+out[1]])==removed
 scenes+=1;total+=out[0]
# Actual overflow sample includes reorder, omissions and repeated region87.
m=json.loads((p/'overflow-scene-171/manifest.json').read_text());rows=next(x['records'] for x in r['region_invocation_samples'] if x['scene']==171);t=m['captured'];raw=(p/'overflow-scene-171/visibility.bin').read_bytes()[256:256+22*16];queue=[struct.unpack_from('<4I',raw,i*16) for i in range(22)]
a=pack(rows,9);c=pack(t['commands'],6);o=pack(t['origins'],12);wp=pack(t['wall_passes'],3);out=(C.c_uint32*size)();assert f(raw,22,a,len(rows),c,len(t['commands']),o,wp,out)
expected,removed=reference(queue,rows,t);assert [tuple(out[2+i*8:10+i*8]) for i in range(out[0])]==expected and list(out[514:514+out[1]])==removed
statuses=collections.Counter(x[-1] for x in expected)
assert out[0]==28 and statuses[3]==4 and len(removed)==4
assert {rows[i][0]&65535 for i in removed}=={21,237}
for mode in ('capacity','caller','provenance','depth'):
 aa=pack(rows,9);oo=pack(t['origins'],12);count=22
 if mode=='capacity':count=33
 if mode=='caller':aa[4]=0
 if mode=='depth':aa[8]=1
 if mode=='provenance':oo[2]^=65535
 output=(C.c_uint32*size)(*[0xdeadbeef]*size);saved=bytes(output)
 assert not f(raw,count,aa,len(rows),c,len(t['commands']),oo,wp,output) and bytes(output)==saved,mode
report=dict(result='PASS',captured_control_scenes=scenes,captured_calls=total,sampled_calls=len(expected),sampled_status_counts=dict(statuses),removed_captured_roots=removed,removed_regions=[21,237],atomic_rejections=4,scope='Structural root bindings and explicit unresolved occurrences. Does not emit geometry or prove sampled child/object/road eligibility.')
(p/'sampled-root-binding-tests.json').write_text(json.dumps(report,indent=2));(p/'overflow-scene-171/root-bindings.json').write_text(json.dumps(dict(calls=expected,removed=removed),indent=2));print(report)
