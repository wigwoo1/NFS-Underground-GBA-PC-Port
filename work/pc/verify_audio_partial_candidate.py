"""Review exact candidate evidence; known residual starvation blocks release."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-partial-live-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
names=['live-build-report.json','live-test-report.json','logic-audit-test-report.json','input-ledger-test-report.json','traffic-live-route-test-report.json','partial-audio-component-report.json']
b,t,a,i,r,c=[json.loads((out/n).read_text()) for n in names]
assert b['core_kind']=='guarded-traffic-refresh2-candidate'
assert t['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE' and a['result']=='PASS_CURRENT_HOST_LOGIC_CADENCE_AUDIT'
assert i['result']=='PASS_ACTUAL_HOST_SCRIPTED_INPUT_LEDGER' and c['result']=='VERIFIED_ACTUAL_PARTIAL_AUDIO_BLOCKS_CONTROLLED_ONLY'
assert b['exe_sha256']==t['exe_sha256']==a['exe_sha256']==r['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert b['core_sha256']==t['core_sha256']==a['core_sha256']==r['core_sha256']==sha(out/'capture-host.dll')
assert a['source_sha256']==i['source_sha256']==c['source_sha256']==sha(source/'live_host.c')
assert a['test_sha256']==sha(source/'test_logic_audit.py') and c['script_sha256']==sha(source/'test_audio_partial_blocks.py') and i['script_sha256']==sha(source/'test_traffic_live_inputs.py')
assert t['test_source_sha256']==sha(source/'test_live_host.py') and r['script_sha256']==sha(source/'test_traffic_refresh2_live_route.py')
for n,h in b['source_sha256'].items():assert sha(source/n)==h,n
assert r['build_receipt_sha256']==sha(out/names[0]) and r['regression_receipt_sha256']==sha(out/names[1]) and r['input_test_receipt_sha256']==sha(out/names[3])
assert i['audio_submission_controlled_test_sha256']==sha(out/names[5])
assert a['original_native_display_hashes_exact'] and a['rom_state_unchanged'] and a['audio_frames']==443007
assert a['audio_sha256']=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
assert r['audio_pcm_exact'] and r['original_wall_clock_budget_met'] and r['late_capture_misses']==0
assert not r['sampled_audio_queue_empty_observed'] and r['session']['audio_dropped_frames']==0
residual=base/'NFSUG-pc-audio-residual-analysis/residual-analysis.json';e=json.loads(residual.read_text())
assert e['source_unchanged_sha256']==sha(source/'live_host.c') and e['component_receipt_sha256']==sha(out/names[5]) and e['script_sha256']==sha(source/'analyze_audio_partial_shortage.py')
shortages=c['rows']['candidate']['measured']['empty_events'];assert shortages==len(e['events']['candidate'])==1
assert e['events']['candidate'][0]['previous_buffers']==2 and e['events']['candidate'][0]['would_immediate_prior_tail_cover_interval']
report=dict(result='VERIFIED_CANDIDATE_COMPONENTS_RELEASE_WITHHELD',release_allowed=False,release_blocker='One known reproducible simulated starvation: buffer count does not establish remaining sound duration.',rough_project_percent=72,exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],original_timing_and_pcm_verified=True,source_sky_consecutive_changes=a['source_sky_consecutive_changes'],local_live_route_sampled_empty_events=r['session']['audio_queue_empty_events'],controlled_residual_shortages=shortages,full_scene_60fps=False,physical_xbox_verified=False,intel_user_device_verified=False,receipt_sha256={n:sha(out/n) for n in names},residual_receipt_sha256=sha(residual),script_sha256=sha(Path(__file__)))
(out/'candidate-readiness-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
