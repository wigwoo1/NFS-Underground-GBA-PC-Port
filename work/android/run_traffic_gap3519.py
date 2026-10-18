"""Read-only step518 witness on ordinary64-entry Android libraries,540 paired steps."""
from pathlib import Path
import hashlib,json,subprocess,uuid,zipfile
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Traffic-20261017';folder=out/'gap3519-results';folder.mkdir(exist_ok=True);adb=base/'android-tools/sdk/platform-tools/adb.exe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=40):return subprocess.run([str(adb),'-s','emulator-5556']+args,check=True,capture_output=True,timeout=timeout)
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30' and run(['shell','getprop','sys.boot_completed']).stdout.strip()==b'1'
t=json.loads((out/'gap3519-test/apk-build-report.json').read_text());p=json.loads((out/'production/apk-build-report.json').read_text());assert t['native_capture'] and t['runner']=='NativeFirstGapInstrumentation'
for name,h in t['source_sha256'].items():assert sha(source/name)==h,name
for name,h in p['source_sha256'].items():
 if name.startswith('java/'):assert t['source_sha256'][name]==h,name
assert t['sha256']==sha(out/'gap3519-test/NFSUG-Android-Core-Preview.apk')
with zipfile.ZipFile(out/'gap3519-test/NFSUG-Android-Core-Preview.apk') as left,zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as right:
 for abi in ['x86_64','arm64-v8a']:
  n='lib/'+abi+'/libnfsug_android_core.so';assert left.read(n)==right.read(n)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(q):sha(q) for q in [rom,state]};assert list(before.values())==['53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593','49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104']
ledger=base/'NFSUG-Android-Context-Refresh-20261017/route-results/input-keys.json';assert len(json.loads(ledger.read_text()))==6000
print(run(['install','-r',str(out/'gap3519-test/NFSUG-Android-Core-Preview.apk')]).stdout.decode(),flush=True);prefix='first-gap-'+uuid.uuid4().hex[:12];(folder/'run-state.json').write_text(json.dumps(dict(prefix=prefix),indent=2))
for suffix,q in [('.gba',rom),('.state',state),('-keys.json',ledger)]:
 temporary='/data/local/tmp/'+prefix+suffix;run(['push',str(q),temporary]);run(['shell','run-as','org.codex.nfsugpreview','cp',temporary,'files/'+prefix+suffix]);run(['shell','rm',temporary])
run(['logcat','-c']);result=run(['shell','am','instrument','-w','-r','-e','fixturePrefix',prefix,'-e','steps','3540','-e','witnessStep','3519','-e','expectGap','false','-e','progress','true','org.codex.nfsugpreview/.NativeFirstGapInstrumentation'],timeout=900);text=result.stdout.decode();(folder/'instrumentation-run.log').write_text(text);print(text,flush=True)
(folder/'instrumentation-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGFirstGap:E','AndroidRuntime:E','*:S']).stdout)
assert 'VERIFIED_ANDROID_FIRST_GAP_COMPONENT_WITNESS' in text and 'INSTRUMENTATION_CODE: -1' in text
r=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+prefix+'-report.json']).stdout);assert r['paired_original_pixels_pcm_clocks_exact'] and r['witness_step']==3519 and r['original']['steps']==r['native']['steps']==3540 and r['native']['missing_steps']==list(range(1,11))
paths=run(['shell','run-as','org.codex.nfsugpreview','ls','files']).stdout.decode().splitlines();frozen={}
for name in paths:
 if name.startswith(prefix) and name.endswith('.bin'):
  data=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]).stdout;target=name.removeprefix(prefix+'-');(folder/target).write_bytes(data);frozen[target]=hashlib.sha256(data).hexdigest()
assert before=={str(q):sha(q) for q in [rom,state]}
assert r['step3519']['original_background']['present'] and r['step3519']['source_background_retry']['present'] and r['step3519']['retained_retry_present']
gold=json.loads((base/'NFSUG-Android-Context-Refresh-20261017/gap3519-results/first-gap-report.json').read_text());assert r['original']==gold['original']
native=json.loads((out/'native/capture-jni-build-report.json').read_text());assert native['visibility_capacity']==64 and not native.get('diagnostic_only',False)
r.update(visibility_capacity=64,frozen_component_sha256=frozen,test_apk_sha256=t['sha256'],production_apk_sha256=p['sha256'],production_java_native_match=True,rom_state_unchanged_sha256=before,runner_sha256=sha(Path(__file__)),limits='Integrated traffic capture recovery at3519,3540 paired original steps with initial1–10 only missing; actual retained world/road/wall/proof required. No GPU/performance proof. No GPU/performance/full-race proof.')
(folder/'first-gap-report.json').write_text(json.dumps(r,indent=2));print('SAVED_FIRST_GAP_FROZEN_COMPONENTS',flush=True)
