"""One source-bound paired6000-step Android route, no retries to hunt a pass."""
from pathlib import Path
import hashlib,json,subprocess,time,uuid,zipfile
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Native-Wide-20261017';folder=out/'route-results';folder.mkdir(exist_ok=True);adb=base/'android-tools/sdk/platform-tools/adb.exe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=40):return subprocess.run([str(adb),'-s','emulator-5556']+args,check=True,capture_output=True,timeout=timeout)
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30'
assert run(['shell','getprop','sys.boot_completed']).stdout.strip()==b'1'
test=json.loads((out/'route-test/apk-build-report.json').read_text());production=json.loads((out/'production/apk-build-report.json').read_text());assert test['native_capture'] and test['runner']=='NativeRouteInstrumentation'
for name,h in test['source_sha256'].items():assert sha(source/name)==h,name
for name,h in production['source_sha256'].items():
 if name.startswith('java/'):assert test['source_sha256'][name]==h,name
assert test['sha256']==sha(out/'route-test/NFSUG-Android-Core-Preview.apk') and production['sha256']==sha(out/'production/NFSUG-Android-Core-Preview.apk')
with zipfile.ZipFile(out/'route-test/NFSUG-Android-Core-Preview.apk') as a,zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as b:
 for abi in ['x86_64','arm64-v8a']:
  name='lib/'+abi+'/libnfsug_android_core.so';assert a.read(name)==b.read(name)
reference=base/'NFSUG-pc-traffic-refresh2-route-tests/diverse-route-report.json';oracle=json.loads(reference.read_text());assert oracle['steps']==6000 and len(oracle['input_keys'])==6000
ledger=folder/'input-keys.json';ledger.write_text(json.dumps(oracle['input_keys']))
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};assert list(before.values())==['53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593','49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104']
print(run(['install','-r',str(out/'route-test/NFSUG-Android-Core-Preview.apk')]).stdout.decode(),flush=True)
prefix='native-route-'+uuid.uuid4().hex[:12];(folder/'run-state.json').write_text(json.dumps(dict(prefix=prefix,adb=str(adb),emulator='emulator-5556',started_at=time.time()),indent=2))
for suffix,p in [('.gba',rom),('.state',state),('-keys.json',ledger)]:
 temporary='/data/local/tmp/'+prefix+suffix;run(['push',str(p),temporary]);run(['shell','run-as','org.codex.nfsugpreview','cp',temporary,'files/'+prefix+suffix]);run(['shell','rm',temporary])
run(['logcat','-c']);result=run(['shell','am','instrument','-w','-r','-e','fixturePrefix',prefix,'org.codex.nfsugpreview/.NativeRouteInstrumentation'],timeout=1800);text=result.stdout.decode();(folder/'instrumentation-run.log').write_text(text);print(text,flush=True)
(folder/'instrumentation-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGNativeRoute:I','AndroidRuntime:E','*:S']).stdout)
assert 'VERIFIED_ANDROID_PAIRED_ROUTE_ORIGINAL_PARITY_CAPTURE_COVERAGE_RECORDED' in text and 'INSTRUMENTATION_CODE: -1' in text
r=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+prefix+'-report.json']).stdout);assert r['all_original_pixels_audio_clocks_exact'] and r['native']['steps']==r['original']['steps']==6000
assert r['native']['original_audio_frames']==oracle['audio_frames'] and r['native']['original_audio_sha256']==oracle['audio_sha256']
missing=r['native']['missing_steps'];failed=r['native']['preparation_failure_steps'];assert r['native']['captured_preflighted_scenes']+len(missing)+len(failed)==6000
assert before=={str(p):sha(p) for p in [rom,state]}
r.update(production_apk_sha256=production['sha256'],test_apk_sha256=test['sha256'],matched_production_java_and_libraries=True,input_keys_sha256=sha(ledger),pc_route_reference_sha256=sha(reference),late_capture_missing_steps=[i for i in missing if i>10],late_preparation_failure_steps=[i for i in failed if i>10],rom_state_unchanged_sha256=before,runner_sha256=sha(Path(__file__)),cpu_source_coverage_gate_met=not any(i>10 for i in missing+failed),scope='Paired unpaced original/native-source6000-step route on API30 emulator. Original display/audio/clock comparison plus CPU preflight of complete retained scenes. No GPU for every endpoint, original-speed wall-clock budget, AudioTrack playback, physical device, completed lap or smooth60 proof.')
(folder/'current-native-route-report.json').write_text(json.dumps(r,indent=2));print('SAVED_ANDROID_PAIRED_ROUTE_PARITY_AND_CAPTURE_LIMITS',flush=True)
