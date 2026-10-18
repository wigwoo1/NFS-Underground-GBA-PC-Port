from pathlib import Path
import ctypes as C,json,struct
from region_anchors import root_anchors
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'root-anchor-test.dll'));f=d.nf_root_region_anchors
f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
report=json.loads((p/'texture-provenance-tests.json').read_text());records=next(x['records'] for x in report['region_invocation_samples'] if x['scene']==143)
batch=(p/'object-replay-143-sampled-queue.bin').read_bytes();sample=[]
for qi in reversed(range(struct.unpack_from('<I',batch)[0])):
 r=struct.unpack_from('<8H',batch,8+qi*2068)
 if not r[5]&8:sample.append(r[0])
roots=[(r[0]&65535,r[6],r[7]) for r in records if r[4]==0x03004da4 and r[8]==0 and r[5]==0]
def call(sample,roots,valid):
 a=(C.c_uint32*len(sample))(*sample);b=(C.c_uint32*(len(roots)*3))(*(v for r in roots for v in r));out=(C.c_uint32*21)(*[0xdeadbeef]*21);prior=bytes(out)
 ok=f(a,len(sample),b,len(roots),out)
 assert bool(ok)==valid
 if not valid:assert bytes(out)==prior;return
 assert out[0]==len(sample);return list(out)[1:1+len(sample)]
slots=call(sample,roots,True);assert slots==list(root_anchors(sample,records).values())
# Existing calls and newly entering calls before each root, preserving gaps.
for i in range(len(roots)):
 seq=[r[0] for r in roots];seq.insert(i,60000+i);result=call(seq,roots,True);assert result[i]==roots[i][1]
cases=[(sample+sample[:1],roots),(sample[::-1],roots),([r for r in sample if r!=21],roots),(sample+[999],roots),(sample,roots+roots[:1]),(sample,[(roots[0][0],3,2)]+roots[1:]),(sample,[(roots[0][0],0,258)]+roots[1:]),(sample*2,roots)]
for a,b in cases:call(a,b,False)
result=dict(result='PASS',sample=sample,slots=slots,positive_cases=1+len(roots),atomic_rejections=len(cases),scope='Native conservative root block slots; not nested/surface eligibility or live integration.')
(p/'native-root-anchor-tests.json').write_text(json.dumps(result,indent=2));print(result)
