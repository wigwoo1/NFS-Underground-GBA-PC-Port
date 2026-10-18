from pathlib import Path
import os,ctypes as C,json,hashlib,struct,time
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-owner-motion-tests';fixtures=base/'NFSUG-pc-world-tests/references';receipt=json.loads((out/'motion-build-report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert receipt['dll_sha256']==sha(out/'world-owner-motion.dll')
for name,digest in receipt['source_sha256'].items():assert sha(Path(name))==digest
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'world-owner-motion.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class Key(C.Structure):_fields_=[('epoch',Q),('refresh',U),('identity',U*5)]
def fn(n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
prepare=fn('nf_pc_world_motion_owner_prepare',[P,S,P,P,S,P,C.c_double,S],P);destroy=fn('nf_pc_world_motion_owner_free',[P],None);info=fn('nf_pc_world_motion_owner_info',[P,P]);match=fn('nf_pc_world_motion_owner_match',[P,U,P]);mesh=fn('nf_pc_world_motion_owner_mesh',[P,U,S],P);material=fn('nf_pc_world_motion_owner_material',[P,U,P,P]);reference=fn('nf_pc_world_motion_mesh',[P,S,U,P,P,S,U,P,C.c_double,S],P);mesh_info=fn('nf_pc_world_mesh_info',[P,P]);mesh_buffer=fn('nf_pc_world_mesh_buffer',[P,U,P,P]);mesh_free=fn('nf_pc_world_mesh_free',[P],None);world_surface=fn('nf_pc_world_surface_buffer',[P,U,U,P,P])
decode=fn('nf_pc_world_decode',[P,S,S],P);world_free=fn('nf_pc_world_free',[P],None)
def word(p,at):return struct.unpack_from('<I',p,at)[0]
def owner(p):return (Q*5)(0x12345678,*struct.unpack_from('<4I',p,16))
def identities(p):
 section=word(p,84);count=word(p,48);surfaces=word(p,count+4);return [struct.unpack_from('<5I',p,section+8+i*20) for i in range(surfaces)]
def blob(m,k):
 p=P();n=S();assert mesh_buffer(m,k,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def state(m):
 i=(Q*16)();assert mesh_info(m,i);return list(i),blob(m,0),blob(m,1)
def surface_blob(w,i,k):
 p=P();n=S();assert world_surface(w,i,k,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
manifest=json.loads((base/'NFSUG-pc-world-tests/world-build-report.json').read_text());groups={};inputs={}
for path in fixtures.glob('*.nsp'):
 assert sha(path)==manifest['reference_sha256'][path.name];inputs[str(path)]=sha(path);groups.setdefault(path.stem.split('-')[0],[]).append(path)
pairs=[]
for paths in groups.values():
 if len(paths)==2:
  a,b=sorted([(p,p.read_bytes()) for p in paths],key=lambda item:word(item[1],16))
  if word(a[1],16)<word(b[1],16) and 0<word(b[1],24)-word(a[1],24)<=8:pairs.append((a[0].name,a[1],b[0].name,b[1]))
repro=base/'NFSUG-pc-world-mesh-motion-tests'
for name in ['rejected-a.nsp','rejected-b.nsp']:inputs[str(repro/name)]=sha(repro/name)
pairs.append(('replay-a',(repro/'rejected-a.nsp').read_bytes(),'replay-b',(repro/'rejected-b.nsp').read_bytes()))
tested=meshes=prepared_decodes=old_only=new_only=ambiguous=changed=unsupported=0;maximum_retained=0;reference_ms=owner_ms=0.;held=None;last_valid=None;material_bytes=0
for name,a,other,b in pairs:
 ak,bk=owner(a),owner(b);aid,bid=identities(a),identities(b);wa,wb=decode(a,len(a),64*1024*1024),decode(b,len(b),64*1024*1024);assert wa and wb
 for alpha in [0.,.25,.5,.75,1.]:
  began=time.perf_counter();o=prepare(a,len(a),ak,b,len(b),bk,alpha,64*1024*1024);assert o,(name,other,alpha);owner_ms+=(time.perf_counter()-began)*1000;oi=(Q*14)();assert info(o,oi);assert oi[3]==len(aid) and oi[4]==len(bid) and oi[6]==(2 if alpha in [0.,1.] else 3) and oi[5]<=64*1024*1024;prepared_decodes+=oi[6];maximum_retained=max(maximum_retained,oi[5]);old_only+=oi[8];new_only+=oi[9];ambiguous+=oi[10];changed+=oi[11];unsupported+=oi[12];requests=0
  for i,key in enumerate(aid):
   mapping=(Q*3)();assert match(o,i,mapping);candidates=[j for j,value in enumerate(bid) if value==key]
   if aid.count(key)>1 or len(candidates)>1:assert mapping[0]==3
   elif not candidates:assert mapping[0]==2
   if mapping[0]!=1:assert not mesh(o,i,32*1024*1024);continue
   j=mapping[1];assert candidates==[j] and mapping[2]==key[0];ka,kb=Key(ak[0],ak[3],(U*5)(*key)),Key(bk[0],bk[3],(U*5)(*key));began=time.perf_counter();ref=reference(a,len(a),i,C.byref(ka),b,len(b),j,C.byref(kb),alpha,32*1024*1024);reference_ms+=(time.perf_counter()-began)*1000;assert ref
   began=time.perf_counter();m=mesh(o,i,32*1024*1024);owner_ms+=(time.perf_counter()-began)*1000;assert m and state(m)==state(ref);mesh_free(ref);requests+=1;meshes+=1
   w=P();surface=U();assert material(o,i,C.byref(w),C.byref(surface));assert surface.value==(j if alpha==1 else i)
   p=P();n=S();assert world_surface(w,surface.value,9,C.byref(p),C.byref(n)) and C.string_at(p,n.value)==struct.pack('<5I',*key)
   for kind in range(10):
    actual=surface_blob(w,surface.value,kind);expected=surface_blob(wb if alpha==1 else wa,j if alpha==1 else i,kind);assert actual==expected;material_bytes+=len(actual)
   if held is None:held=(o,m,state(m));o_held=o
   else:mesh_free(m)
  after=(Q*14)();assert info(o,after) and after[6]==oi[6] and after[13]==requests
  last_valid=(a,b,ak,bk)
  if held is None or o!=held[0]:destroy(o)
  tested+=1
 world_free(wa);world_free(wb)
assert tested>=5 and meshes>20 and held
a,b,ak,bk=last_valid;bad_requests=0
for alpha in [-1.,2.,float('nan')]:assert not prepare(a,len(a),ak,b,len(b),bk,alpha,64*1024*1024);bad_requests+=1
for index in range(5):
 bad=(Q*5)(*bk);bad[index]+=1;assert not prepare(a,len(a),ak,b,len(b),bad,.5,64*1024*1024);bad_requests+=1
assert not prepare(a,len(a),ak,b,len(b),bk,.5,1);bad_requests+=1
o=prepare(a,len(a),ak,b,len(b),bk,.5,64*1024*1024);assert o;oi=(Q*14)();assert info(o,oi);destroy(o);o=prepare(a,len(a),ak,b,len(b),bk,.5,oi[5]);assert o;destroy(o);assert not prepare(a,len(a),ak,b,len(b),bk,.5,oi[5]-1);bad_requests+=1
# Duplicate an identity within the newer source packet: no ordinal guessing.
ids=identities(b);duplicate=None
for j,value in enumerate(ids):
 for k,other in enumerate(ids):
  if j!=k and value[0]==other[0] and value!=other:duplicate=(j,k);break
 if duplicate:break
assert duplicate;j,k=duplicate;mutated=bytearray(b);at=word(b,84)+8;mutated[at+k*20:at+(k+1)*20]=struct.pack('<5I',*ids[j]);mutated=bytes(mutated);o=prepare(a,len(a),ak,mutated,len(mutated),bk,.5,64*1024*1024);assert o;oi=(Q*14)();assert info(o,oi) and oi[10]>0
for i in range(oi[3]):
 mapping=(Q*3)();assert match(o,i,mapping)
 if mapping[0]==3:assert not mesh(o,i,32*1024*1024)
destroy(o)
del a,b,pairs,groups;assert state(held[1])==held[2];destroy(held[0]);assert state(held[1])==held[2];mesh_free(held[1])
assert inputs=={name:sha(Path(name)) for name in inputs}
report=dict(result='PASS_PREPARED_WORLD_OWNER_MOTION_COMPONENT',owner_phase_contexts=tested,meshes_exact_to_per_surface_reference=meshes,world_decode_count=prepared_decodes,no_world_decode_during_mesh_requests=True,maximum_retained_bytes=maximum_retained,old_only_rows=old_only,new_only_rows=new_only,ambiguous_rows=ambiguous,changed_rows=changed,unsupported_rows=unsupported,synthetic_duplicate_identity_rejected=True,negative_prepare_requests=bad_requests,exact_budget_boundary_verified=True,held_mesh_outlives_owner=True,material_source_index_verified=True,all_selected_surface_buffers_exact_bytes=material_bytes,diagnostic_reference_ms=reference_ms,diagnostic_prepare_plus_mesh_ms=owner_ms,timing_limit='Single offline corpus; different allocation lifetimes, not live frame pacing or a universal speedup.',input_sha256=inputs,dll_sha256=sha(out/'world-owner-motion.dll'),build_report_sha256=sha(out/'motion-build-report.json'),test_source_sha256=sha(Path(__file__)),live_integration=False,full_scene_60fps=False)
(out/'owner-motion-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='input_sha256'},indent=2))
