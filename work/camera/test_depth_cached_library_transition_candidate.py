import json
from pathlib import Path
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
from owned_source_native_depth_rectangle_candidate import SourceFaceDeterminants as Base
import struct
endpoint_checks=[]
def build(a,b,d,table):
 c=SourceFaceDeterminants(a,b,d,table)
 if c.single_endpoint:
  for i,row in enumerate((a,b)):
   raw=struct.unpack('<12i',row['blocks'][2]);m=tuple(v/16384 if j<9 else float(v) for j,v in enumerate(raw));rect=(-32768,-32768,32768,32768)
   actual=c.combined_decisions(m,i,rect)
   if c.endpoint_valid[i]:assert actual==Base(row,row,d,table).combined_decisions(m,0,rect)
   else:assert not any(actual[0]) and all(x==4 for x in actual[1])
   endpoint_checks.append(dict(endpoint=i,valid=c.endpoint_valid[i],faces=len(c.faces)))
 return c
batch.SourceFaceDeterminants=build
from owned_precomputed_source_cached_library_candidate import PrecomputedSourceWorldSamples,source_library_owner
assert source_library_owner() is source_library_owner()
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791505088433840800')");ns={};cached=None
try:
 exec(compile(source,'capture_setup','exec'),ns);cached=PrecomputedSourceWorldSamples(ns['prepared'],(.2,.4,.6,.8),trace=True)
 checks=[dict(alpha=a,selected_faces=cached.source_masks[a][3]['selected_faces']) for a in cached.samples]
 assert len(checks)==4
finally:
 if cached:cached.close()
 for name in ('prepared','history'):
  if ns.get(name):ns[name].close()
out=dict(result='PASS_CAPTURED_DEPTH_TRANSITION_PREPARATION',checks=checks,endpoint_checks=endpoint_checks,scope='Four source preparation samples on failed captured pair; single valid endpoint residual candidate. No GPU pixel or live/fractional visibility fidelity proof.')
Path('work/camera/prototype-runs/native-depth-cached-library-transition-20261008.json').write_text(json.dumps(out,indent=2));print(out)
