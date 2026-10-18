"""Sequential actual-host comparison with the same injected16ms swap delay."""
from pathlib import Path
import hashlib,json,os,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');source=root/'work/pc';base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-pc-present-lock-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'live-build-report.json').read_text());assert sha(out/'NFSUG-Source-Native-Preview.exe')==build['exe_sha256'];assert sha(out/'capture-host.dll')==build['core_sha256']
gpu=(source/'scene_gpu.c').read_text();old='if(ok&&!SwapBuffers(g->dc))ok=0;';assert gpu.count(old)==1
staged_gpu=out/'diagnostic-delayed-gpu.c';staged_gpu.write_text(gpu.replace(old,'if(ok)Sleep(16);'+old),encoding='utf-8')
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected={str(p):sha(p) for p in [rom,state]}
rows={};commands={}
for label,path in [('baseline',root/'outputs/nfsug-native-renderer/camera-research/pc-present-lock-20261017/before/live_host.c'),('candidate',source/'live_host.c')]:
 staged=out/(label+'-delay-host.c');staged.write_bytes(path.read_bytes());exe=out/(label+'-delay-host.exe');command=list(build['command'])
 command=[str(staged_gpu) if Path(value).name=='scene_gpu.c' else str(staged) if Path(value).name=='live_host.c' else value for value in command];command[command.index('-o')+1]=str(exe);command.insert(1,'-I'+str(source))
 compiled=subprocess.run(command,env=env,capture_output=True,text=True,timeout=90);(out/(label+'-delay-build.log')).write_text(compiled.stdout+compiled.stderr,encoding='utf-8');compiled.check_returncode()
 report=out/(label+'-delay-session.json');pcm=out/(label+'-delay.pcm');assert not report.exists(),'Preserve previous comparison'
 run=[str(exe),'--rom',str(rom),'--state',str(state),'--hidden','--frames','296','--script','--geometry-cache','--no-audio','--oracle',str(base/'NFSUG-android-capture-local/capture-off/frames.raw'),'--audio-dump',str(pcm),'--report',str(report)]
 result=subprocess.run(run,env=env,capture_output=True,text=True,timeout=90);(out/(label+'-delay-run.log')).write_text(result.stdout+result.stderr,encoding='utf-8');result.check_returncode();r=json.loads(report.read_text())
 assert r['logic_frames']==296 and r['timing_errors']==r['original_frame_mismatches']==r['prepare_failures']==r['present_failures']==0
 assert r['processed_sequence']==r['final_sequence'] and r['background_allocations']==r['background_releases'] and r['geometry_allocations']==r['geometry_releases']
 assert not r['full_scene_60fps'] and not r['audio_device_opened']
 rows[label]=dict(session=r,pcm_sha256=sha(pcm),exe_sha256=sha(exe),staged_host_sha256=sha(staged));commands[label]=run
assert rows['baseline']['pcm_sha256']==rows['candidate']['pcm_sha256']
old_wait=rows['baseline']['session']['phases']['publish_lock_wait'];new_wait=rows['candidate']['session']['phases']['publish_lock_wait'];assert new_wait['mean_ms']<old_wait['mean_ms']
ideal=296*280896/16777216;candidate=rows['candidate']['session'];assert ideal<=candidate['elapsed_seconds']<=ideal+.25
assert protected=={str(p):sha(p) for p in [rom,state]}
report=dict(result='VERIFIED_INJECTED_SWAP_WAIT_PUBLICATION_DECOUPLING',rows=rows,commands=commands,injected_delay_ms=16,diagnostic_only=True,original_timing_ideal_seconds=ideal,candidate_original_wall_clock_budget_met=True,exact_original_frame_oracle=True,exact_pcm_between_modes=True,baseline_publish_wait_mean_ms=old_wait['mean_ms'],candidate_publish_wait_mean_ms=new_wait['mean_ms'],gpu_source_sha256=sha(source/'scene_gpu.c'),staged_gpu_sha256=sha(staged_gpu),source_sha256=sha(source/'live_host.c'),script_sha256=sha(Path(__file__)),real_visible_scanout_verified=False,full_scene_60fps=False,limits='Two sequential fixed-input original-timed native-host runs with identical injected16ms Sleep before each SwapBuffers. This is a deliberately worst-case blocking callback, not real vblank timing or a physical monitor/input-latency measurement. Game logic/PCM unchanged; renderer may coalesce pending endpoints when slower than producer.')
(out/'delay-comparison-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','commands']},indent=2))
