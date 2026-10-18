import json
from pathlib import Path
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
from owned_source_native_depth_rectangle_candidate import SourceFaceDeterminants as Base
import struct,ctypes as C
endpoint_checks=[]
def build(a,b,d,table):
 c=SourceFaceDeterminants(a,b,d,table)
 if c.single_endpoint:
  for i,row in enumerate((a,b)):
   raw=struct.unpack('<12i',row['blocks'][2]);m=tuple(v/16384 if j<9 else float(v) for j,v in enumerate(raw));rect=struct.unpack('<4i',row['blocks'][9])
   actual=c.combined_decisions(m,i,rect)
   if c.endpoint_valid[i]:
    assert actual==Base(row,row,d,table).combined_decisions(m,0,rect)
    count=len(c.vertices);points=C.create_string_buffer(count*4);blocks=row['blocks'];scale=struct.unpack_from('<I',blocks[0],64)[0];center=struct.unpack_from('<2h',blocks[3],8)
    assert d.nfs_model_project(bytes(blocks[2]),bytes(blocks[4]),count,scale,*center,c.native_table,points)==1
    d.nfs_model_face_visible.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
    d.nfs_model_polygon_classify.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
    native_faces=[];native_rect=[]
    for ids in c.faces:
     indices=(C.c_uint16*len(ids))(*ids);visible=C.c_int();code=C.c_int()
     assert d.nfs_model_face_visible(points,count,indices,len(ids),C.byref(visible))==1
     assert d.nfs_model_polygon_classify(points,count,indices,len(ids),(C.c_int32*4)(*rect),C.byref(code))==1
     native_faces.append(bool(visible.value));native_rect.append(code.value)
    assert actual==(tuple(native_faces),tuple(native_rect)),'Candidate differs from recovered integer visibility'
    endpoint_checks.append(dict(native_oracle_faces=len(native_faces),native_selected_faces=sum(v and code!=4 for v,code in zip(native_faces,native_rect)),captured_clip_rectangle=list(rect)))
   else:assert not any(actual[0]) and all(x==4 for x in actual[1])
   endpoint_checks.append(dict(endpoint=i,valid=c.endpoint_valid[i],faces=len(c.faces)))
 return c
batch.SourceFaceDeterminants=build
from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')","folder=Path('work/camera/prototype-runs/fullscene-failure-1791505088433840800')");ns={};cached=None
try:
 exec(compile(source,'capture_setup','exec'),ns);cached=PrecomputedSourceWorldSamples(ns['prepared'],(.2,.4,.6,.8),trace=True)
 checks=[dict(alpha=a,selected_faces=cached.source_masks[a][3]['selected_faces']) for a in cached.samples]
 assert len(checks)==4
finally:
 if cached:cached.close()
 for name in ('prepared','history'):
  if ns.get(name):ns[name].close()
out=dict(result='PASS_DEPTH_ENDPOINT_NATIVE_VISIBILITY',checks=checks,endpoint_checks=endpoint_checks,scope='Four source preparation samples on failed captured pair; 57 valid endpoint face and rectangle decisions equal recovered native integer routines; invalid endpoint whole-model rejection. Not a direct emulator raster or fractional visibility proof.')
Path('work/camera/prototype-runs/native-depth-endpoint-oracle-20261008.json').write_text(json.dumps(out,indent=2));print(out)
