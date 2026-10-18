"""Matched fullscene live accounting; no promotion from short-run timing alone."""
import json,re,sys,runpy
from pathlib import Path
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010');results=[]
for label,selected in (('candidate',True),):
 log=(p/'geometry-single-copy-live.log').read_text();raw=re.findall(r'G:[^\r\n]*owned-native-\d+\.json',log)[-1];r=json.loads(Path(raw).read_text())
 sys.argv=['coverage',raw,str(p/('geometry-single-copy-'+label+'-coverage.json'))];runpy.run_path('work/camera/verify_preclose_native_coverage.py',run_name='__main__');coverage=json.loads(Path(sys.argv[2]).read_text())
 ledger=r['original_update_retention']['complete_original_updates'];updates=ledger['records'];assert ledger['dropped']==0 and ledger['total']==len(updates)>0
 assert all(b['refresh']==a['refresh']+1 for a,b in zip(updates,updates[1:]))
 assert all(a['started_ns']<=a['completed_ns'] for a in updates)
 jobs=r['world_preparation_stage_samples'];assert jobs and all(x['terminal'][5]['geometry_input_selected'] is selected for x in jobs)
 s=r['shutdown_evidence'];child=s['preparation_service_shutdown'];assert not child['child_alive'] and not child['preparation_thread_alive'] and child['child_exitcode']==0 and not child['errors']
 assert s['native_owner_released'] and s['active_contexts_after_close']==0 and not s['gpu_thread_alive'] and s['pending_scene_count']==s['retained_scene_count']==0
 assert r['hud_lease_cleanup']['owner_stats']==[0,0,0]
 a=coverage['active_native_intervals']
 results.append(dict(variant=label,raw=raw,updates=len(updates),child_jobs=len(jobs),selection_verified=True,cleanup_verified=True,active_frames=coverage['active_successful_frames'],max_gap_ms=a['max_ms'],over25=a['over25'],over33=a['over33'],over50=a['over50'],skipped_indices=a['skipped_indices_between_successes'],initial_hold_ms=coverage['initial_after_deadline_hold_ms'],trailing_hold_ms=coverage['trailing_hold_ms'],last_update_start_late_ms=(updates[-1]['started_ns']-updates[-1]['original_deadline_ns'])/1e6,cadence_gate_passed=coverage['cadence_gate_passed']))
result=dict(result='PASS_SINGLE_COPY_GEOMETRY_LIVE_ACCOUNTING',runs=results,scope='Single30s selected candidate, contiguous original updates and cleanup. Not a matched comparison or sustained60/scanout qualification.')
(p/'geometry-single-copy-live-accounting.json').write_text(json.dumps(result,indent=2));print(result['result']);print(results)
