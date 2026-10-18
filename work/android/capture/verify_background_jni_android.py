"""Normal sky/background, source geometry binding and actual Android joined snapshot checks."""
from pathlib import Path
import hashlib,json,zipfile,subprocess,struct
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');out=b/'NFSUG-background-owner-api-fixtures';app=b/'NFSUG-android-local/app-background-jni-tests';native=b/'NFSUG-android-background-jni-native-local';runtime=json.loads((app/'background-jni-android-report.json').read_text());apk=json.loads((app/'apk-build-report.json').read_text());build=json.loads((native/'capture-jni-build-report.json').read_text());host=json.loads((out/'background-owner-api-report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert host['background_snapshots']==590 and len(host['selected_backgrounds'])==9 and host['rejected_warmup']==[11848,11851]
assert runtime['result']=='PASS_ANDROID_SOURCE_BACKGROUND_JNI' and runtime['pc_identical_source_backgrounds']==9 and runtime['unowned_warmup_rejected']==2 and runtime['source_display_snapshots']==594 and runtime['wall_owners']==148 and runtime['older_owner_immutable_checks']==147
assert runtime['retained_road_cells']==100870 and runtime['retained_wall_cells']==206571 and runtime['original_rgba_frames']==600 and runtime['post_reset_original_frames']==80 and runtime['audio_frames']==443007 and runtime['original_timing']
assert sha(Path(apk['apk']))==apk['sha256']==runtime['apk_sha256']
for name,digest in apk['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
provenance=json.loads((native/'source-provenance.json').read_text())
for name,digest in provenance['unaltered_source_sha256'].items():assert sha(r/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
for name,digest in build['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/build_capture.py','/stage_capture.py')):assert sha(r/name)==digest,name
with zipfile.ZipFile(apk['apk']) as z:
 for target in build['targets']:
  assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256'];symbols=subprocess.run([str(b/'android-tools/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(native/target['library'])],check=True,capture_output=True,text=True).stdout
  for method in ('captureSkyEnableNative','captureBackgroundSceneNative'):assert 'Java_org_codex_nfsugpreview_NativeCore_'+method in symbols
for name,digest in runtime['fixtures'].items():assert sha(b/'NFSUG-background-jni-fixtures'/name)==digest
for extension in ('nwh','nrh','nrp'):
 for path in out.glob('owner-*.'+extension):assert path.read_bytes()==(b/'NFSUG-road-owner-api-fixtures'/path.name).read_bytes(),path.name
# Compare source indices/masks and full sky source assets independently of palette aliases.
def section(raw,part):
 at,size=struct.unpack_from('<2Q',raw,64+part*16);return raw[at:at+size]
covered=skyowners=0
for name in host['selected_backgrounds'].values():
 actual=(out/name).read_bytes();reference=(b/'NFSUG-wall-assets-fixtures'/name).read_bytes();count=struct.unpack_from('<Q',actual,56)[0]
 for i in range(count):
  a=section(actual,i+1);e=section(reference,i+1);assert a[:80]==e[:80] and a[38480:]==e[38480:]
  for cell,mask in enumerate(a[38480:]):
   if mask:assert a[80+cell]==e[80+cell];covered+=1
  assert section(section(actual,0),i+1)==section(section(reference,0),i+1);skyowners+=1
jdk=b/'android-tools/jdk-21.0.12.1+1/bin';classes=out/'combined-classes';test=r/'work/android/tests/org/codex/nfsugpreview/SourceBackgroundBindingTest.java';subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(r/'work/android/java'),'-d',str(classes),str(test)],check=True);text=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.SourceBackgroundBindingTest',str(out),str(b/'NFSUG-wall-assets-fixtures')],check=True,capture_output=True,text=True).stdout.strip();assert 'snapshots=9' in text and 'missing_or_forged_rejected=18' in text
for row in (b/'NFSUG-background-jni-fixtures/background-scenes.txt').read_text().splitlines():
 refresh,digest=row.split();assert sha(out/('source-'+host['selected_backgrounds'][refresh]))==digest
result=dict(result='PASS_NORMAL_SOURCE_BACKGROUND_INTEGRATION',host_background_snapshots=590,android_pc_identical_source_backgrounds=9,warmup_rejected=2,covered_source_index_checks=covered,sky_owner_assets_identical=skyowners,host_binding_test=text,original_android_frames=600,post_reset_frames=80,original_timing_audio=True,retained_road_cells=100870,retained_wall_cells=206571,source_and_fixture_apk_native_hashes_verified=True,test_apk_sha256=apk['sha256'],gpu_presented=False,full_scene_60fps=False,physical_arm64=False,source_hashes={name:sha(r/name) for name in ['work/android/capture/observer_adapter.inc','work/android/capture/core_capture_api.inc','work/android/nfsug_android_jni.c','work/android/java/org/codex/nfsugpreview/NativeCore.java','work/android/java/org/codex/nfsugpreview/NativeSourceBackgroundBinding.java','work/android/tests/org/codex/nfsugpreview/SourceBackgroundBindingTest.java','work/android/instrumentation/org/codex/nfsugpreview/BackgroundHistoryInstrumentation.java']})
(app/'background-jni-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'},indent=2))
