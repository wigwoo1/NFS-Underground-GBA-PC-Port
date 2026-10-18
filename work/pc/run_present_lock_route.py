"""Bounded native PC route with real WinMM output; not a smooth60 acceptance."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');source=root/'work/pc';base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-present-lock-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'live-build-report.json').read_text());audit=json.loads((out/'logic-audit-test-report.json').read_text());component=json.loads((out/'protocol-report.json').read_text());reference=json.loads((base/'NFSUG-pc-traffic-refresh2-route-tests/diverse-route-report.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--tag',default='present-lock-route');tag=parser.parse_args().tag;assert re.fullmatch('[a-z0-9-]{1,40}',tag)
assert build['core_kind']=='guarded-traffic-refresh2-present-lock-candidate'
assert audit['result']=='PASS_CURRENT_HOST_LOGIC_CADENCE_AUDIT' and audit['original_native_display_hashes_exact']
assert build['exe_sha256']==audit['exe_sha256']==sha(out/'NFSUG-Source-Native-Preview.exe')
assert build['core_sha256']==audit['core_sha256']==reference['core_sha256']==sha(out/'capture-host.dll')
for name,digest in build['source_sha256'].items():assert sha(source/name)==digest,name
assert audit['source_sha256']==sha(source/'live_host.c')
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected={str(p):sha(p) for p in [rom,state]}
report=out/(tag+'-6000.json');pcm=out/(tag+'-6000.pcm');capture=out/(tag+'-6000.rgba');assert not report.exists(),'Preserve a previous run'
command=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(rom),'--state',str(state),'--hidden','--script-diverse','--frames','6000','--geometry-cache','--report',str(report),'--audio-dump',str(pcm),'--capture',str(capture)]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE','NF_AUDIO_POSITION_CSV']:env.pop(name,None)
start=time.monotonic();process=subprocess.Popen(command,env=env);(out/(tag+'-run-state.json')).write_text(json.dumps(dict(phase='live',pid=process.pid,command=command)),encoding='utf-8');print('STARTED_AUDIO_DURATION_ROUTE',process.pid,flush=True)
code=process.wait(timeout=240);r=json.loads(report.read_text());assert code==r['exit_code']==0
assert r['logic_frames']==6000 and r['timing_errors']==r['present_failures']==r['prepare_failures']==0
assert r['capture_failure_count']==10 and r['published_frames']==5990 and r['capture_failure_last_frame']==10 and r['capture_gap_fallback_count']==0
assert [entry[0] for entry in r['capture_failure_log']]==[entry['step'] for entry in reference['failures']]
assert r['native_renders']>5000 and r['native_presents']>5000 and not r['live_readback'] and r['render_thread_owns_gl']
assert r['audio_frames']==reference['audio_frames']==4430117 and sha(pcm)==reference['audio_sha256']=='e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807'
assert r['audio_device_opened'] and r['audio_dropped_frames']==0
assert r['audio_duration_queries']>0 and r['audio_duration_valid']>0 and r['audio_duration_valid']+r['audio_duration_unknown']==r['audio_duration_queries']
assert r['processed_sequence']==r['final_sequence'] and r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
assert protected=={str(p):sha(p) for p in [rom,state]}
assert capture.stat().st_size==3840*2160*4
ideal=6000*280896/16777216
result=dict(result='VERIFIED_PRESENT_LOCK_NATIVE_PC_ROUTE_LIMITED_SCOPE',session=r,command=command,wall_seconds=time.monotonic()-start,original_timing_ideal_seconds=ideal,original_wall_clock_budget_met=ideal<=r['elapsed_seconds']<=ideal+.25,pcm_sha256=sha(pcm),pcm_exact=True,logic_audit_receipt_sha256=sha(out/'logic-audit-test-report.json'),component_receipt_sha256=sha(out/'protocol-report.json'),build_receipt_sha256=sha(out/'live-build-report.json'),exe_sha256=build['exe_sha256'],core_sha256=build['core_sha256'],runner_sha256=sha(Path(__file__)),rom_state_sha256=protected,physical_audible_quality_verified=False,full_scene_60fps=False,full_race=False,intel_user_device_tested=False,limits='Scripted local AMD native GL and real WinMM submission at original game timing. Driver queue is sampled; absence of empty polls cannot prove continuous audible output or latency. No full-scene interpolation, full race, physical Xbox or user Intel machine verification.')
(out/(tag+'-report.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');(out/(tag+'-run-state.json')).write_text(json.dumps(dict(phase='terminal',passed=True)),encoding='utf-8')
print(json.dumps({key:r[key] for key in ['logic_frames','elapsed_seconds','native_presents','audio_frames','audio_dropped_frames','audio_queue_empty_events','audio_duration_queries','audio_duration_valid','audio_duration_unknown','capture_gap_fallback_count']},indent=2),flush=True);print(result['result'],flush=True)
