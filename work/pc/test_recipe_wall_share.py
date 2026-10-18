from pathlib import Path
import os,ctypes as C,json,hashlib,threading
base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-wall-share-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((out/'live-recipe-build-report.json').read_text());dll=out/'recipe-store-wall-share.dll';assert sha(dll)==r['strict_store_dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(dll))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(n,args,result=C.c_int):f=getattr(d,n);f.argtypes=args;f.restype=result;return f
op=fn('nf_recipe_store_open',[Q,S],P);close=fn('nf_recipe_store_close',[P],None);put=fn('nf_recipe_store_put',[P,Q,U,Q,P,U]);patch=fn('nf_pc_recipe_store_wall_column',[P,Q,Q,P,P]);prune=fn('nf_recipe_store_prune',[P,Q,P,S]);reset=fn('nf_recipe_store_reset',[P,Q]);snap=fn('nf_recipe_store_snapshot',[P,Q,P,S],P);free=fn('nf_recipe_snapshot_free',[P],None);info=fn('nf_recipe_store_info',[P,P]);block=fn('nf_recipe_snapshot_block',[P,S,U,P,P]);minimum=fn('nf_recipe_store_minimum',[],S)()
values=[('owned block '+str(i)).encode() for i in range(15)]
def args(values):buffers=[C.create_string_buffer(v) for v in values];return buffers,(Block*len(values))(*[Block(C.cast(v,P),len(values[i])) for i,v in enumerate(buffers)])
def stats(pool):a=(Q*5)();assert info(pool,a);return tuple(a)
def source(pool):buffers,a=args(values);assert put(pool,1,2,1,a,15);view=snap(pool,1,(Q*2)(2,1),1);assert view;return view

def changed(pool,epoch,ordinal,template,values):buffers,a=args(values);return patch(pool,epoch,ordinal,template,a)
def contents(view):
 result=[]
 for i in range(15):p=P();n=S();assert block(view,0,i,C.byref(p),C.byref(n));result.append((p.value,C.string_at(p,n.value)))
 return result
p=op(1,minimum+100000);template=source(p);before=stats(p)
assert not changed(p,1,2,template,[b'new column',b'z'*1000000]) and stats(p)==before
assert not changed(p,2,2,template,[b'a',b'b']) and not changed(p,1,0,template,[b'a',b'b']) and stats(p)==before
result=[]
def wrong_thread():result.append(changed(p,1,2,template,[b'a',b'b']))
t=threading.Thread(target=wrong_thread);t.start();t.join();assert result==[0] and stats(p)==before
other=op(1,minimum+100000);assert not changed(other,1,2,template,[b'a',b'b']);close(other)
assert prune(p,1,None,0) and stats(p)[1:3]==(0,0);before=stats(p)
# Replacement overlaps an orphaned common block: reattach its allocation once.
replacement=[values[0],b'new shade'];assert changed(p,1,2,template,replacement);after=stats(p);charge=after[3]-before[3];assert after[1:3]==(1,14)
view=snap(p,1,(Q*2)(2,2),1);assert view;original=contents(template);updated=contents(view)
for i in list(range(12))+[14]:assert original[i]==updated[i]
assert updated[12]==original[0] and updated[13][1]==replacement[1] and contents(template)==original
before=stats(p);assert not changed(p,1,2,template,replacement) and stats(p)==before
assert reset(p,2) and not changed(p,2,3,template,replacement);close(p);assert contents(template)==original and contents(view)==updated;free(template)
result=[]
def read_worker():assert contents(view)==updated;free(view);result.append(True)
t=threading.Thread(target=read_worker);t.start();t.join();assert result==[True]
# Exact allocation boundary includes already published template ownership.
for delta,success in [(-1,False),(0,True)]:
 pool=op(1,before[3]+charge+100000) # measure fixture's retained base charge first
 prototype=source(pool);assert prune(pool,1,None,0);base_charge=stats(pool)[3];free(prototype);close(pool)
 pool=op(1,base_charge+charge+delta);prototype=source(pool);assert prune(pool,1,None,0);before=stats(pool);assert bool(changed(pool,1,2,prototype,replacement))==success
 if not success:assert stats(pool)==before
 free(prototype);close(pool)
report=dict(result='PASS_OWNED_WALL_TEMPLATE_COLUMN_SHARING',common_blocks_same_pointer=True,per_column_replacements_exact=True,source_writer_eviction_and_root_reattachment=True,replacement_common_block_overlap_deduplicated=True,failed_staged_allocation_atomic=True,exact_budget_boundary=True,duplicate_invalid_stale_cross_store_and_wrong_thread_rejected=True,snapshots_survive_reset_close_and_worker_read_free=True,dll_sha256=sha(dll),build_report_sha256=sha(out/'live-recipe-build-report.json'),script_sha256=sha(Path(__file__)))
(out/'wall-share-unit-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
