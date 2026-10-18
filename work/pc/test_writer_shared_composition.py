from pathlib import Path
import os,ctypes as C,json,hashlib
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-shared-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
with os.add_dll_directory('C:/msys64/mingw64/bin'):lib=C.CDLL(str(out/'recipe-gpu.dll'))
def bind(n,args,res=C.c_int):f=getattr(lib,n);f.argtypes=args;f.restype=res;return f
pool_open=bind('nf_recipe_store_open',[Q,S],P);pool_close=bind('nf_recipe_store_close',[P],None);pool_info=bind('nf_recipe_store_info',[P,P]);pool=pool_open(2,64*1024*1024);assert pool
original=here/'test_writer_composition_gpu.py';text=original.read_text().replace('NFSUG-pc-writer-composition-tests','NFSUG-pc-writer-shared-tests')
anchor="op=bind(d,'nf_pc_recipe_writer_decode',[P,U,Q,U,P,U,S],P);";assert text.count(anchor)==1
text=text.replace(anchor,"shared_decode=bind(d,'nf_pc_recipe_writer_decode_shared',[P,P,U,Q,U,P,U],P);op=lambda key,kind,ordinal,write,blocks,count,maximum: shared_decode(pool,key,kind,ordinal,write,blocks,count);")
anchor=' assert len(prepared)==3';assert text.count(anchor)==1
text=text.replace(anchor,anchor+"\n thin_allocation_bytes=0\n for handle,_ in handles:\n  allocation=(Q*10)();assert bind(cap['d'],'nf_pc_recipe_writer_info',[P,P])(handle,allocation);thin_allocation_bytes+=allocation[9]\n pool_state=(Q*5)();assert pool_info(pool,pool_state);pool_close(pool);pool=None;print('SHARED_STORE_CLOSED_BEFORE_GPU',list(pool_state),flush=True)")
# Existing test verifies all original cell values and complete images after pool close.
ns={'__file__':str(original),'__name__':'shared_writer_composition','pool':pool,'pool_info':pool_info,'pool_close':pool_close}
try:exec(compile(text,str(original),'exec'),ns)
finally:
 if ns.get('pool'):pool_close(ns['pool'])
old=json.loads((base/'NFSUG-pc-writer-composition-tests/writer-composition-test-report.json').read_text());new=json.loads((out/'writer-composition-test-report.json').read_text());state=list(ns['pool_state']);assert state[3]<state[4] and state[3]<old['writer_and_address_retained_bytes']//4
for name,h in old['diagnostic_images'].items():assert new['diagnostic_images'][name]==h,name
r=dict(result='PASS_SHARED_WRITER_COMPLETE_SCENES_AND_STORE_LIFETIME',pool_state_before_close=state,old_copied_writer_and_address_bytes=old['writer_and_address_retained_bytes'],new_thin_writer_and_address_bytes=new['writer_and_address_retained_bytes'],pool_ledger_bytes=state[3],thin_writer_allocations=ns['thin_allocation_bytes'],address_map_bytes=new['writer_and_address_retained_bytes']-ns['thin_allocation_bytes'],combined_pool_and_address_bytes=state[3]+new['writer_and_address_retained_bytes']-ns['thin_allocation_bytes'],pool_closed_before_all_gpu_draws=True,all_complete_scene_images_unchanged=True,script_sha256=sha(Path(__file__)),original_test_sha256=sha(original),executed_test_sha256=hashlib.sha256(text.encode()).hexdigest(),gpu_dll_sha256=sha(out/'recipe-gpu.dll'),scope='Existing store ledger includes deduplicated complete canonical15-block assets (including raw texture/shade/palette), writer table, snapshots and thin writer bodies; address maps remain separate. Not RSS/GPU/temporary allocation or live batching.',full_scene_60fps=False)
(out/'writer-shared-composition-report.json').write_text(json.dumps(r,indent=2));print(r)
