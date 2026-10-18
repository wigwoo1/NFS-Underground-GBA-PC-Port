"""Observe playback-queue health using the verified 3600-step original PCM oracle.

Queue emptiness is sampled. This does not measure audible gap duration or prove
that a queue without empty observations has continuous output between polls.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
source=Path(__file__).resolve().parent;root=source.parent.parent
base=Path(r'C:\NFSUG-Workspace')
p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=base/'NFSUG-pc-audio-queue-tests');p.add_argument('--expect-continuous-capture',action='store_true');args=p.parse_args();out=args.output_dir
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'live-build-report.json').read_text());tests=json.loads((out/'live-test-report.json').read_text())
assert tests['result']=='PASS_LIVE_SOURCE_NATIVE_HOST_LIMITED_PROTOTYPE' and tests['test_source_sha256']==sha(source/'test_live_host.py')
assert tests['build_receipt_sha256']==sha(out/'live-build-report.json')
for n,h in build['source_sha256'].items():assert sha(source/n)==h,n
exe=out/'NFSUG-Source-Native-Preview.exe';assert sha(exe)==tests['exe_sha256']==build['exe_sha256']
assert sha(out/'capture-host.dll')==tests['core_sha256']==build['core_sha256']
refdir=base/'NFSUG-pc-geometry-cache-host';reference=json.loads((refdir/'long-segment-report.json').read_text())
ref=reference['rows']['original-fast-reference'];assert reference['checks']['audio_exact'] and reference['checks']['original_clock_steps_exact']
assert ref['logic_frames']==3600 and ref['timing_errors']==0 and sha(refdir/'original-fast-reference-3600.pcm')==ref['pcm_sha256']
# Original-output oracle intentionally supports a changed core; ROM/state/inputs,
# all PCM bytes and runtime clocks must still match the original reference.
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in (rom,state)}
assert sorted(before.values())==sorted(reference['rom_state_sha256'].values())
path=out/'audio-queue-3600.json';pcm=out/'audio-queue-3600.pcm'
cmd=[str(exe),'--rom',str(rom),'--state',str(state),'--hidden','--script','--frames','3600','--geometry-cache','--report',str(path),'--audio-dump',str(pcm)]
env=dict(os.environ)
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE']:env.pop(name,None)
subprocess.run(cmd,env=env,check=True,timeout=180)
r=json.loads(path.read_text());assert r['exit_code']==0 and r['logic_frames']==3600 and r['timing_errors']==0 and r['present_failures']==0
assert r['audio_frames']==ref['audio_frames'] and sha(pcm)==ref['pcm_sha256']
assert r['audio_device_opened'] and r['audio_queue_observations']>0
assert r['audio_queue_empty_events']<=r['audio_queue_empty_observations']<=r['audio_queue_observations']
assert len(r['audio_queue_empty_pcm_frames'])==min(32,r['audio_queue_empty_events'])
assert r['processed_sequence']==r['final_sequence'] and r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
assert before=={str(p):sha(p) for p in (rom,state)}
if args.expect_continuous_capture:assert r['capture_failure_last_frame']<=10 and r['capture_gap_fallback_count']==0
ideal=3600*280896/16777216
result=dict(result='VERIFIED_SAMPLED_AUDIO_QUEUE_OBSERVATIONS',audio_queue_empty_observed=r['audio_queue_empty_observations']>0,audio_pcm_exact=True,no_capture_failures_after_startup=r['capture_failure_last_frame']<=10,original_reference_core_sha256=reference['core_sha256'],audio_frames=r['audio_frames'],pcm_sha256=sha(pcm),original_wall_clock_budget_met=ideal<=r['elapsed_seconds']<=ideal+.15,original_timing_ideal_seconds=ideal,session=r,command=cmd,exe_sha256=sha(exe),core_sha256=sha(out/'capture-host.dll'),build_receipt_sha256=sha(out/'live-build-report.json'),regression_receipt_sha256=sha(out/'live-test-report.json'),original_reference_receipt_sha256=sha(refdir/'long-segment-report.json'),original_reference_pcm_sha256=sha(refdir/'original-fast-reference-3600.pcm'),script_sha256=sha(Path(__file__)),rom_state_sha256=before,full_scene_60fps=False,scope='3600 scripted steps on local AMD system. Sampled driver queue state, not audible gap duration or physical Intel/Xbox/full-race validation.')
(out/'audio-queue-long-test-report.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='session'},indent=2))
print(json.dumps({k:r[k] for k in ['elapsed_seconds','audio_dropped_frames','audio_queue_observations','audio_queue_empty_observations','audio_queue_empty_events','audio_queue_min_buffers','audio_queue_max_buffers','audio_queue_empty_pcm_frames','capture_failure_last_frame','max_logic_capture_ms']},indent=2))
