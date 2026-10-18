from pathlib import Path
import ctypes as C,json
from scene_segments import scene_segments
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'scene-segments-test.dll'));f=d.nf_scene_segments;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
r=json.loads((p/'texture-provenance-tests.json').read_text());traces={x['serial']:x for x in r['dispatch_samples']}
size=2+256+257+1024*4
names={'wall':1,'road':2,'deferred':3,'child':4,'model':5}
scenes=segments=0
def array(rows,width):return (C.c_uint32*(len(rows)*width))(*(v for row in rows for v in (row if row is not None else [0]*width)))
for sample in r['region_invocation_samples']:
 rows=sample['records'];t=traces[sample['scene']];parents,blocks=scene_segments(rows,t['commands'],t['origins'],t['wall_passes'])
 a=array(rows,9);b=array(t['commands'],6);o=array(t['origins'],12);wp=array(t['wall_passes'],3);out=(C.c_uint32*size)()
 assert f(a,len(rows),b,len(t['commands']),o,wp,out)
 assert out[0]==len(rows) and list(out)[2:2+len(rows)]==[4294967295 if x is None else x for x in parents]
 for i,block in enumerate(blocks):
  begin,end=out[258+i],out[259+i]
  expected=[(names[s['kind']],s['begin'],s['end'],s.get('child',4294967295)) for s in block]
  actual=[tuple(out[515+j*4:519+j*4]) for j in range(begin,end)]
  assert actual==expected
 scenes+=1;segments+=out[1]
# Mutate final valid fixture: depth gap, interval overflow, foreign provenance.
rejections=0
for mode in ('depth','interval','provenance','capacity'):
 aa=array(rows,9);oo=array(t['origins'],12);output=(C.c_uint32*size)(*[0xdeadbeef]*size);before=bytes(output);n=len(rows)
 if mode=='depth':aa[8]=1
 if mode=='interval':aa[7]=258
 if mode=='capacity':n=257
 if mode=='provenance':
  j=next(j for j,c in enumerate(t['commands']) if c[0]!=3);oo[j*12+2]^=65535
 assert not f(aa,n,b,len(t['commands']),oo,wp,output) and bytes(output)==before
 rejections+=1
report=dict(result='PASS',scenes=scenes,segments=segments,atomic_rejections=rejections,scope='Native/Python captured segmentation parity; not sampled visibility or live gameplay.')
(p/'native-scene-segment-tests.json').write_text(json.dumps(report,indent=2));print(report)
