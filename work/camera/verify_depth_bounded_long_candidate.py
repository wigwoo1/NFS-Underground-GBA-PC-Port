"""Compare full-run counters/GC observations, never infer discarded frame details."""
import json,sys,hashlib
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
s=r['bounded_diagnostic_stats'];assert s['total_records']==r['presentations'] and s['retained_records']==len(r['presentation_samples']) and s['total_records']==s['retained_records']+s['dropped_records'];assert s['whole_run_thread_context_checked'];assert s['whole_run_native_identity_checked']
t=r['timing'];assert t['original_clock_hz']==16777216 and t['cycles_per_update']==280896 and abs(t['simulated_seconds']-r['original_updates']*280896/16777216)<1e-9
shutdown=r['shutdown_evidence'];assert not shutdown['gpu_thread_alive'] and not shutdown['preparation_thread_alive'] and shutdown['native_owner_released'] and shutdown['active_contexts_after_close']==0
for name,digest in json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text()).items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest().upper()==digest.upper()
assert r['gc_trace_dropped']==0;gc=r['gc_collection_samples'];bygen={i:dict(count=sum(x['generation']==i for x in gc),max_ms=max((x['end_ns']-x['start_ns'])/1e6 for x in gc if x['generation']==i)) for i in sorted({x['generation'] for x in gc})}
out=dict(result='PASS_BOUNDED_LONG_COUNTERS_CLEANUP_HASHES',updates=r['original_updates'],presentations=r['presentations'],retained=s['retained_records'],dropped=s['dropped_records'],whole_run_api_intervals=s['whole_run_api_intervals'],gc_by_generation=bygen,pause_count=len(r['pause_events']),scope='Whole counter/interval aggregates and GC observation; thread/context checked every append. Native commit identity checked every append; phase fidelity limited to retained window. No physical scanout verification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

