"""Frozen repaired endpoint GPU check; never replace a live route test."""
from pathlib import Path
import hashlib,json,subprocess,uuid,zipfile
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Traffic-20261017';folder=out/'traffic-gpu-results';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
terminal=out/'route-results/current-native-route-report.json';assert terminal.exists(),'Wait for SAME route session54477 terminal report; do not replace installed APK yet'
route=json.loads(terminal.read_text());assert route['all_original_pixels_audio_clocks_exact'] and route['native']['steps']==6000
adb=base/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=40):return subprocess.run([str(adb),'-s','emulator-5556']+args,capture_output=True,check=True,timeout=timeout)
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30' and run(['shell','getprop','sys.boot_completed']).stdout.strip()==b'1'
test=json.loads((out/'traffic-gpu-test/apk-build-report.json').read_text());production=json.loads((out/'production/apk-build-report.json').read_text())
assert test['instrumentation'] and test['runner']=='TrafficSceneGpuInstrumentation' and not production['instrumentation']
assert test['sha256']==sha(out/'traffic-gpu-test/NFSUG-Android-Core-Preview.apk')
for name,h in test['source_sha256'].items():assert sha(source/name)==h,name
for name,h in production['source_sha256'].items():
 if name.startswith('java/'):assert test['source_sha256'][name]==h,name
with zipfile.ZipFile(out/'traffic-gpu-test/NFSUG-Android-Core-Preview.apk') as a,zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as b:
 for abi in ['x86_64','arm64-v8a']:assert a.read('lib/'+abi+'/libnfsug_android_core.so')==b.read('lib/'+abi+'/libnfsug_android_core.so')
witness=json.loads((out/'gap3519-results/first-gap-report.json').read_text());assert witness['step3519']['retained_retry_present'] and witness['step3519']['kind']==1
inputs={'owner0-kind0.bin':'background.bin'}
for owner in range(1):
 for kind,extension in [(1,'world'),(2,'road'),(3,'wall'),(4,'proof')]:inputs['owner'+str(owner)+'-kind'+str(kind)+'.bin']='owner'+str(owner)+'-'+extension+'.bin'
for name in inputs.values():assert sha(out/'gap3519-results'/name)==witness['frozen_component_sha256'][name],name
folder.mkdir(exist_ok=True);prefix='traffic3519-'+uuid.uuid4().hex[:12]
print(run(['install','-r',str(out/'traffic-gpu-test/NFSUG-Android-Core-Preview.apk')]).stdout.decode(),flush=True)
for target,name in inputs.items():
 temporary='/data/local/tmp/'+prefix+'-'+target;run(['push',str(out/'gap3519-results'/name),temporary]);run(['shell','run-as','org.codex.nfsugpreview','cp',temporary,'files/'+prefix+'-'+target]);run(['shell','rm',temporary])
run(['logcat','-c']);result=run(['shell','am','instrument','-w','-r','-e','fixturePrefix',prefix,'org.codex.nfsugpreview/.TrafficSceneGpuInstrumentation'],timeout=180);text=result.stdout.decode();(folder/'instrumentation-run.log').write_text(text);print(text,flush=True)
(folder/'instrumentation-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGRecoveredGPU:E','AndroidRuntime:E','*:S']).stdout)
assert 'PASS_TRAFFIC_SCENE3519_RETAINED_GPU' in text and 'INSTRUMENTATION_CODE: -1' in text
r=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+prefix+'-gpu-report.json']).stdout);assert r['context_recreated'] and r['actual_retained_renderer'] and not r['full_scene_60fps'] and not r['live_gameplay']
images=[]
for row in r['scene']['images']:
 width,height=row['width'],row['height'];data=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+prefix+'-'+str(width)+'.rgba'],timeout=60).stdout
 assert len(data)==width*height*4 and hashlib.sha256(data).hexdigest()==row['sha256'];path=folder/('scene3519-'+str(width)+'.rgba');path.write_bytes(data);images.append(dict(path=str(path),sha256=sha(path),width=width,height=height))
r.update(test_apk_sha256=test['sha256'],production_apk_sha256=production['sha256'],production_java_native_matched=True,fixture_sha256={name:sha(out/'gap3519-results'/name) for name in inputs.values()},images=images,runner_sha256=sha(Path(__file__)),route_report_sha256=sha(terminal),limits='Frozen repaired endpoint native/4K GPU draw and context recreation on emulator. No live motion, fidelity to every original pixel, physical-device performance/audio, full race or smooth60 proof.')
(folder/'traffic-scene-gpu-report.json').write_text(json.dumps(r,indent=2));print('SAVED_RECOVERED_ENDPOINT_GPU_REPORT',flush=True)
