"""Report exact wrapped ARM depths for a rejected captured source model."""
import json,struct,ctypes as C
from pathlib import Path
import owned_source_presentation_batch_candidate as batch
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples,projection_table_owner
original=batch.SourceFaceDeterminants;rejected=[]
def diagnostic(older,newer,d,table):
 try:return original(older,newer,d,table)
 except ValueError as e:
  if str(e)!='Original model projection rejected':raise
  native=table.native;d.nfs_model_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_int,C.c_int,C.c_void_p,C.c_void_p]
  for endpoint,row in enumerate((older,newer)):
   b=row['blocks'];m=struct.unpack('<12i',b[2]);vertices=list(struct.iter_unpack('<3h',b[4]));depths=[]
   for x,y,z in vertices:
    dot=(x*m[2]+y*m[5]+z*m[8])&0xffffffff;dot=dot-0x100000000 if dot&0x80000000 else dot;depths.append((m[11]+(dot>>14))&0xffffffff)
   scale=struct.unpack_from('<I',b[0],64)[0];center=struct.unpack_from('<2h',b[3],8);out=C.create_string_buffer(len(vertices)*4);rc=d.nfs_model_project(bytes(b[2]),bytes(b[4]),len(vertices),scale,*center,native,out)
   rejected.append(dict(key=list(row['key']) if isinstance(row['key'],tuple) else row['key'],endpoint=endpoint,matrix=list(m),vertices=len(vertices),native_result=rc,first_rejected=next((dict(index=i,unsigned_depth=v,signed_depth=v-0x100000000 if v&0x80000000 else v) for i,v in enumerate(depths) if v>0x6000),None),minimum_signed_depth=min(v-0x100000000 if v&0x80000000 else v for v in depths),maximum_signed_depth=max(v-0x100000000 if v&0x80000000 else v for v in depths)))
  raise
batch.SourceFaceDeterminants=diagnostic
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791505088433840800')");ns={}
try:
 exec(compile(source,'capture_setup','exec'),ns);PrecomputedSourceWorldSamples(ns['prepared'],(.2,.4,.6,.8))
except ValueError as e:assert str(e)=='Original model projection rejected'
finally:
 for k in ('prepared','history'):
  if ns.get(k):ns[k].close()
assert rejected
out=dict(result='REJECTED_ENDPOINT_DEPTH_DIAGNOSTIC',models=rejected,scope='Exact captured matrices/vertices and unsigned32 wrapped depth domain; explains native reject, not recovered visibility policy.')
Path('work/camera/prototype-runs/native-rejected-depth-20261008.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
