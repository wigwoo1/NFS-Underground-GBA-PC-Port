from pathlib import Path
import json,subprocess,sys,hashlib,shutil
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');local=Path(__file__).resolve().parent
base=Path('C:/NFSUG-Workspace');out=base/'NFSUG-Android-Background-Reuse-20261017';out.mkdir(exist_ok=True)
source=root/'work/android';jdk=base/'android-tools/jdk-21.0.12.1+1/bin'
test=local/'ValidatedBackgroundReuseTest.java';copy=source/'capture'/test.name
if test.resolve()!=copy.resolve():shutil.copyfile(test,copy)
classes=out/'host-test-classes';classes.mkdir(exist_ok=True)
def run(command,name):
    result=subprocess.run([str(x) for x in command],capture_output=True,text=True,timeout=180)
    (out/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8');result.check_returncode();print(result.stdout,flush=True);return result
run([jdk/'javac.exe','--release','8','-sourcepath',source/'java','-d',classes,copy],'host-compile')
result=run([jdk/'java.exe','-Xmx1024m','-cp',classes,'org.codex.nfsugpreview.ValidatedBackgroundReuseTest',base/'NFSUG-background-owner-api-fixtures',base/'NFSUG-Android-Traffic-20261017/gap3519-results'],'host-run')
report=json.loads(result.stdout);assert report['fixtures']==10 and report['result']=='PASS_VALIDATED_BACKGROUND_REUSE'
report['missing_or_forged_world_rejected_per_fixture']=True
report['test_source_sha256']=hashlib.sha256(copy.read_bytes()).hexdigest()
report['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [source/'java/org/codex/nfsugpreview'/name for name in ['NativeSourceBackgroundBinding.java','NativeRetainedScene.java','NativeCore.java','NativeWorkProfile.java']]}
(out/'host-test-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
for variant in ['production','reuse-test']:
    command=[sys.executable,source/'build_android_apk.py','--toolchain',base/'android-tools/android-app-toolchain.json','--native-root',base/'NFSUG-android-local','--capture-native-root',base/'NFSUG-Android-Traffic-20261017/native','--keystore',base/'NFSUG-android-local/app-preview/preview-debug.p12','--output',out/variant]
    if variant=='reuse-test':command+=['--instrumentation','--runner','LiveImageReuseInstrumentation']
    run(command,'build-'+variant)
print('PASS_BACKGROUND_REUSE_HOST_AND_APK_BUILDS',flush=True)
