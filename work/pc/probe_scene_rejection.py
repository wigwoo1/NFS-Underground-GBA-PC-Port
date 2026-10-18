"""Replay the known missing scene with the read-only rejection detail export."""
from pathlib import Path
import hashlib,json,subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace");out=base/'NFSUG-pc-scene-rejection-tests';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((base/'NFSUG-pc-background-gap-probe/background-gap-milestone-report.json').read_text());assert prior['source_sha256']==sha(here/'probe_background_gaps.py')
s=(here/'probe_background_gaps.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('source=Path(__file__).resolve().parent;root=source.parent.parent;',f'source=Path({str(here)!r});root=source.parent.parent;')
replace("out=base/'NFSUG-pc-background-gap-probe'","out=base/'NFSUG-pc-scene-rejection-tests'")
replace("core_dir=base/'NFSUG-pc-geometry-cache-core'","core_dir=base/'NFSUG-pc-scene-rejection-core'")
replace("core_dir/'geometry-cache-build-report.json'","core_dir/'scene-rejection-build-report.json'")
replace("scene_stats=fn('nf_native_scene_stats',[P],None)","scene_stats=fn('nf_native_scene_stats',[P],None)\ndiag=fn('nfa_core_capture_scene_rejection_info',[P,P,S])")
replace("row['native_scene_stats']=list(ns)","row['native_scene_stats']=list(ns)\n   detail=(U*192)();assert diag(h,detail,192) and tuple(detail[:3])==(0x314a524e,1,192) and tuple(detail[6:10])==tuple(ns)\n   row['rejection_detail']=list(detail[16:25]);row['first_bad_event']=list(detail[32:41]);row['model_rejection_detail']=list(detail[48:56]);row['rejected_model_visits']=list(detail[64:177]);row['model_assembly_stats']=list(detail[177:180]);row['owned_assembly_stats']=list(detail[180:182]);row['owned_model_stats']=list(detail[182:186]);row['context_extract_stats']=list(detail[186:190]);row['context_guard_stats']=list(detail[190:192])")
s=s.replace("'retained_owner_metadata','owner_join_checks'","'rejection_detail','first_bad_event','model_rejection_detail','model_assembly_stats','owned_assembly_stats','owned_model_stats','context_extract_stats'")
staged=out/'probe-recorded-rejection.py';staged.write_text(s);subprocess.run([sys.executable,str(staged)],check=True)
r=json.loads((out/'background-gap-probe-report.json').read_text());assert [v['logic_step'] for v in r['failures']]==list(range(1947,1952)) and r['audio_sha256']==prior['three_replay_audio_hashes_exact']
r.update(maintained_probe_sha256=sha(Path(__file__)),parent_probe_sha256=sha(here/'probe_background_gaps.py'),diagnostic_build_receipt_sha256=sha(base/'NFSUG-pc-scene-rejection-core/scene-rejection-build-report.json'))
(out/'scene-rejection-probe-report.json').write_text(json.dumps(r,indent=2))
