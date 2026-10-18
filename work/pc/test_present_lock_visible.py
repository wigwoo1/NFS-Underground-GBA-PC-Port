from pathlib import Path
import hashlib,json,os,subprocess,time
base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-present-lock-tests';root=Path('Y:/CODEX/NFSUG-Native-PC-Port')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'live-build-report.json').read_text());long=json.loads((out/'present-lock-route-report.json').read_text())
assert long['result']=='VERIFIED_PRESENT_LOCK_NATIVE_PC_ROUTE_LIMITED_SCOPE'
assert sha(out/'NFSUG-Source-Native-Preview.exe')==build['exe_sha256']
assert sha(out/'capture-host.dll')==build['core_sha256']
report=out/'visible-present-session.json';assert not report.exists()
pcm=out/'visible-present.pcm'
cmd=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'),'--state',str(root/'work/integration-0.state'),'--frames','296','--script','--geometry-cache','--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw'),'--audio-dump',str(pcm),'--report',str(report)]
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS','NF_TEST_MOTION_CAPTURE_PROFILE','NF_AUDIO_POSITION_CSV']:env.pop(name,None)
p=subprocess.Popen(cmd,env=env);print('VISIBLE_TEST_STARTED',p.pid,flush=True)
code=p.wait(timeout=60);r=json.loads(report.read_text());sync=r['presentation_sync']
assert code==r['exit_code']==0 and r['logic_frames']==296
assert r['timing_errors']==r['original_frame_mismatches']==r['present_failures']==r['prepare_failures']==0
assert r['processed_sequence']==r['final_sequence']
assert r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
assert sync['observed'] and sync['visible_presents']>0 and sync['requested_interval']==sync['reported_interval']==1 and sync['set_failures']==0
assert r['audio_device_opened'] and r['audio_dropped_frames']==0
reference=json.loads((out/'logic-audit-test-report.json').read_text())
# PCM identity is checked against the same fixed-input hidden diagnostic run.
assert sha(pcm)==sha(out/'candidate-delay.pcm')
result=dict(result='VERIFIED_VISIBLE_SWAP_POLICY_FIXED_INPUT_LIMITED_SCOPE',session=r,command=cmd,exe_sha256=build['exe_sha256'],core_sha256=build['core_sha256'],pcm_sha256=sha(pcm),runner_sha256=sha(Path(__file__)),physical_scanout_verified=False,tearing_verified=False,full_scene_60fps=False,limits='Ordinary visible HWND on local AMD driver, original-frame oracle and exact PCM. Driver-reported interval1 and present intervals do not prove physical scanout, tearing absence or full-scene interpolation.')
(out/'visible-present-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:r[k] for k in ['elapsed_seconds','native_presents','presentation_sync','phases']},indent=2),flush=True)
