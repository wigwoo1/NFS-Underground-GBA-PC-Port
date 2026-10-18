from pathlib import Path
import hashlib,json,os,shutil,subprocess
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');source=root/'work/pc';base=Path('C:/NFSUG-Workspace');local=Path(__file__).resolve().parent;parent=base/'NFSUG-pc-audio-duration-tests';out=base/'NFSUG-pc-swap-observation-tests';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();receipt=json.loads((parent/'live-build-report.json').read_text())
for name,digest in receipt['source_sha256'].items():
 if name not in ['live_host.c','scene_gpu.c','scene_gpu.h']:assert sha(source/name)==digest,name
assert sha(parent/'capture-host.dll')==receipt['core_sha256']
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def run(command,name,timeout=90):
 result=subprocess.run([str(x) for x in command],env=env,capture_output=True,text=True,timeout=timeout);(out/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8');result.check_returncode();return result
command=list(receipt['command']);command[command.index('-o')+1]=str(out/'NFSUG-Source-Native-Preview.exe');run(command,'host-build');shutil.copyfile(parent/'capture-host.dll',out/'capture-host.dll')
test=local/'test_swap_observation.c';shutil.copyfile(test,source/test.name)
fixture=[str(test) if Path(arg).name=='live_host.c' else arg for arg in command if arg!='-mwindows'];fixture[fixture.index('-o')+1]=str(out/'swap-observation-fixture.exe');fixture.insert(1,'-I'+str(source));run(fixture,'fixture-build')
observed=run([out/'swap-observation-fixture.exe'],'fixture-run',timeout=30);result=json.loads(observed.stdout);assert result['result']=='PASS_REAL_WGL_SWAP_OBSERVATION_COMPONENT'
result.update(test_source_sha256=sha(test),gpu_source_sha256=sha(source/'scene_gpu.c'),header_sha256=sha(source/'scene_gpu.h'));(out/'swap-component-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
receipt.update(command=command,exe_sha256=sha(out/'NFSUG-Source-Native-Preview.exe'),core_kind='guarded-traffic-refresh2-swap-observation-candidate',swap_observation=True,live_integration_verified=False,builder_sha256=sha(Path(__file__)))
for name in ['live_host.c','scene_gpu.c','scene_gpu.h']:receipt['source_sha256'][name]=sha(source/name)
(out/'live-build-report.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(result,indent=2));print('PASS_SWAP_OBSERVATION_BUILD_AND_REAL_WGL_COMPONENT',flush=True)
