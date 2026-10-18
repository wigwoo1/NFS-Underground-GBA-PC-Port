import struct,json
from pathlib import Path
from owned_motion_pairs import _decode_records
from owned_model_small_block_bytes_candidate import decode
from owned_segmented_frame_candidate import SegmentedFrame
def frame(kind=3,sizes=None,count=12):
 sizes=sizes or [0,1,4096,4097]+[3]*8
 g=struct.pack('<4I',0x3147534e,kind,123,count)+b''.join(struct.pack('<I',n)+bytes([i])*n for i,n in enumerate(sizes))
 return struct.pack('<6I2Q',0x3346474e,7,len(g),0,0,0,1,7*280896)+g
def sig(r):return (r['refresh'],r['epoch'],r['ticks'],[(x['kind'],x['context'],x['key'],[bytes(b) for b in x['blocks']]) for x in r['records']])
checks=0
for kind in [1,2,3]:
 for sizes in [None,[1048576]+[0]*11]:
  f=frame(kind,sizes)
  for mode in [True,False,'models']:
   for owner in [f,SegmentedFrame(f,f,len(f)),bytearray(f)]:
    a=_decode_records(owner,mode);b=decode(owner,mode);assert sig(a)==sig(b);checks+=1
    if type(owner) is bytearray:assert all(isinstance(x,memoryview) for x in b['records'][0]['blocks'])
   result=decode(f,mode);del f;assert sig(result)==sig(b)
   f=frame(kind,sizes)
errors=0
valid=frame();bad=[valid[:39],valid[:40],frame(4),frame(count=11),valid[:-1],valid[:56]+struct.pack('<I',1048577)+valid[60:],valid[:56]+struct.pack('<I',999999)+valid[60:]]
# Emptygeometry is valid; omit valid header-only zeroextent unless envelope mismatches.
for f in bad:
 outcomes=[]
 for fn in [_decode_records,decode]:
  try:fn(f,'models')
  except Exception as e:outcomes.append((type(e).__name__,str(e)))
  else:raise AssertionError('Malformed accepted')
 assert outcomes[0]==outcomes[1];errors+=1
out=dict(result='PASS_SMALL_MODEL_BLOCK_BOUNDARIES',exact_cases=checks,malformed_cases=errors,scope='All3kinds/sourcekeymodes/bytes-segmented-mutable owners,0/4096/4097/1MiB sizes, original validationerrors andretainedpayload lifetime. Syntheticrecordsnot fullnativefidelity.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/small-model-block-edges.json').write_text(json.dumps(out,indent=2));print(out)
