"""Compare guarded cache against maintained uncached core, including lifecycle."""
from pathlib import Path
import hashlib,json,subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace')
out=base/'NFSUG-pc-geometry-cache-core';reader=base/'NFSUG-pc-source-reader-direct-tests'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'geometry-cache-build-report.json').read_text())
assert build['core_sha256']==sha(out/'capture-host.dll')
for n,h in build['maintained_source_sha256'].items():assert sha(here/n)==h,n
rr=json.loads((reader/'reader-direct-test-report.json').read_text())
assert rr['result']=='PASS_MAINTAINED_SOURCE_READER_DIRECT' and rr['dll_sha256']==sha(reader/'source-reader.dll')
for n,h in rr['source_sha256'].items():assert sha(here/n)==h,n
s=(here/'test_owned_assembly_core.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a
 s=s.replace(a,b,1)
replace('source=Path(__file__).resolve().parent;root=source.parent.parent;',f'source=Path({str(here)!r});root=source.parent.parent;')
replace("str(base/'NFSUG-pc-reader-tests/source-reader.dll')","str(base/'NFSUG-pc-source-reader-direct-tests/source-reader.dll')")
replace('for dll in [old,new]:',"rop_direct=fn(adapter,'nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P)\ncache_enable=fn(new,'nfa_core_geometry_cache_enable',[P,I]);cache_info=fn(new,'nfa_core_geometry_cache_info',[P])\nfor dll in [old,new]:")
replace('reader=rop(C.byref(api),64*1024*1024);assert reader;',"reader=rop_direct(C.byref(api),64*1024*1024,C.cast(dll.nfa_core_capture_background_take,P),C.cast(dll.nfa_core_capture_owned_free,P),C.cast(dll.nfa_core_capture_source_world_take,P),C.cast(dll.nfa_core_capture_source_world_free,P));assert reader;\n if dll is new:\n  stats=(Q*12)();assert cache_info(stats) and stats[0]==0 and cache_enable(h,1)\n ")
extra='''
  # Compare against direct uncached regeneration under changed mutable evidence.
  item=cores[1];h=item['h'];frame=rcap(item['reader'],64*1024*1024);assert frame
  owner_fn=fn(adapter,'nf_pc_source_frame_owner',[P,U,P]);identity=(Q*5)();assert owner_fn(frame,0,identity)
  raw=fn(new,'nfa_core_capture_source_world',[P,Q,U,U,U,P,S],S)
  take=fn(new,'nfa_core_capture_source_world_take',[P,Q,U,U,U,C.POINTER(P)],S)
  release=fn(new,'nfa_core_capture_source_world_free',[P],None)
  def current_geometry():
   n=raw(h,*identity[:4],None,0);assert n;buf=C.create_string_buffer(n);assert raw(h,*identity[:4],buf,n)==n
   return buf.raw
  def taken_geometry():
   p=P();n=take(h,*identity[:4],C.byref(p));assert p and n
   try:return C.string_at(p,n)
   finally:release(p)
  assert blob(frame,0,1)==current_geometry()==taken_geometry()
  free(frame)
  for enabled in [0,1]:
   cache_before=(Q*12)();cache_after=(Q*12)();assert cache_info(cache_before)
   assert fn(new,'nf_live_model_outcomes_enable',[I])(enabled)
   expected=current_geometry();assert taken_geometry()==expected
   assert cache_info(cache_after) and cache_after[2]>cache_before[2],('mutable outcome change did not miss',enabled)
   # Next identical request should hit and still equal uncached regeneration.
   assert taken_geometry()==expected
  import threading
  thread_results=[]
  def wrong_thread():
   p=P();n=take(h,*identity[:4],C.byref(p));thread_results.append((n,p.value,cache_enable(h,0)))
  thread=threading.Thread(target=wrong_thread);thread.start();thread.join()
  assert thread_results==[(0,None,0)]
  # Stale keys may remain physically stored but cannot be returned after expiry.
  for _ in range(80):
   assert item['f']['step'](h,1)==1
   while item['f']['read_audio'](h,pcm,4096):pass
  p=P();assert take(h,*identity[:4],C.byref(p))==0 and not p
  full_stats=(Q*12)();assert cache_info(full_stats) and full_stats[1]>0 and full_stats[2]>0 and full_stats[6]<=full_stats[8] and full_stats[7]<=full_stats[8] and full_stats[11]<=4
'''
replace('  for item in cores:\n   dll=item[\'dll\'];h=item[\'h\'];assert item[\'f\'][\'load_state\']',extra+"  for item in cores:\n   dll=item['dll'];h=item['h'];assert item['f']['load_state']")
replace("assert fn(dll,'nfa_core_capture_enable',[P,I])(h,0) and not rcap(item['reader'],64*1024*1024)","assert fn(dll,'nfa_core_capture_enable',[P,I])(h,0) and not rcap(item['reader'],64*1024*1024)\n   if dll is new:\n    stats=(Q*12)();assert cache_info(stats) and stats[0]==0 and stats[11]==0 and stats[6]<1024")
replace('assert frames==590 and all(',"life=(Q*3)();geometry_life=(Q*3)();assert fn(new,'nfa_core_capture_owned_background_info',[P])(life) and fn(new,'nfa_core_capture_owned_geometry_info',[P])(geometry_life) and life[0]==life[1]>0 and geometry_life[0]==geometry_life[1]>0\nclosed_stats=(Q*12)();assert cache_info(closed_stats) and closed_stats[0]==0 and closed_stats[11]==0 and closed_stats[6]<1024\nassert frames==590 and all(")
replace('held_frames_outlive_both_cores=True,',"held_frames_outlive_both_cores=True,mutable_outcome_changes_force_misses=True,wrong_thread_cache_requests_rejected=True,expired_geometry_owner_rejected=True,cache_disabled_and_empty_after_close=True,cache_stats_before_reset=list(full_stats),all_transferred_allocations_released_after_core_close=True,background_allocations=int(life[0]),geometry_allocations=int(geometry_life[0]),")
s=s.replace('PASS_OWNED_ASSEMBLY_CORE_PARITY','PASS_GUARDED_GEOMETRY_CACHE_CORE_PARITY')
staged=out/'test-guarded-cache-parity.py';staged.write_text(s)
subprocess.run([sys.executable,str(staged),'--candidate-dir',str(out),'--baseline-core',str(base/'NFSUG-pc-source-transfer-core/capture-host.dll')],check=True)
r=json.loads((out/'owned-core-test-report.json').read_text())
assert r['result']=='PASS_GUARDED_GEOMETRY_CACHE_CORE_PARITY'
r.update(maintained_source_sha256=build['maintained_source_sha256'],maintained_test_sha256=sha(Path(__file__)),base_test_sha256=sha(here/'test_owned_assembly_core.py'),reader_test_receipt_sha256=sha(reader/'reader-direct-test-report.json'),build_receipt_sha256=sha(out/'geometry-cache-build-report.json'),full_scene_60fps=False)
(out/'geometry-cache-core-test-report.json').write_text(json.dumps(r,indent=2));print('PASS_GUARDED_CACHE_INTEGRATION',r['core_sha256'])
