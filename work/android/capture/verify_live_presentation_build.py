from pathlib import Path
import json,hashlib,subprocess,zipfile
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');out=b/'NFSUG-live-presentation-host';app=b/'NFSUG-android-local/app-live-native-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((app/'apk-build-report.json').read_text());assert a['result']=='PASS_SIGNED_APK_BUILD' and sha(Path(a['apk']))==a['sha256']
for name,digest in a['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
n=json.loads((b/'NFSUG-android-background-jni-native-local/capture-jni-build-report.json').read_text())
with zipfile.ZipFile(a['apk']) as z:
 for target in n['targets']:assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
jdk=b/'android-tools/jdk-21.0.12.1+1/bin';results=[]
for name,expected,args in [('NativePresentationTest','PASS_NATIVE_PRESENTATION',[]),('NativePresentationSceneTest','PASS_PRESENTATION_SCENES',[str(b/'NFSUG-background-owner-api-fixtures')])]:
 source=r/('work/android/tests/org/codex/nfsugpreview/'+name+'.java')
 subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(r/'work/android/java'),'-d',str(out/'classes'),str(source)],check=True)
 text=subprocess.run([str(jdk/'java.exe'),'-Xmx192m','-cp',str(out/'classes'),'org.codex.nfsugpreview.'+name,*args],check=True,capture_output=True,text=True).stdout.strip();assert expected in text;results.append(text)
result=dict(result='PASS_LIVE_PRESENTATION_BUILD_AND_HOST',tests=results,apk_sha256=a['sha256'],source_apk_native_hashes_verified=True,android_live_runtime_verified=False,full_scene_60fps=False,published=False,scope='Opt-in GameSession/FrameView source integration compiled; bounded mailbox and exact scene identity host verified. New FBO/blit/live lifecycle require Android runtime test.')
(app/'live-presentation-build-host-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
