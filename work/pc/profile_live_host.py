from pathlib import Path
import subprocess,os,json,hashlib,time
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-live-host-tests';env=dict(os.environ)
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:env.pop(key,None)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};results={}
for name,args in [('profile-original',['--original','--fast','--no-audio']),('profile-uncached',['--uncached-capture']),('profile-native',[])]:
 cmd=[str(out/'NFSUG-Source-Native-Preview.exe'),'--rom',str(rom),'--state',str(state),'--hidden','--script','--frames','1200','--report',str(out/f'{name}.json'),'--audio-dump',str(out/f'{name}.pcm')]+args
 subprocess.run(cmd,env=env,check=True,timeout=90);r=json.loads((out/f'{name}.json').read_text());assert r['logic_frames']==1200 and r['timing_errors']==0 and r['present_failures']==0 and r['processed_sequence']==r['final_sequence'];assert r['phases']['core_step']['count']==1200 and r['phases']['logic_iteration']['count']==1200;results[name]=r;print(name,json.dumps(r),flush=True)
assert results['profile-native']['native_renders']>0 and results['profile-native']['audio_dropped_frames']==0
assert sha(out/'profile-original.pcm')==sha(out/'profile-native.pcm')==sha(out/'profile-uncached.pcm')
assert results['profile-native']['single_build_reader'] and not results['profile-uncached']['single_build_reader']
assert results['profile-native']['elapsed_seconds']<=1200*280896/16777216+.2
assert results['profile-native']['phases']['source_capture']['mean_ms']<results['profile-uncached']['phases']['source_capture']['mean_ms']
assert before=={str(p):sha(p) for p in [rom,state]}
b=dict(result='PASS_LONGER_LIVE_TIMING_PROFILE_PCM_EXACT',logic_frames=1200,original_hz=16777216/280896,ideal_seconds=1200*280896/16777216,audio_frames=results['profile-native']['audio_frames'],audio_sha256=sha(out/'profile-native.pcm'),rom_state_sha256=before,source_sha256=sha(Path(__file__)),exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),gpu_metrics_are_cpu_submission_times=True,full_scene_60fps=False,cases=results)
(out/'live-profile-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k!='cases'},indent=2))
