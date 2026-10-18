"""Read-only step82 component witness, source-bound to the current preview."""
from pathlib import Path
import hashlib,json,subprocess,uuid,zipfile
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Native-Wide-20261017';folder=out/'assembly-probe-results';folder.mkdir(exist_ok=True);adb=base/'android-tools/sdk/platform-tools/adb.exe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=40):return subprocess.run([str(adb),'-s','emulator-5556']+args,check=True,capture_output=True,timeout=timeout)
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30' and run(['shell','getprop','sys.boot_completed']).stdout.strip()==b'1'
t=json.loads((out/'assembly-probe-test/apk-build-report.json').read_text());p=json.loads((out/'production/apk-build-report.json').read_text());assert t['native_capture'] and t['runner']=='NativeClassifiedGapInstrumentation'
for name,h in t['source_sha256'].items():assert sha(source/name)==h,name
for name,h in p['source_sha256'].items():
 if name.startswith('java/'):assert t['source_sha256'][name]==h,name
assert t['sha256']==sha(out/'assembly-probe-test/NFSUG-Android-Core-Preview.apk')
with zipfile.ZipFile(out/'assembly-probe-test/NFSUG-Android-Core-Preview.apk') as left,zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as right:
 for abi in ['x86_64','arm64-v8a']:
  n='lib/'+abi+'/libnfsug_android_core.so';diag=json.loads((out/'assembly-probe-native/capture-jni-build-report.json').read_text());parent=json.loads((out/'native/capture-jni-build-report.json').read_text());assert diag['diagnostic_only'];target=next(x for x in diag['targets'] if x['abi']==abi);original=next(x for x in parent['targets'] if x['abi']==abi);assert hashlib.sha256(left.read(n)).hexdigest()==target['sha256'] and hashlib.sha256(right.read(n)).hexdigest()==original['sha256']
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(q):sha(q) for q in [rom,state]};assert list(before.values())==['53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593','49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104']
ledger=out/'route-results/input-keys.json';assert len(json.loads(ledger.read_text()))==6000
print(run(['install','-r',str(out/'assembly-probe-test/NFSUG-Android-Core-Preview.apk')]).stdout.decode(),flush=True);prefix='first-gap-'+uuid.uuid4().hex[:12];(folder/'run-state.json').write_text(json.dumps(dict(prefix=prefix),indent=2))
for suffix,q in [('.gba',rom),('.state',state),('-keys.json',ledger)]:
 temporary='/data/local/tmp/'+prefix+suffix;run(['push',str(q),temporary]);run(['shell','run-as','org.codex.nfsugpreview','cp',temporary,'files/'+prefix+suffix]);run(['shell','rm',temporary])
run(['logcat','-c']);result=run(['shell','am','instrument','-w','-r','-e','fixturePrefix',prefix,'-e','steps','540','-e','witnessStep','518','-e','backgroundProbe','true','-e','rejectionProbe','true','-e','assemblyProbe','true','org.codex.nfsugpreview/.NativeClassifiedGapInstrumentation'],timeout=240);text=result.stdout.decode();(folder/'instrumentation-run.log').write_text(text);print(text,flush=True)
(folder/'instrumentation-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGFirstGap:E','AndroidRuntime:E','*:S']).stdout)
assert 'VERIFIED_ANDROID_FIRST_GAP_COMPONENT_WITNESS' in text and 'INSTRUMENTATION_CODE: -1' in text
r=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+prefix+'-report.json']).stdout);assert r['paired_original_pixels_pcm_clocks_exact'] and r['witness_step']==518 and r['native']['steps']==540
paths=run(['shell','run-as','org.codex.nfsugpreview','ls','files']).stdout.decode().splitlines();frozen={}
for name in paths:
 if name.startswith(prefix) and name.endswith('.bin'):
  data=run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]).stdout;target=name.removeprefix(prefix+'-');(folder/target).write_bytes(data);frozen[target]=hashlib.sha256(data).hexdigest()
assert before=={str(q):sha(q) for q in [rom,state]}
gold=json.loads((out/'gap518-results/first-gap-report.json').read_text());assert r['native']==gold['native'] and r['original']==gold['original']
for name in ['original_background','legacy_combined_scene','source_background_retry','retained_retry_present','owners','timing','capture_stats']:assert r['step518'][name]==gold['step518'][name],name
raw=r['step518']['capture_context']['background_probe'];assert len(raw)==64 and raw[0]==0x3147424e and raw[1]==1 and raw[2:6]==raw[52:56]==r['step518']['timing']
assert diag['visibility_capacity']==64 and diag['parent_native_report_sha256']==sha(out/'native/capture-jni-build-report.json') and not diag['logic_or_rejection_changed']
for n,h in diag['staged_diagnostic_sha256'].items():assert sha(out/'assembly-probe-native/source'/n)==h
assert diag['factory_sha256']==sha(source/'capture/build_model_assembly_probe.py')
previous=json.loads((out/'background-probe-results/background-probe-report.json').read_text());assert r['step518']['capture_context']['background_probe']==previous['step518']['capture_context']['background_probe'] and frozen==previous['frozen_component_sha256']
prior=json.loads((out/'rejection-probe-results/rejection-probe-report.json').read_text());assert r['step518']['capture_context']['packet_rejection']==prior['step518']['capture_context']['packet_rejection']
meta=r['step518']['capture_context']['packet_rejection'];assert len(meta)==153 and meta[2:6]==r['step518']['timing'] and meta[6:14]==r['step518']['capture_stats']
r.update(frozen_component_sha256=frozen,test_apk_sha256=t['sha256'],production_apk_sha256=p['sha256'],production_java_match=True,diagnostic_native_parent_verified=True,production_java_native_match=False,rom_state_unchanged_sha256=before,runner_sha256=sha(Path(__file__)),limits='Read-only capture API observation at518,540 paired original steps exact against ordinary64-entry parent witness. x86 diagnostic only; no production native identity claim. No GPU/performance/full-race proof.')
(folder/'assembly-probe-report.json').write_text(json.dumps(r,indent=2));print('SAVED_FIRST_GAP_FROZEN_COMPONENTS',flush=True)
