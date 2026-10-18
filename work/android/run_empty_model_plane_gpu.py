"""Run the bounded coverage test only on the owned Android emulator."""
from pathlib import Path
import hashlib,json,subprocess
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Empty-Model-Plane-20261017';folder=out/'gpu-scene-results';folder.mkdir(exist_ok=True);adb=base/'android-tools/sdk/platform-tools/adb.exe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=40):return subprocess.run([str(adb),'-s','emulator-5556']+args,check=True,capture_output=True,timeout=timeout)
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30'
assert run(['shell','getprop','sys.boot_completed']).stdout.strip()==b'1'
build=json.loads((out/'gpu-scene-test/apk-build-report.json').read_text());reference=json.loads((out/'compile-check/apk-build-report.json').read_text())
assert build['instrumentation'] and build['runner']=='EmptyModelPlaneInstrumentation' and not build['native_capture']
assert build['sha256']==sha(out/'gpu-scene-test/NFSUG-Android-Core-Preview.apk')
for name,h in build['source_sha256'].items():assert sha(source/name)==h,name
for name,h in reference['source_sha256'].items():
 if name.startswith('java/'):assert build['source_sha256'][name]==h,name
print(run(['install','-r',str(out/'gpu-scene-test/NFSUG-Android-Core-Preview.apk')]).stdout.decode(),flush=True)
fixtures=[('scene3593',base/'NFSUG-pc-scene-prepare-failure-replay'),('scene3800',base/'NFSUG-pc-empty-plane-second-failure')];fixture_hashes={}
for prefix,fixture in fixtures:
 for p in sorted(fixture.glob('witness-owner*-kind*.bin')):
  name=prefix+'-'+p.name.removeprefix('witness-');temporary='/data/local/tmp/nfsug-empty-'+name
  run(['push',str(p),temporary]);run(['shell','run-as','org.codex.nfsugpreview','cp',temporary,'files/'+name]);run(['shell','rm',temporary]);fixture_hashes[name]=sha(p)
run(['logcat','-c']);result=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.EmptyModelPlaneInstrumentation'],timeout=180);text=result.stdout.decode();(folder/'instrumentation-run.log').write_text(text);print(text,flush=True)
(folder/'instrumentation-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGEmptyModelGPU:E','AndroidRuntime:E','*:S']).stdout)
assert 'PASS_ANDROID_EMPTY_MODEL_ACTUAL_SCENE_SHADER_GLES' in text and 'INSTRUMENTATION_CODE: -1' in text
r=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/empty-model-plane-gpu-report.json']).stdout);assert len(r['cases'])==16 and r['actual_native_scene_program'] and r['context_recreated']
for c in r['cases']:
 assert (c['red_pixels']==0) if c['case'] not in ['thin','visible'] else (c['red_pixels']>0)
assert len(r['frozen_complete_retained_scenes'])==2 and all(x['strict_model_plane_failures_recovered']>0 and len(x['images'])==2 for x in r['frozen_complete_retained_scenes'])
for prefix,_ in fixtures:
 (folder/(prefix+'-240.rgba')).write_bytes(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+prefix+'-240.rgba']).stdout)
r.update(fixture_sha256=fixture_hashes,apk_sha256=build['sha256'],build_receipt_sha256=sha(out/'gpu-scene-test/apk-build-report.json'),runner_sha256=sha(Path(__file__)),scope='Actual NativeSceneGpu program/plane on isolated API30 SwiftShader with synthetic filled triangles at240x160 and3840x2160(active3240). Two frozen complete retained scenes rendered; no original-frame pixel-fidelity, live/physical-device cadence or original-game thin-line-raster proof.')
(folder/'gpu-verification-summary.json').write_text(json.dumps(r,indent=2));print('VERIFIED_ANDROID_ACTUAL_SCENE_SHADER_ZERO_COVERAGE_CONTROLS',flush=True)
