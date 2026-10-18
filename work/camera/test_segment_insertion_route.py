from pathlib import Path
import ctypes as C,json,collections
from scene_segments import scene_segments
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'scene-segments-test.dll'));f=d.nf_segment_wall_insertions
f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
r=json.loads((p/'texture-provenance-tests.json').read_text());traces={x['serial']:x for x in r['dispatch_samples']};counts=collections.Counter();ambiguous=[]
def array(rows,width):return (C.c_uint32*(len(rows)*width))(*(v for row in rows for v in (row if row is not None else [0]*width)))
for sample in r['region_invocation_samples']:
 rows=sample['records'];t=traces[sample['scene']];commands=t['commands'];_,blocks=scene_segments(rows,commands,t['origins'],t['wall_passes'])
 a=array(rows,9);b=array(commands,6);o=array(t['origins'],12);wp=array(t['wall_passes'],3);segments=[s for block in blocks for s in block]
 all_sources={c[2] for c in commands if c[0]==2}
 for index,segment in enumerate(segments):
  if segment['kind'] not in ('wall','deferred'):continue
  begin,end=segment['begin'],segment['end'];sources=[commands[j][2] for j in range(begin,end)]
  outside={c[2] for j,c in enumerate(commands) if c[0]==2 and not begin<=j<end}
  unsupported=len(set(sources))!=len(sources) or bool(set(sources)&outside)
  def run(values):
   ss=(C.c_uint32*len(values))(*values);out=(C.c_uint32*129)(*[0xdeadbeef]*129);before=bytes(out)
   ok=f(a,len(rows),b,len(commands),o,wp,index,ss,len(values),out)
   if unsupported:assert not ok and bytes(out)==before;return None
   assert ok;return list(zip(out[1:1+out[0]],out[65:65+out[0]]))
  result=run(sources)
  if unsupported:
   counts['ambiguous_segments_rejected']+=1;ambiguous.append(dict(scene=sample['scene'],segment=index,sources=sources));continue
  assert result==[];counts['unchanged_segments_exact']+=1
  for gap in range(len(sources)+1):
   synthetic=0xf0000000+gap;assert synthetic not in all_sources
   values=sources[:gap]+[synthetic]+sources[gap:]
   assert run(values)==[(synthetic,begin+gap)]
   counts['synthetic_gap_insertions_exact']+=1
 counts['scenes']+=1
report=dict(result='PASS',counts=dict(counts),ambiguous=ambiguous,scope='Captured segment binding with synthetic additions in every gap. Synthetic sources test order only, not real assets/eligibility.')
(p/'segment-insertion-route-tests.json').write_text(json.dumps(report,indent=2));print(dict(counts))
