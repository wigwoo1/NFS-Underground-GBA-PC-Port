import json
from pathlib import Path
source=Path('work/camera/prototype-runs/owned-native-1791634146505619600.json');r=json.loads(source.read_text());p=r['pause_retention'];events=r['pause_events']
assert p['total_records']==p['retained_records']==len(events)==3 and p['dropped_records']==0
for e in events:assert e['begin_ns']<=e['native_pause_ack_ns']<=e['end_ns']<=e['native_resume_ack_ns'] and e['duration_ns']==e['end_ns']-e['begin_ns']
f=r['frame_preparation_shutdown'];b=r['background_copy_shutdown'];s=r['shutdown_evidence'];child=s['preparation_service_shutdown']
assert f['joined'] and f['pending']==0 and f['owner_alive_after_preparation_join'] and f['owner_released_after_renderer_close']
assert not b['thread_alive'] and b['pending']==0 and b['counts']['failed']==0
assert not child['child_alive'] and not child['preparation_thread_alive'] and child['child_exitcode']==0 and not child['errors']
assert s['native_owner_released'] and s['active_contexts_after_close']==0 and not s['gpu_thread_alive'] and s['pending_scene_count']==s['retained_scene_count']==0
assert r['hud_lease_cleanup']['owner_stats']==[0,0,0]
a=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_intervals']
out=dict(result='PASS_BOUNDED_LIVE_UNIFIED_PAUSE_AND_CLEANUP',raw=str(source.resolve()),completed_pauses=len(events),native_intervals=a['count'],excluded_discontinuities=a['excluded'],max_native_ms=a['max_ms'],over25=a['over25'],cadence_qualified=False,scope='Three complete retained pause acknowledgments and final native/source/preparation cleanup. Does not independently prove all intermediate pause presentation/source-update invariants, reset behavior, pixel parity or sustained60. Retirement remains disabled.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/pooled-retirement-component-20261010/live-repeat-pause-audit.json').write_text(json.dumps(out,indent=2));print(out['result'],len(events),'pauses')
