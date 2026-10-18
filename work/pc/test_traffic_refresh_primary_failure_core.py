"""Verify first-failed-model diagnostic ABI preserves complete source bytes."""
from pathlib import Path
import hashlib,json,subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace");out=base/'NFSUG-pc-traffic-refresh-primary-failure-core'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'traffic-refresh-primary-failure-build-report.json').read_text());assert build['core_sha256']==sha(out/'capture-host.dll')
for n,h in build['maintained_source_sha256'].items():assert sha(here/n)==h,n
reader=base/'NFSUG-pc-source-reader-direct-tests';rr=json.loads((reader/'reader-direct-test-report.json').read_text());assert rr['dll_sha256']==sha(reader/'source-reader.dll')
for n,h in rr['source_sha256'].items():assert sha(here/n)==h,n
s=(here/'test_owned_assembly_core.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('source=Path(__file__).resolve().parent;root=source.parent.parent;',f'source=Path({str(here)!r});root=source.parent.parent;')
replace("str(base/'NFSUG-pc-reader-tests/source-reader.dll')","str(base/'NFSUG-pc-source-reader-direct-tests/source-reader.dll')")
replace('for dll in [old,new]:',"rop_direct=fn(adapter,'nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P)\nfor dll in [old,new]:")
replace('reader=rop(C.byref(api),64*1024*1024);assert reader;',"reader=rop_direct(C.byref(api),64*1024*1024,C.cast(dll.nfa_core_capture_background_take,P),C.cast(dll.nfa_core_capture_owned_free,P),C.cast(dll.nfa_core_capture_source_world_take,P),C.cast(dll.nfa_core_capture_source_world_free,P));assert reader;")
replace('assert frames==590 and all(',"life=(Q*3)();glife=(Q*3)();assert fn(new,'nfa_core_capture_owned_background_info',[P])(life) and fn(new,'nfa_core_capture_owned_geometry_info',[P])(glife) and life[0]==life[1]>0 and glife[0]==glife[1]>0\nassert frames==590 and all(")
replace('held_frames_outlive_both_cores=True,','held_frames_outlive_both_cores=True,transfers_balanced=True,')
s=s.replace('PASS_OWNED_ASSEMBLY_CORE_PARITY','PASS_REFRESH_PRIMARY_FAILURE_CORE_PARITY')
staged=out/'test-rejection-parity.py';staged.write_text(s)
subprocess.run([sys.executable,str(staged),'--candidate-dir',str(out),'--baseline-core',str(base/'NFSUG-pc-traffic-refresh-core/capture-host.dll')],check=True)
r=json.loads((out/'owned-core-test-report.json').read_text());assert r['result']=='PASS_REFRESH_PRIMARY_FAILURE_CORE_PARITY'
r.update(maintained_test_sha256=sha(Path(__file__)),maintained_source_sha256=build['maintained_source_sha256'],base_test_sha256=sha(here/'test_owned_assembly_core.py'),full_scene_60fps=False)
(out/'traffic-refresh-primary-failure-core-test-report.json').write_text(json.dumps(r,indent=2));print('PASS_REFRESH_PRIMARY_FAILURE_CORE_PARITY')

