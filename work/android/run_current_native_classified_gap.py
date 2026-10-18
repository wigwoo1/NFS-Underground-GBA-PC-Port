"""Read-only step82 component witness, source-bound to the current preview."""
from pathlib import Path
import hashlib,json,subprocess,uuid,zipfile
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Native-Current-20261017';folder=out/'classified-gap-results';folder.mkdir(exist_ok=True);adb=base/'android-tools/sdk/platform-tools/adb.exe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=40):return subprocess.run([str(adb),'-s','emulator-5556']+args,check=True,capture_output=True,timeout=timeout)
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30' and run(['shell','getprop','sys.boot_completed']).stdout.strip()==b'1'
t=json.loads((out/'classified-gap-test/apk-build-report.json').read_text());p=json.loads((out/'production/apk-build-report.json').read_text());assert t['native_capture'] and t['runner']=='NativeClassifiedGapInstrumentation'
for name,h in t['source_sha256'].items():assert sha(source/name)==h,name
for name,h in p['source_sha256'].items():
 if name.startswith('java/'):assert t['source_sha256'][name]==h,name
assert t['sha256']==sha(out/'classified-gap-test/NFSUG-Android-Core-Preview.apk')
with zipfile.ZipFile(out/'classified-gap-test/NFSUG-Android-Core-Preview.apk') as left,zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as right:
 for abi in ['x86_64','arm64-v8a']:
  n='lib/'+abi+'/libnfsug_android_core.so';diag=json.loads((out/'classified-native/capture-jni-build-report.json').read_text());parent=json.loads((out/'native/capture-jni-build-report.json').read_text());assert diag['diagnostic_only'];target=next(x for x in diag['targets'] if x['abi']==abi);original=next(x for x in parent['targets'] if x['abi']==abi);assert hashlib.sha256(left.read(n)).hexdigest()==target['sha256'] and hashlib.sha256(right.read(n)).hexdigest()==original['sha256']
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(q):sha(q) for q in [rom,state]};assert list(before.values())==['53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593','49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104']
ledger=out/'route-results/input-keys.json';assert len(json.loads(ledger.read_text()))==6000
print(run(['install','-r',str(out/'classified-gap-test/NFSUG-Android-Core-Preview.apk')]).stdout.decode(),flush=True);prefix='first-gap-'+uuid.uuid4().hex[:12];(folder/'run-state.json').write_text(json.dumps(dict(prefix=prefix),indent=2))
for suffix,q in [('.gba',rom),('.state',state),('-keys.json',ledger)]:
 temporary='/data/local/tmp/'+prefix+suffix;run(['push',str(q),temporary]);run(['shell','run-as','org.codex.nfsugpreview','cp',temporary,'files/'+prefix+suffix]);run(['shell','rm',temporary])
run(['logcat','-c']);result=run(['shell','am','instrument','-w','-r','-e','fixturePrefix',prefix,'org.codex.nfsugpreview/.NativeClassifiedGapInstrumentation'],timeout=120);text=result.stdout.decode();(folder/'instrumentation-run.log').write_text(text);print(text,flush=True)
(folder/'instrumentation-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGFirstGap:E','AndroidRuntime:E','*:S']).stdout)
assert 'VERIFIED_ANDROID_FIRST_GAP_COMPONENT_WITNESS' in text and 'INSTRUMENTATION_CODE: -1' in text
r=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+prefix+'-report.json']).stdout);assert r['paired_original_pixels_pcm_clocks_exact'] and 82 in r['native']['missing_steps']
paths=run(['shell','run-as','org.codex.nfsugpreview','ls','files']).stdout.decode().splitlines();frozen={}
for name in paths:
 if name.startswith(prefix) and name.endswith('.bin'):
  data=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]).stdout;target=name.removeprefix(prefix+'-');(folder/target).write_bytes(data);frozen[target]=hashlib.sha256(data).hexdigest()
assert before=={str(q):sha(q) for q in [rom,state]}
gold=json.loads((out/'first-gap-results/first-gap-report.json').read_text());assert frozen==gold['frozen_component_sha256'] and r['native']==gold['native'] and r['original']==gold['original']
assert r['step82']['owners'][0]['classifier'][0:2]==[1,0] and r['step82']['owners'][1]['classifier'][0]==0 and r['step82']['owners'][1]['classifier'][1] in [1,3,4,5]
for n,h in diag['staged_diagnostic_sha256'].items():assert sha(out/'classified-native/source'/n)==h
assert diag['factory_sha256']==sha(source/'capture/build_first_gap_classifier.py')
r.update(frozen_component_sha256=frozen,test_apk_sha256=t['sha256'],production_apk_sha256=p['sha256'],production_java_match=True,diagnostic_native_parent_verified=True,production_java_native_match=False,rom_state_unchanged_sha256=before,runner_sha256=sha(Path(__file__)),limits='Readout starts only after reproduced step82 null retained scene. Extra capture queries occur afterward;100-step paired original pixels/PCM/clocks remain equal. No GPU/performance/full-race proof.')
(folder/'classified-gap-report.json').write_text(json.dumps(r,indent=2));print('SAVED_FIRST_GAP_FROZEN_COMPONENTS',flush=True)
