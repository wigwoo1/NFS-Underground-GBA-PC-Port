"""Verify first-ever failure reporting against real separated capture histories."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-capture-counter-live-tests';previous=base/'NFSUG-pc-empty-plane-live-host-tests'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=(out/'before/live_host.c').read_text();current=(source/'live_host.c').read_text()
assert current==old.replace('if(!capture_failure_streak)capture_failure_first_frame=frames;','if(!capture_failure_count)capture_failure_first_frame=frames;',1)
b=json.loads((out/'live-build-report.json').read_text());r=json.loads((out/'live-test-report.json').read_text());before=json.loads((previous/'live-test-report.json').read_text())
assert b['exe_sha256']==r['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert r['test_source_sha256']==sha(source/'test_live_host.py') and r['build_receipt_sha256']==sha(out/'live-build-report.json')
for n,h in b['source_sha256'].items():assert sha(source/n)==h,n
assert r['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE' and len(r['cases'])==7
histories={}
for name,end,count in [('capture-gap-short',125,16),('capture-gap-sustained',134,25)]:
 a=before['cases'][name];z=r['cases'][name]
 assert a['capture_failure_first_frame']==120 and z['capture_failure_first_frame']==1
 assert a['capture_failure_log']==z['capture_failure_log'] and z['capture_failure_last_frame']==end and z['capture_failure_count']==count
 assert z['timing_errors']==z['original_frame_mismatches']==z['present_failures']==z['prepare_failures']==0
 histories[name]=dict(previous_first=120,corrected_first=1,last=end,failures=count,event_history_unchanged=True)
assert before['original_audio_sha256']==r['original_audio_sha256'] and before['screenshot_sha256']==r['screenshot_sha256']
report=dict(result='VERIFIED_CAPTURE_FAILURE_FIRST_EVER_COUNTER',cases=histories,all_seven_live_cases_passed=True,only_production_change='First failure field now gated on total count, not current streak',original_4k_endpoint_and_pcm_unchanged=True,exe_sha256=r['exe_sha256'],core_sha256=r['core_sha256'],build_receipt_sha256=sha(out/'live-build-report.json'),regression_receipt_sha256=sha(out/'live-test-report.json'),prior_regression_receipt_sha256=sha(previous/'live-test-report.json'),script_sha256=sha(Path(__file__)),rough_project_percent=70,full_scene_60fps=False,remaining_capture_gaps_fixed=False,audio_stutter_fixed=False)
(out/'capture-counter-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
