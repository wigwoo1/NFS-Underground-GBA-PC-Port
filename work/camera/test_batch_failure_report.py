import subprocess,sys,json,hashlib,shutil
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/batch-failure-report-20261007');cp.mkdir(exist_ok=True)
command=[sys.executable,'work/camera/run_batch_failure_diagnostic.py','--startup-readiness','--full-scene','--background-prepare','--process-prepare','--shared-process-output','--precompute-world-samples','--presentation-delay-refreshes','12','--python-thread-switch-ms','1','--capture-sky','--interpolate-sky','--continuous-sky','--native-present-callback','--original-update-boundary','--swap-interval','0','--smoke-seconds','5']
p=subprocess.run(command,capture_output=True,text=True,timeout=90);(cp/'diagnostic-output.txt').write_text(p.stdout+p.stderr)
assert p.returncode!=0 and 'NF_DIAGNOSTIC_BATCH_FAILURE' in p.stderr
assert 'not JSON serializable' not in p.stderr
report_paths=[Path(x.strip()) for x in p.stdout.splitlines() if x.strip().endswith('.json') and 'owned-native-' in x]
assert len(report_paths)==1
r=json.loads(report_paths[0].read_text());assert r['result']=='FAILED' and 'NF_DIAGNOSTIC_BATCH_FAILURE' in r['error']
s=r['shutdown_evidence'];child=s['preparation_service_shutdown']
assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released']
for k in ('gpu_queries_after_close','gpu_fences_after_close','active_contexts_after_close','retained_scene_count','pending_scene_count','prepared_result_count'):assert s[k]==0
assert not child['child_alive'] and child['child_exitcode']==0 and not child['forced_termination'] and child['shared_mapping_closed'] and child['connection_closed'] and not child['retained_previous_scene']
assert isinstance(r['presentation_samples'],list)
for line in p.stdout.splitlines():
 if line.strip().endswith('.json') and ('owned-native-' in line or 'pool-cleanup-' in line):shutil.copy2(Path(line.strip()),cp/Path(line.strip()).name)
for n in ('live_native_batch_candidate.py','run_batch_failure_diagnostic.py','test_batch_failure_report.py'):shutil.copy2(Path('work/camera')/n,cp/n)
hp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json');h=json.loads(hp.read_text());assert {k:hashlib.sha256(Path(k).read_bytes()).hexdigest().upper() for k in h}==h;shutil.copy2(hp,cp/hp.name)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS_EXPECTED_DIAGNOSTIC_FAILURE',exitcode=p.returncode,original_error_preserved=True,report_readable=True,compact_ledger_serializable=True,cleanup='PASS',protected_hashes_exact=True),indent=2));print('PASS expected worker failure, original error preserved, readable report, child/mapping/GPU cleanup, protected hashes exact')
