from pathlib import Path
import hashlib,json,zipfile,subprocess,struct,argparse
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');parser=argparse.ArgumentParser();parser.add_argument('--app',type=Path);args=parser.parse_args()
b=Path(r'C:\NFSUG-Workspace');app=args.app or b/'NFSUG-android-local/app-complete-scene-gpu-tests';native=b/'NFSUG-android-background-jni-native-local'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((app/'apk-build-report.json').read_text());v=json.loads((app/'complete-scene-gpu-android-report.json').read_text());n=json.loads((native/'capture-jni-build-report.json').read_text())
assert v['result']=='PASS_ANDROID_COMPLETE_RETAINED_GPU' and sha(Path(a['apk']))==a['sha256']==v['apk_sha256']
for name,digest in a['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
p=json.loads((native/'source-provenance.json').read_text())
for name,digest in p['unaltered_source_sha256'].items():assert sha(r/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
for name,digest in n['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/build_capture.py','/stage_capture.py')):assert sha(r/name)==digest,name
with zipfile.ZipFile(a['apk']) as z:
 for target in n['targets']:assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
assert len(v['fixtures'])==52
for name,digest in v['fixtures'].items():assert sha(b/'NFSUG-complete-scene-gpu-fixtures'/name)==digest,name
for key,value in dict(original_rgba_frames=600,post_reset_original_frames=80,audio_frames=443007,native_gpu_frames=9,four_k_frames=3,coverage_checks=384000,coverage_holes=0,composition_pixel_checks=1161600,retained_road_color_checks=220586,retained_wall_color_checks=467714).items():assert v[key]==value,key
assert v['original_timing'] and v['context_recreated'] and v['render_thread_handoff_after_core_close'] and not v['real_time_pacing']
images={}
for name,size in [('complete-scene-native.png',(240,160)),('complete-scene-4k.png',(3840,2160))]:
 raw=(app/name).read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II',raw,16)==size;images[name]=dict(size=size,sha256=sha(app/name))
jdk=b/'android-tools/jdk-21.0.12.1+1/bin';out=b/'NFSUG-background-owner-api-fixtures';classes=out/'complete-scene-classes';test=r/'work/android/tests/org/codex/nfsugpreview/RetainedSceneTest.java'
subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(r/'work/android/java'),'-d',str(classes),str(test)],check=True)
host=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.RetainedSceneTest',str(out)],check=True,capture_output=True,text=True).stdout.strip();assert 'PASS_RETAINED_SCENE' in host
result=dict(result='PASS_COMPLETE_RETAINED_GPU_INTEGRATION',host_test=host,source_apk_native_fixture_hashes_verified=True,images=images,android_result=v['result'],native_gpu_frames=9,four_k_frames=3,coverage_holes=0,live_play=False,full_scene_60fps=False,physical_arm64=False)
baseline=b/'NFSUG-android-local/app-complete-scene-gpu-tests'
if app!=baseline:
 old=json.loads((baseline/'complete-scene-gpu-integration-report.json').read_text())
 for name,metadata in images.items():assert metadata['sha256']==old['images'][name]['sha256'] and sha(baseline/name)==metadata['sha256'],name
 result['baseline_native_and_4k_images_byte_identical']=True
(app/'complete-scene-gpu-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
