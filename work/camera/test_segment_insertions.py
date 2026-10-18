from pathlib import Path
import ctypes as C,json
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'scene-segments-test.dll'));f=d.nf_segment_wall_insertions
f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
# Empty child and model remain barriers between same-phase wall runs.
rows=[1,2,3,4,0,0,0,4,0,5,6,7,8,0,0,1,1,1]
commands=[2,0,100,0,0,0,2,1,200,0,0,0,3,0xffffffff,0,0,0,0,2,3,300,0,0,0]
origins=[0,0,1,2,3,4,0,0,0,0,0,0]*4;phases=[0,0,0]*4
arr=lambda v:(C.c_uint32*len(v))(*v)
a,b,o,w=map(arr,(rows,commands,origins,phases))
def check(segment,sources,expected):
 out=(C.c_uint32*129)(*[0xdeadbeef]*129);prior=bytes(out);ss=arr(sources)
 ok=f(a,2,b,4,o,w,segment,ss,len(sources),out)
 if expected is None:assert not ok and bytes(out)==prior
 else:assert ok and list(zip(out[1:1+out[0]],out[65:65+out[0]]))==expected
check(0,[99,100,101],[(99,0),(101,1)])
check(2,[199,200,201],[(199,1),(201,2)])
check(4,[299,300,301],[(299,3),(301,4)])
for segment,sources in ((0,[100,200]),(2,[100,200]),(2,[200,300]),(1,[101]),(3,[101]),(5,[101]),(0,[]),(0,[100,100])):check(segment,sources,None)
report=dict(result='PASS',positive_cases=3,atomic_rejections=8,scope='Segment-local extension preserves child/model barriers. New-source eligibility remains caller obligation; empty/new segments unsupported.')
(p/'segment-insertion-tests.json').write_text(json.dumps(report,indent=2));print(report)
