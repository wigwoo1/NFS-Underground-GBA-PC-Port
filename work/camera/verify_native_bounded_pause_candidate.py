"""Bounded live counters and cleanup; explicitly no full-session cadence proof."""
import hashlib,json,sys
from pathlib import Path
from analyze_active_play_cadence import analyze
r=json.loads(Path(sys.argv[1]).read_text());s=r['bounded_diagnostic_stats'];rows=r['presentation_samples']
assert r['result']=='SMOKE_COMPLETE' and s['total_records']==r['presentations']==s['validated_records']
assert s['retained_records']==len(rows) and s['dropped_records']+len(rows)==s['total_records']
assert s['successful_presentations']+s['unsuccessful_presentations']==s['total_records']
assert s['whole_run_context_invariants_verified'] and not s['full_run_telemetry_retained']
assert r['timing']['original_clock_hz']==16777216 and r['timing']['cycles_per_update']==280896
assert abs(r['timing']['simulated_seconds']-r['original_updates']*280896/16777216)<1e-9
assert len(r['pause_events'])==3
for p in r['pause_events']:assert p['end_ns']>=p['begin_ns'] and p['duration_ns']==p['end_ns']-p['begin_ns']
shutdown=r['shutdown_evidence'];assert shutdown['active_contexts_after_close']==0 and not shutdown['gpu_thread_alive'] and shutdown['native_owner_released'] and not shutdown['preparation_thread_alive']
p=shutdown['preparation_service_shutdown'];assert p['child_exitcode']==0 and p['shared_mapping_closed'] and p['connection_closed'] and not p['forced_termination'] and not p['child_alive']
try:analyze(r)
except ValueError as error:assert 'truncated' in str(error)
else:raise AssertionError('Truncated report accepted for whole-run cadence')
protected=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text())
for name,digest in protected.items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest().upper()==digest
out=dict(result='PASS_BOUNDED_PAUSE_LIVE',report=sys.argv[1],stats=s,pause_events=3,original_updates=r['original_updates'],protected_files_verified=len(protected),truncated_cadence_rejected=True,scope='Live whole-run context/result counts and three pause events; not whole-run source identity, sky/pixel cadence or physical controller proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
