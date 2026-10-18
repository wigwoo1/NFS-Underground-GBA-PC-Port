from pathlib import Path
import ctypes as C,threading,hashlib,json
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-shared-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
original=here/'test_writer_gpu_synthetic.py';boot=original.read_text().split('try:\n for name,kind,command,texture,shade in cases:')[0].replace('NFSUG-pc-writer-gpu-tests','NFSUG-pc-writer-shared-tests');ns={'__file__':str(original),'__name__':'shared_writer_guard_inputs'};exec(compile(boot,str(original),'exec'),ns)
P,S,Q,U=[ns[k] for k in ['P','S','Q','U']];fn=ns['fn'];ref=ns['ref'];owner=ref['owner'];ordinal=ref['ordinal'];open_pool=fn('nf_recipe_store_open',[Q,S],P);close_pool=fn('nf_recipe_store_close',[P],None);info_pool=fn('nf_recipe_store_info',[P,P]);minimum=fn('nf_recipe_store_minimum',[],S)();decode=fn('nf_pc_recipe_writer_decode_shared',[P,P,U,Q,U,P,U],P);shared_info=fn('nf_pc_recipe_writer_shared_info',[P,P]);wi=fn('nf_pc_recipe_writer_info',[P,P]);buffer=fn('nf_pc_recipe_writer_buffer',[P,U,P,P]);sample=fn('nf_pc_recipe_writer_cell',[P,U,U,P]);plain=ns['op'];free=ns['wf'];pool=None;writers=[];guards=0
name,kind,command,texture,shade=ns['cases'][2];keep,blocks=ref['fixture'](kind,command,texture,shade)
def stats(pool):v=(Q*5)();assert info_pool(pool,v);return list(v)
def data(w,k):p=P();n=S();assert buffer(w,k,C.byref(p),C.byref(n));return p.value,C.string_at(p,n.value)
try:
 tiny=open_pool(owner[0],minimum+1);assert tiny;before=stats(tiny);assert not decode(tiny,owner,kind,ordinal,8,blocks,15) and stats(tiny)==before;close_pool(tiny);guards+=1
 pool=open_pool(owner[0],64*1024*1024);assert pool
 for i in range(3):w=decode(pool,owner,kind,ordinal+i,8,blocks,15);assert w;writers.append(w)
 assert data(writers[0],1)[0]==data(writers[1],1)[0]==data(writers[2],1)[0]
 assert data(writers[0],2)[0]==data(writers[1],2)[0] and data(writers[0],3)[0]==data(writers[2],3)[0]
 states=stats(pool);results=[]
 def wrong_thread():results.append(decode(pool,owner,kind,ordinal+10,8,blocks,15))
 t=threading.Thread(target=wrong_thread);t.start();t.join();assert results==[None] and stats(pool)==states;guards+=1
 # A different original command under the SAME key must reject, even when its
 # raw texture/shade/palette bytes are identical and local decode is valid.
 badcommand=list(command);badcommand[0]^=1;badkeep,badblocks=ref['fixture'](kind,badcommand,texture,shade);valid=plain(owner,kind,ordinal,8,badblocks,15,64*1024*1024);assert valid;free(valid);assert not decode(pool,owner,kind,ordinal,8,badblocks,15) and stats(pool)==states;guards+=1
 # Content identity, not a texture's source address, determines blob sharing.
 altered=bytearray(texture);altered[-1]^=1;otherkeep,otherblocks=ref['fixture'](kind,command,bytes(altered),shade);other=decode(pool,owner,kind,ordinal+20,8,otherblocks,15);assert other and data(other,1)[0]!=data(writers[0],1)[0];free(other)
 # A one-writer ledger boundary must accept exactly and reject one byte less.
 measure=open_pool(owner[0],64*1024*1024);mw=decode(measure,owner,kind,ordinal,8,blocks,15);assert mw;exact=stats(measure)[3];free(mw);close_pool(measure)
 exact_pool=open_pool(owner[0],exact);ew=decode(exact_pool,owner,kind,ordinal,8,blocks,15);assert ew and stats(exact_pool)[3]==exact;free(ew);close_pool(exact_pool)
 small_pool=open_pool(owner[0],exact-1);assert small_pool and not decode(small_pool,owner,kind,ordinal,8,blocks,15);assert stats(small_pool)[3]<=exact-1;close_pool(small_pool);guards+=1
 old=ref['op'](owner,kind,ordinal,8,blocks,15,64*1024*1024);assert old;expected=[]
 for y in range(160):
  for x in [119,120,121,122]:value=(Q*4)();assert ref['sample'](old,x,y,value);expected.append((x,y,list(value)))
 ref['free'](old)
 wanted={k:data(writers[0],k)[1] for k in range(5)}
 for b in keep:C.memset(b,0,len(b))
 close_pool(pool);pool=None
 for w in writers:
  for k,v in wanted.items():assert data(w,k)[1]==v
  for x,y,want in expected:v=(Q*4)();assert sample(w,x,y,v) and list(v)==want
 first=writers.pop(0);allocation=(Q*10)();assert wi(first,allocation);before=(Q*5)();assert shared_info(writers[0],before)
 def free_worker():
  for k,v in wanted.items():assert data(first,k)[1]==v
  free(first)
 t=threading.Thread(target=free_worker);t.start();t.join();after=(Q*5)();assert shared_info(writers[0],after);assert before[3]-after[3]==allocation[9],(list(before),list(after),list(allocation))
 print('SHARED_WRITER_POOL_BUDGET_AND_LIFETIME_PASS',flush=True)
finally:
 for w in writers:free(w)
 if pool:close_pool(pool)
 ns['close'](ns['g'])
r=dict(result='PASS_SHARED_WRITER_CANONICAL_IDENTITY_BUDGET_THREAD_AND_LIFETIME',negative_cases=guards,shared_texture_shade_palette_addresses=True,changed_texture_same_source_address_not_aliased=True,same_key_changed_original_command_rejected=True,exact_pool_budget_bytes=exact,one_byte_less_rejected=True,input_overwrite_and_store_close_survived=True,point_checks=3*len(expected),all_five_owned_buffers_exact=True,worker_read_free_ledger_decrement_exact=True,released_writer_ledger_bytes=int(allocation[9]),script_sha256=sha(Path(__file__)),input_sha256=sha(original),executed_prefix_sha256=hashlib.sha256(boot.encode()).hexdigest(),gpu_dll_sha256=sha(out/'recipe-gpu.dll'),full_scene_60fps=False)
(out/'writer-shared-guard-report.json').write_text(json.dumps(r,indent=2));print(r)
