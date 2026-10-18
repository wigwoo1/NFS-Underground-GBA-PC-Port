from pathlib import Path
import os,ctypes as C,json,hashlib,threading
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-alias-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'live-recipe-build-report.json').read_text());dll=out/'recipe-store-alias.dll';assert sha(dll)==receipt['strict_store_dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(dll))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(n,args,result=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
op=fn('nf_recipe_store_open',[Q,S],P);close=fn('nf_recipe_store_close',[P],None);put=fn('nf_recipe_store_put',[P,Q,U,Q,P,U]);alias=fn('nf_pc_recipe_store_alias',[P,Q,U,Q,Q]);info=fn('nf_recipe_store_info',[P,P]);prune=fn('nf_recipe_store_prune',[P,Q,P,S]);reset=fn('nf_recipe_store_reset',[P,Q]);snap=fn('nf_recipe_store_snapshot',[P,Q,P,S],P);free=fn('nf_recipe_snapshot_free',[P],None);block=fn('nf_recipe_snapshot_block',[P,S,U,P,P]);minimum=fn('nf_recipe_store_minimum',[],S)()
def stats(p):a=(Q*5)();assert info(p,a);return tuple(a)
def insert(p,ordinal,data):a=C.create_string_buffer(data);b=Block(C.cast(a,P),len(data));return put(p,1,1,ordinal,C.byref(b),1)
def snapshot_bytes(p,i):a=P();n=S();assert block(p,i,0,C.byref(a),C.byref(n));return a.value,C.string_at(a,n.value)
p=op(1,minimum+100000);assert insert(p,1,b'owned source');before=stats(p);base_charge=before[3]-minimum;assert alias(p,1,1,2,1);after=stats(p);alias_charge=after[3]-before[3];assert after[1:3]==(2,1) and alias_charge>0
assert alias(p,1,1,2,1) and stats(p)==after;assert insert(p,3,b'different');before=stats(p)
assert not alias(p,1,1,3,1) and not alias(p,2,1,4,1) and not alias(p,1,0,4,1) and not alias(p,1,1,4,999) and stats(p)==before
result=[]
def wrong_thread():result.append(alias(p,1,1,4,1))
t=threading.Thread(target=wrong_thread);t.start();t.join();assert result==[0] and stats(p)==before
k=(Q*4)(1,1,1,2);view=snap(p,1,k,2);assert view;pa,a=snapshot_bytes(view,0);pb,b=snapshot_bytes(view,1);assert pa==pb and a==b==b'owned source'
assert prune(p,1,(Q*2)(1,2),1) and stats(p)[1:3]==(1,1);assert snapshot_bytes(view,0)[1]==b'owned source';assert reset(p,2);close(p);assert snapshot_bytes(view,1)[1]==b'owned source';free(view)
for delta,success in [(-1,False),(0,True)]:
 p=op(1,minimum+base_charge+alias_charge+delta);assert insert(p,1,b'owned source');before=stats(p);assert bool(alias(p,1,1,2,1))==success
 if not success:assert stats(p)==before
 close(p)
r=dict(result='PASS_IMMUTABLE_ROAD_WRITER_ALIAS_GUARDS',same_blob_pointer=True,idempotent_binding=True,conflicting_missing_invalid_and_stale_rejected=True,wrong_thread_rejected=True,alias_survives_source_writer_prune_reset_and_store_close=True,exact_budget_boundary_and_failure_atomic=True,alias_metadata_charge=alias_charge,dll_sha256=sha(dll),build_report_sha256=sha(out/'live-recipe-build-report.json'),script_sha256=sha(Path(__file__)))
(out/'alias-unit-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
