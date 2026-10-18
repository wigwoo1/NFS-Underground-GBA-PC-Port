"""Exercise the verified varied route through actual native GL presentation/audio."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
from PIL import Image
import numpy as np
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-audio-position-probe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=out);out=parser.parse_args().output_dir
b=json.loads((out/'live-build-report.json').read_text());t=json.loads((out/'live-test-report.json').read_text());i=json.loads((out/'input-ledger-test-report.json').read_text());reference=json.loads((base/'NFSUG-pc-traffic-refresh2-route-tests/diverse-route-report.json').read_text())
assert b['core_kind']=='diagnostic-refresh2-audio-position' and t['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE'
assert b['exe_sha256']==t['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe') and b['core_sha256']==t['core_sha256']==reference['core_sha256']==sha(out/'capture-host.dll')
assert i['result']=='PASS_ACTUAL_HOST_SCRIPTED_INPUT_LEDGER' and i['source_sha256']==sha(source/'live_host.c') and i['script_sha256']==sha(source/'test_traffic_live_inputs.py')
for n,h in b['source_sha256'].items():assert sha(source/n)==h,n
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]}
csv_path=out/'audio-position-6000.csv';assert not csv_path.exists(),'Preserve existing diagnostic run; inspect its result before rerunning'
assert b['diagnostic_staged_source_sha256']==sha(out/'live_host_position_probe.c')
report=out/'traffic-live-6000.json';pcm=out/'traffic-live-6000.pcm';capture=out/'traffic-live-6000.rgba'
cmd=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(rom),'--state',str(state),'--hidden','--script-diverse','--frames','6000','--geometry-cache','--report',str(report),'--audio-dump',str(pcm),'--capture',str(capture)]
env=dict(os.environ);env['NF_AUDIO_POSITION_CSV']=str(csv_path)
for n in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE']:env.pop(n,None)
subprocess.run(cmd,env=env,check=True,timeout=240);r=json.loads(report.read_text())
assert r['exit_code']==0 and r['scripted_input_mode']==2 and r['logic_frames']==6000 and r['timing_errors']==r['present_failures']==r['prepare_failures']==0
assert r['capture_failure_count']==10 and r['published_frames']==5990 and r['capture_failure_first_frame']==1 and r['capture_failure_last_frame']==10 and r['capture_gap_fallback_count']==0
assert [x[0] for x in r['capture_failure_log']]==[x['step'] for x in reference['failures']]
assert r['native_renders']>5000 and r['native_presents']>5000 and r['capture_native'] and r['render_thread_owns_gl'] and not r['live_readback']
assert r['audio_frames']==reference['audio_frames']==4430117 and sha(pcm)==reference['audio_sha256']=='e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807'
assert r['audio_dropped_frames']==0 and r['audio_device_opened'] and r['audio_queue_observations']>0
assert r['processed_sequence']==r['final_sequence'] and r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
assert before=={str(p):sha(p) for p in [rom,state]}
raw=capture.read_bytes();assert len(raw)==3840*2160*4;pixels=np.frombuffer(raw,np.uint8).reshape(2160,3840,4)[::-1].copy();assert pixels[:,:3240,3].max()==255 and not pixels[:,3240:].any();Image.fromarray(pixels).save(out/'traffic-live-6000.png')
ideal=6000*280896/16777216
result=dict(result='VERIFIED_AUDIO_POSITION_DIAGNOSTIC_ROUTE',session=r,command=cmd,original_timing_ideal_seconds=ideal,original_wall_clock_budget_met=ideal<=r['elapsed_seconds']<=ideal+.25,audio_pcm_exact=True,sampled_audio_queue_empty_observed=r['audio_queue_empty_observations']>0,late_capture_misses=0,all_known_capture_gaps_held_without_gba_fallback=True,full_scene_60fps=False,full_race_verified=False,physical_xbox_tested=False,script_sha256=sha(Path(__file__)),build_receipt_sha256=sha(out/'live-build-report.json'),regression_receipt_sha256=sha(out/'live-test-report.json'),input_test_receipt_sha256=sha(out/'input-ledger-test-report.json'),reference_receipt_sha256=sha(base/'NFSUG-pc-traffic-refresh2-route-tests/diverse-route-report.json'),exe_sha256=b['exe_sha256'],core_sha256=b['core_sha256'],screenshot_sha256=sha(out/'traffic-live-6000.png'),pcm_sha256=sha(pcm),rom_state_sha256=before,limits='Scripted local AMD GL/audio run. Full-scene interpolation and full race not verified. Queue is sampled, not proof of continuous audible playback.No post-startup source gaps in this route; other routes and full-scene smooth motion remain unverified.')
assert csv_path.exists();result.update(position_csv_sha256=sha(csv_path),diagnostic_only=True,staged_source_sha256=sha(out/'live_host_position_probe.c'))
(out/'traffic-live-route-test-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='session'},indent=2));print(json.dumps({k:r[k] for k in ['elapsed_seconds','native_renders','native_presents','max_logic_capture_ms','capture_failure_count','capture_gap_hold_frames','capture_gap_fallback_count','audio_queue_empty_events']},indent=2))
