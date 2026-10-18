"""Owned prepared-list snapshot evaluation, lifetime and missing-query guards."""
import ctypes as C,json,struct
from pathlib import Path
p=Path(__file__).resolve().parent;out=p/'prototype-runs/paired-lifecycle';report=json.loads((out/'report.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();d=C.CDLL(str(p/'visibility-probe-wide.dll'));P=C.c_void_p
for name in ['nf_visibility_assets_create','nf_visibility_snapshot_create_prepared','nf_visibility_snapshot_clone']:getattr(d,name).restype=P
for name in ['nf_visibility_assets_release','nf_visibility_snapshot_destroy']:getattr(d,name).argtypes=[P]
d.nf_visibility_assets_create.argtypes=[P,C.c_size_t];d.nf_visibility_snapshot_create_prepared.argtypes=[P,P,C.c_size_t,C.c_uint32,C.c_uint32];d.nf_visibility_snapshot_clone.argtypes=[P];d.nf_visibility_snapshot_bind.argtypes=[P,P];d.nf_visibility_snapshot_evaluate_for.argtypes=[P,C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,P];d.nf_visibility_snapshot_pose.argtypes=[P,C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,P];d.nf_visibility_snapshot_prepared_view.argtypes=[P,P]
d.nf_visibility_snapshot_evaluate_prepared_view.argtypes=[P,C.c_uint64,C.c_uint32,C.c_uint32,C.c_uint32,P,P]
d.nf_visibility_view_sample.argtypes=[P,P,C.c_double,P]
class Identity(C.Structure):_fields_=[('epoch',C.c_uint64),('serial',C.c_uint32),('begin',C.c_uint32),('end',C.c_uint32),('query',C.c_uint32),('builder',C.c_uint32)]
identity=(C.c_int32*12)(16384,0,0,0,16384,0,0,0,16384,0,0,0)
quarter=(C.c_int32*12)(0,0,-16384,0,16384,0,16384,0,0,128,0,0)
midrotation=(C.c_int32*12)();assert d.nf_visibility_view_sample(identity,quarter,0.5,midrotation)
assert list(midrotation)==[11585,0,-11585,0,16384,0,11585,0,11585,64,0,0]
results=[]
for c in report['checks']:
 name=Path(c['state']).stem;before=(out/(name+'-builder-source.bin')).read_bytes();after=(out/(name+'-builder-end-source.bin')).read_bytes();state=c['diagnostics']['builder_registers'][0];off=0x40000+state-0x03000000;qa,ga=struct.unpack_from('<2I',before,off+96);selected=struct.unpack_from('<H',before,0x40000+0x5d44)[0]
 def get(ram,a,n):return ram[a-0x02000000:a-0x02000000+n] if a<0x03000000 else ram[0x40000+a-0x03000000:0x40000+a-0x03000000+n]
 asset=d.nf_visibility_assets_create(rom,len(rom));buf=C.create_string_buffer(before,len(before));s=d.nf_visibility_snapshot_create_prepared(asset,buf,len(before),state,selected);assert s;ident=Identity(7,1,2,5,3,4);assert d.nf_visibility_snapshot_bind(s,C.byref(ident));copy=d.nf_visibility_snapshot_clone(s);assert copy;d.nf_visibility_snapshot_destroy(s);d.nf_visibility_assets_release(asset);C.memset(buf,0,len(before))
 try:
  result=C.create_string_buffer(4868);assert d.nf_visibility_snapshot_evaluate_for(copy,7,1,2,5,result);expected=get(after,state,256)+get(after,qa,512)+get(after,ga,4096)+struct.pack('<I',selected);assert result.raw==expected
  view=C.create_string_buffer(48);assert d.nf_visibility_snapshot_prepared_view(copy,view);va=struct.unpack_from('<I',before,off+84)[0];assert view.raw==get(before,va,48)
  sampled=C.create_string_buffer(4868);assert d.nf_visibility_snapshot_evaluate_prepared_view(copy,7,1,2,5,view,sampled) and sampled.raw==expected
  # Compare overlay against a distinct owned RAM capture containing that view.
  shifted=bytearray(view.raw);translation=struct.unpack_from('<I',shifted,36)[0];struct.pack_into('<I',shifted,36,(translation+128)&0xffffffff)
  altered=bytearray(before);voff=va-0x02000000 if va<0x03000000 else 0x40000+va-0x03000000;altered[voff:voff+48]=shifted
  altasset=d.nf_visibility_assets_create(rom,len(rom));altbuf=C.create_string_buffer(bytes(altered),len(altered));alternate=d.nf_visibility_snapshot_create_prepared(altasset,altbuf,len(altered),state,selected);assert alternate
  try:
   assert d.nf_visibility_snapshot_bind(alternate,C.byref(ident));oracle=C.create_string_buffer(4868);assert d.nf_visibility_snapshot_evaluate_for(alternate,7,1,2,5,oracle)
   shiftbuf=C.create_string_buffer(bytes(shifted),48);mid=C.create_string_buffer(48)
   assert d.nf_visibility_view_sample(view,shiftbuf,0,mid) and mid.raw==view.raw
   assert d.nf_visibility_view_sample(view,shiftbuf,1,mid) and mid.raw==shiftbuf.raw
   assert d.nf_visibility_view_sample(view,shiftbuf,0.5,mid)
   expected_mid=bytearray(view.raw);struct.pack_into('<I',expected_mid,36,(translation+64)&0xffffffff);assert mid.raw==bytes(expected_mid)
   invalid=C.create_string_buffer(bytes([165])*48,48)
   for fraction in [-1,2,float('nan')]:assert not d.nf_visibility_view_sample(view,shiftbuf,fraction,invalid) and invalid.raw==bytes([165])*48
   shiftbuf=C.create_string_buffer(bytes(shifted),48);assert d.nf_visibility_snapshot_evaluate_prepared_view(copy,7,1,2,5,shiftbuf,sampled) and sampled.raw==oracle.raw
   assert d.nf_visibility_snapshot_evaluate_for(copy,7,1,2,5,result) and result.raw==expected
  finally:d.nf_visibility_snapshot_destroy(alternate);d.nf_visibility_assets_release(altasset)
  rejected=C.create_string_buffer(bytes([165])*4868,4868);assert not d.nf_visibility_snapshot_evaluate_prepared_view(copy,8,1,2,5,view,rejected) and rejected.raw==bytes([165])*4868
  postasset=d.nf_visibility_assets_create(rom,len(rom));postbuf=C.create_string_buffer(after,len(after));post=d.nf_visibility_snapshot_create_prepared(postasset,postbuf,len(after),state,selected);assert post
  try:
   assert d.nf_visibility_snapshot_bind(post,C.byref(ident));postresult=C.create_string_buffer(4868);assert d.nf_visibility_snapshot_evaluate_for(post,7,1,2,5,postresult)
   assert postresult.raw==expected, name+' post-builder list is not repeatable'
   assert d.nf_visibility_snapshot_evaluate_prepared_view(post,7,1,2,5,view,postresult) and postresult.raw==expected
  finally:d.nf_visibility_snapshot_destroy(post);d.nf_visibility_assets_release(postasset)
  pose=C.create_string_buffer(bytes([165])*104,104);assert not d.nf_visibility_snapshot_pose(copy,7,1,2,5,pose) and pose.raw==bytes([165])*104
  sentinel=C.create_string_buffer(bytes([165])*4868,4868);assert not d.nf_visibility_snapshot_evaluate_for(copy,8,1,2,5,sentinel) and sentinel.raw==bytes([165])*4868
 finally:d.nf_visibility_snapshot_destroy(copy)
 results.append(dict(state=name,owned_evaluation_exact_original_builder=True,actual_view_exact=True,explicit_view_endpoint_original_exact=True,translated_view_matches_distinct_owned_capture=True,retained_source_unchanged=True,post_builder_rebuild_exact=True,view_sampling_endpoints_midpoint_and_guards=True,query_pose_atomic_rejection=True,stale_epoch_atomic_rejection=True));print(name,'PASS')
(out/'prepared-snapshot-test.json').write_text(json.dumps(dict(result='PASS',checks=results,scope='Immutable prepared-list snapshot ownership/native builder evaluation only; query interpolation/live scene renderer integration pending.'),indent=2))
