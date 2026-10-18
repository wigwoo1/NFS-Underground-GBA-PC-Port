"""Replay the exact refresh mismatch in control or guarded-handoff mode."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
here=Path(__file__).resolve().parent;base=Path(r"C:\NFSUG-Workspace")
p=argparse.ArgumentParser();p.add_argument('--handoff',action='store_true');args=p.parse_args();core=base/('NFSUG-pc-model-context-handoff' if args.handoff else 'NFSUG-pc-model-context-control');out=core/'probe';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();s=(here/'probe_background_gaps.py').read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('source=Path(__file__).resolve().parent;root=source.parent.parent;',f'source=Path({str(here)!r});root=source.parent.parent;')
replace("out=base/'NFSUG-pc-background-gap-probe'",f'out=Path({str(out)!r})')
replace("core_dir=base/'NFSUG-pc-geometry-cache-core'",f'core_dir=Path({str(core)!r})')
replace("core_dir/'geometry-cache-build-report.json'","core_dir/'context-refresh-build-report.json'")
replace("scene_stats=fn('nf_native_scene_stats',[P],None)","scene_stats=fn('nf_native_scene_stats',[P],None)\ndiag=fn('nfa_core_capture_context_rejection_info',[P,P,S])")
replace("row['native_scene_stats']=list(ns)","row['native_scene_stats']=list(ns)\n   context=(U*20)();assert diag(h,context,20);row['context_rejection_detail']=list(context[:16]);row['refresh_handoff_stats']=list(context[16:20])")
s=s.replace("'retained_owner_metadata','owner_join_checks'","'context_rejection_detail','refresh_handoff_stats'")
staged=out/'probe-context-refresh.py';staged.write_text(s);subprocess.run([sys.executable,str(staged)],check=True)
r=json.loads((out/'background-gap-probe-report.json').read_text());prior=json.loads((base/'NFSUG-pc-background-gap-probe/background-gap-milestone-report.json').read_text());assert r['audio_sha256']==prior['three_replay_audio_hashes_exact']
if args.handoff:
 assert not r['failures'] and all(row['native_scene_stats'][2]==0 for row in r['rows'])
 assert r['rows'][-1]['refresh_handoff_stats'][1]==1 and r['rows'][-1]['refresh_handoff_stats'][2]==0
else:
 assert [row['logic_step'] for row in r['failures']]==list(range(1947,1952))
 for row in r['failures']:
  d=row['context_rejection_detail'];assert d[0]==d[6] and d[1]==d[7] and d[2:5]==d[8:11] and d[5]==d[11]+1 and d[12]==d[13]==d[14]==1 and d[15]<=d[11]
r.update(result='PASS_CONTEXT_HANDOFF_RECOVERS_SCENE_458' if args.handoff else 'PASS_CONTEXT_FAILURE_IS_ONLY_ONE_REFRESH_AGE',handoff_enabled=args.handoff,maintained_probe_sha256=sha(Path(__file__)),parent_probe_sha256=sha(here/'probe_background_gaps.py'),build_receipt_sha256=sha(core/'context-refresh-build-report.json'))
(out/'context-refresh-probe-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['rows'][-1]['refresh_handoff_stats'])
