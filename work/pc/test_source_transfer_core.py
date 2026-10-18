"""Real-core parity plus owned/direct frame lifetime checks for maintained sources."""
from pathlib import Path
import json,hashlib,subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-source-transfer-core';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reader=base/'NFSUG-pc-source-reader-direct-tests';rr=json.loads((reader/'reader-direct-test-report.json').read_text());assert rr['result']=='PASS_MAINTAINED_SOURCE_READER_DIRECT' and rr['dll_sha256']==sha(reader/'source-reader.dll')
for n,h in rr['source_sha256'].items():assert sha(here/n)==h,n
s=(here/'test_owned_assembly_core.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('source=Path(__file__).resolve().parent;root=source.parent.parent;',f'source=Path({str(here)!r});root=source.parent.parent;')
replace("str(base/'NFSUG-pc-reader-tests/source-reader.dll')","str(base/'NFSUG-pc-source-reader-direct-tests/source-reader.dll')")
replace('for dll in [old,new]:',"rop_direct=fn(adapter,'nf_pc_source_reader_open_direct_sources',[P,S,P,P,P,P],P)\nfor dll in [old,new]:")
replace('reader=rop(C.byref(api),64*1024*1024);assert reader;',"reader=rop_direct(C.byref(api),64*1024*1024,C.cast(dll.nfa_core_capture_background_take,P),C.cast(dll.nfa_core_capture_owned_free,P),C.cast(dll.nfa_core_capture_source_world_take,P),C.cast(dll.nfa_core_capture_source_world_free,P)) if dll is new else rop(C.byref(api),64*1024*1024);assert reader;")
replace('assert frames==590 and all(',"life=(Q*3)();geometry_life=(Q*3)();assert fn(new,'nfa_core_capture_owned_background_info',[P])(life) and fn(new,'nfa_core_capture_owned_geometry_info',[P])(geometry_life) and life[0]==life[1]>0 and geometry_life[0]==geometry_life[1]>0\nassert frames==590 and all(")
replace('held_frames_outlive_both_cores=True,','held_frames_outlive_both_cores=True,all_transferred_allocations_released_after_core_close=True,background_allocations=int(life[0]),background_releases=int(life[1]),geometry_allocations=int(geometry_life[0]),geometry_releases=int(geometry_life[1]),')
s=s.replace('PASS_OWNED_ASSEMBLY_CORE_PARITY','PASS_SOURCE_TRANSFER_CORE_PARITY')
staged=out/'test-maintained-core-parity.py';staged.write_text(s)
subprocess.run([sys.executable,str(staged),'--candidate-dir',str(out),'--baseline-core',str(base/'NFSUG-pc-owned-assembly-core-tests/capture-host.dll')],check=True)
r=json.loads((out/'owned-core-test-report.json').read_text());assert r['result']=='PASS_SOURCE_TRANSFER_CORE_PARITY';r.update(source_sha256={n:sha(here/n) for n in ['source_frame.c','source_frame.h','source_reader.c','source_reader.h','source_transfer_observer.inc','source_transfer_core_api.inc']},maintained_test_sha256=sha(Path(__file__)),reader_direct_test_receipt_sha256=sha(reader/'reader-direct-test-report.json'),maintained_build_receipt_sha256=sha(out/'source-transfer-build-report.json'),base_test_source_sha256=sha(here/'test_owned_assembly_core.py'))
(out/'source-transfer-core-test-report.json').write_text(json.dumps(r,indent=2));print('PASS_MAINTAINED_TRANSFER_CORE_INTEGRATION',r['core_sha256'])
