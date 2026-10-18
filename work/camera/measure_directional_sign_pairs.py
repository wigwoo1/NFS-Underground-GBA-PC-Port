"""Measure sign texture pair equivalence against actual sampled source frames."""
import ctypes as C,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
from scene_batches import batches
path=Path(sys.argv[1]);capture=json.loads(path.read_text());trace=Path(capture['trace']);assert hashlib.sha256(trace.read_bytes()).hexdigest()==capture['trace_sha256']
material=json.loads(Path(sys.argv[2]).read_text());wanted={tuple(c['interval']) for c in material['checks']};checks=[]
d=C.CDLL(str((Path('work/camera')/'native_wall.dll').resolve()));fn=d.nfs_wall_unshaded_addresses;fn.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
for batch in batches(trace):
 key=(batch['begin_refresh'],batch['end_refresh'])
 if key not in wanted:continue
 active=None;row=None
 for e in batch['events']:
  if e['pc'] in (0x030032f0,0x03004770):active=None
  if e['pc']==0x03000304:
   active=e['blocks'][5][0]
   if active==0x08574c3c:
    texture=np.frombuffer(e['blocks'][66][1],np.uint8).reshape(64,64);palette=np.frombuffer(e['blocks'][67][1],'<u2');even=texture[:,::2];odd=texture[:,1::2]
    row=dict(interval=key,texture_sha256=hashlib.sha256(texture.tobytes()).hexdigest(),texture_index_pair_differences=int((even!=odd).sum()),texture_color_pair_differences=int((palette[even]!=palette[odd]).sum()),texture_zero_pair_differences=int(((even!=0)!=(odd!=0)).sum()),reads=0,sampled_index_pair_differences=0,sampled_color_pair_differences=0,sampled_zero_pair_differences=0);checks.append(row)
  if active!=0x08574c3c or e['pc']!=0x030053e8:continue
  state=e['blocks'][75][1];words=struct.unpack('<17I',state);assert not(words[6] and words[11]>0x1b000)
  count=e['regs'][3];src=(C.c_uint*320)();dst=(C.c_uint*320)();assert fn(C.create_string_buffer(state),e['regs'][1],e['regs'][2],count,src,dst)
  for a in list(src)[:count]:
   offset=a-words[9];y,x=divmod(offset,64);assert 0<=y<64 and x%2==0
   v,w=int(texture[y,x]),int(texture[y,x+1]);row['reads']+=1;row['sampled_index_pair_differences']+=v!=w;row['sampled_color_pair_differences']+=int(palette[v])!=int(palette[w]);row['sampled_zero_pair_differences']+=bool(v)!=bool(w)
assert len(checks)==6 and sum(c['reads'] for c in checks)==19598
out=path.with_name(path.stem.replace('-verification','-sign-pair-equivalence')+'.json');out.write_text(json.dumps(dict(result='MEASURED',checks=checks,scope='Actual original texture frames and sampled even-column addresses versus adjacent odd columns. Pair equivalence only, not full GPU projected sampling or raster proof.'),indent=2));print(json.dumps(checks))
