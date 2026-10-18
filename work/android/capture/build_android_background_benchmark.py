from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');base=Path('C:/NFSUG-Workspace');local=Path(__file__).resolve().parent
out=base/'NFSUG-Android-Fixed-Background-Benchmark-20261017';out.mkdir(exist_ok=True)
android=root/'work/android';source=local/'AndroidBackgroundReuseBenchmark.java';saved=android/'capture'/source.name
if source.resolve()!=saved.resolve():shutil.copyfile(source,saved)
tool=json.loads((base/'android-tools/android-app-toolchain.json').read_text());jdk=Path(tool['jdk']);sdk=Path(tool['sdk']);platform=sdk/'platforms/android-36/android.jar';build=sdk/'build-tools/36.0.0'
classes=out/'classes';classes.mkdir(exist_ok=True);dex=out/'dex';dex.mkdir(exist_ok=True)
def run(args,name):
    result=subprocess.run([str(x) for x in args],capture_output=True,text=True,timeout=90);(out/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8');result.check_returncode()
run([jdk/'bin/javac.exe','--release','8','-sourcepath',android/'java','-d',classes,saved],'javac')
run([jdk/'bin/jar.exe','cf',out/'classes.jar','-C',classes,'.'],'jar')
run([jdk/'bin/java.exe','-cp',build/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',platform,'--output',dex,out/'classes.jar'],'dex')
with zipfile.ZipFile(out/'benchmark.jar','w',zipfile.ZIP_DEFLATED) as archive:archive.write(dex/'classes.dex','classes.dex')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources={}
for path in classes.rglob('*.class'):
    name=path.name.split('$')[0].split('.')[0]+'.java';p=saved if name==saved.name else android/'java/org/codex/nfsugpreview'/name;sources[str(p)]=sha(p)
report=dict(result='PASS_ANDROID_FIXED_SCENE_BENCHMARK_BUILD',jar_sha256=sha(out/'benchmark.jar'),source_sha256=sources,rom_bundled=False,private_key_bundled=False,runtime_verified=False)
(out/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
