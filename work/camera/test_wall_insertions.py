from pathlib import Path
import ctypes as C,json,itertools
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'root-anchor-test.dll'));f=d.nf_wall_insertions;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
def call(s,r,tail,ok=True):
 a=(C.c_uint32*len(s))(*s);b=(C.c_uint32*(2*len(r)))(*(v for row in r for v in row));out=(C.c_uint32*129)(*[0xdeadbeef]*129);prior=bytes(out)
 assert bool(f(a,len(s),b,len(r),tail,out))==ok
 if not ok:assert bytes(out)==prior;return
 return list(zip(list(out)[1:1+out[0]],list(out)[65:65+out[0]]))
# Enumerate every retained subset, inserting every omitted source. Original
# command gaps represent other commands whose ordering must be preserved.
s=[101,102,103,104,105];positive=0
for mask in range(32):
 r=[(source,2+i*3) for i,source in enumerate(s) if mask&(1<<i)]
 result=call(s,r,18);commands=[('old',i) for i in range(19)]
 for source,before in result:commands.insert(commands.index(('old',before)),('new',source))
 expected=[source for source in s if source not in dict(r)]
 assert [v for kind,v in commands if kind=='new']==expected
 for source,before in result:assert before==next((slot for value,slot in r if value>source),18)
 positive+=1
assert call([139910928,139910996],[(139910996,3)],4)==[(139910928,3)]
assert call([11,12],[],0)==[(11,0),(12,0)]
bad=[([1,1],[],3),([2,1],[(1,0),(2,1)],3),([1],[(1,0),(2,1)],3),([1],[(1,3)],3),([1,2],[(1,2),(2,1)],3),([1],[(1,0),(1,1)],3),([0],[],3),([1],[],258),(list(range(1,66)),[],3)]
for args in bad:call(*args,ok=False)
report=dict(result='PASS',positive_cases=positive+2,atomic_rejections=len(bad),scope='Native ordered insertion component; verified tail and scene/pass binding remain caller responsibilities.')
(p/'wall-insertion-tests.json').write_text(json.dumps(report,indent=2));print(report)

