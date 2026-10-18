"""Build/sign a debug Android core-preview APK. No ROM/assets/private key bundled."""
import argparse,hashlib,json,os,subprocess,zipfile,uuid,xml.etree.ElementTree as ET
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument("--toolchain",type=Path,required=True)
a.add_argument("--native-root",type=Path,required=True)
a.add_argument("--output",type=Path,required=True)
a.add_argument("--capture-native-root",type=Path)
a.add_argument("--keystore",type=Path)
a.add_argument("--instrumentation",action="store_true")
a.add_argument("--runner",choices=("TouchInstrumentation","EmptyModelPlaneInstrumentation","RecoveredSceneGpuInstrumentation","TrafficSceneGpuInstrumentation","LiveImageReuseInstrumentation","NativeRouteInstrumentation","NativeFirstGapInstrumentation","NativeClassifiedGapInstrumentation","LifecycleInstrumentation","CaptureInstrumentation","BundleInstrumentation","ModelGpuInstrumentation","WorldInstrumentation","SceneGpuInstrumentation","IndexedSceneGpuInstrumentation","LitSceneGpuInstrumentation","RoadAttributesInstrumentation","RoadClipInstrumentation","RoadSceneGpuInstrumentation","SourceRoadInstrumentation","SourceRoadGpuInstrumentation","SplitSceneGpuInstrumentation","ObjScanlineInstrumentation","HudRulesInstrumentation","HudFrameInstrumentation","HudGpuInstrumentation","MenuTextInstrumentation","MenuTextGpuInstrumentation","MenuCaptureInstrumentation","MenuCaptureGpuInstrumentation","SkyInstrumentation","SkyGpuInstrumentation","SkySceneInstrumentation","SkySceneGpuInstrumentation","SkyCoverageInstrumentation","RaceSceneGpuInstrumentation","BackgroundSceneGpuInstrumentation","RoadEdgeGpuInstrumentation","BoundSceneGpuInstrumentation","SequenceSceneGpuInstrumentation","RetainedSequenceGpuInstrumentation","SourceWorldInstrumentation","WallHistoryInstrumentation","RoadHistoryInstrumentation","BackgroundHistoryInstrumentation","CompleteSceneGpuInstrumentation","LivePresentationInstrumentation","PreviewNativeUiInstrumentation"),default="TouchInstrumentation")
a=a.parse_args()
source=Path(__file__).resolve().parent
tool=json.loads(a.toolchain.read_text());jdk=Path(tool["jdk"]);sdk=Path(tool["sdk"])
build=sdk/"build-tools/36.0.0";android=sdk/"platforms/android-36/android.jar"
a.output.mkdir(parents=True,exist_ok=True)
build_id=uuid.uuid4().hex[:12]
classes=a.output/("classes-"+build_id);classes.mkdir()
dex=a.output/("dex-"+build_id);dex.mkdir()
stage=a.output/("source-"+build_id);stage.mkdir()
env=os.environ.copy();env["JAVA_HOME"]=str(jdk);env["PATH"]=str(jdk/"bin")+";"+env["PATH"]
logs=[]
def run(args,name):
 command=[str(x) for x in args]
 # SDK batch frontends are replaced with their actual Java jars to avoid shell quoting.
 with (a.output/(name+".log")).open("w",encoding="utf-8") as log:
  subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 logs.append(name+".log")
 print(name+" passed",flush=True)
java=jdk/"bin/java.exe"

libraries={}
if a.capture_native_root:
 native_report=json.loads((a.capture_native_root/"capture-jni-build-report.json").read_text())
 assert native_report["jni"],"Capture variant needs JNI in the same core image"
 if native_report.get("diagnostic_only"):assert a.instrumentation and a.runner=="NativeClassifiedGapInstrumentation","Diagnostic native libraries cannot be packaged as ordinary previews"
 for name,digest in native_report["native_inputs"].items():
  # Only compiled source/build inputs must remain equal; test/readme changes are independent.
  if name.endswith((".c",".h",".inc","CMakeLists.txt","/stage_capture.py","/build_capture.py")):
   assert hashlib.sha256((source.parents[1]/name).read_bytes()).hexdigest()==digest,"Stale native input: "+name
 for target in native_report["targets"]:
  file=a.capture_native_root/target["library"]
  assert hashlib.sha256(file.read_bytes()).hexdigest()==target["sha256"]
  libraries[target["abi"]]=file
else:
 native_report=json.loads((a.native_root/"android-build-report.json").read_text(encoding="utf-8-sig"))
 assert native_report.get("jni_built"),"Build native libraries with -Jni first"
 for item in native_report["project_inputs"]:
  assert hashlib.sha256((source/item["name"]).read_bytes()).hexdigest()==item["sha256"].lower(),"Stale native source: "+item["name"]
 for target in native_report["targets"]:
  library=a.native_root/("build-"+target["abi"])/"libnfsug_android_core.so"
  assert hashlib.sha256(library.read_bytes()).hexdigest()==target["sha256"].lower(),"Stale native library"

 for target in native_report["targets"]:libraries[target["abi"]]=a.native_root/("build-"+target["abi"])/"libnfsug_android_core.so"
sources=sorted((source/"java").rglob("*.java"))
if a.instrumentation:
 sources+=sorted((source/"instrumentation").rglob("*.java"))
 sources+=sorted((source/"tests/org/codex/nfsugpreview").glob("World*Test.java"))
 sources.append(source/"tests/org/codex/nfsugpreview/SourceRoadProjectionTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/ObjScanlineTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/HudRulesTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/HudCandidatesTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/HudFrameTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/MenuTextTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/SkyTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/SkyPlanesTest.java")
 sources.append(source/"tests/org/codex/nfsugpreview/SkySceneTest.java")
source_bytes={p.relative_to(source).as_posix():p.read_bytes() for p in sources+[source/"AndroidManifest.xml",source/"build_android_apk.py"]}
for name,data in source_bytes.items():
 dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
manifest=stage/"AndroidManifest.xml"
if a.instrumentation:
 ET.register_namespace("android","http://schemas.android.com/apk/res/android")
 tree=ET.parse(manifest);tag="{http://schemas.android.com/apk/res/android}"
 for runner in ("TouchInstrumentation","EmptyModelPlaneInstrumentation","RecoveredSceneGpuInstrumentation","TrafficSceneGpuInstrumentation","LiveImageReuseInstrumentation","NativeRouteInstrumentation","NativeFirstGapInstrumentation","NativeClassifiedGapInstrumentation","LifecycleInstrumentation","CaptureInstrumentation","BundleInstrumentation","ModelGpuInstrumentation","WorldInstrumentation","SceneGpuInstrumentation","IndexedSceneGpuInstrumentation","LitSceneGpuInstrumentation","RoadAttributesInstrumentation","RoadClipInstrumentation","RoadSceneGpuInstrumentation","SourceRoadInstrumentation","SourceRoadGpuInstrumentation","SplitSceneGpuInstrumentation","ObjScanlineInstrumentation","HudRulesInstrumentation","HudFrameInstrumentation","HudGpuInstrumentation","MenuTextInstrumentation","MenuTextGpuInstrumentation","MenuCaptureInstrumentation","MenuCaptureGpuInstrumentation","SkyInstrumentation","SkyGpuInstrumentation","SkySceneInstrumentation","SkySceneGpuInstrumentation","SkyCoverageInstrumentation","RaceSceneGpuInstrumentation","BackgroundSceneGpuInstrumentation","RoadEdgeGpuInstrumentation","BoundSceneGpuInstrumentation","SequenceSceneGpuInstrumentation","RetainedSequenceGpuInstrumentation","SourceWorldInstrumentation","WallHistoryInstrumentation","RoadHistoryInstrumentation","BackgroundHistoryInstrumentation","CompleteSceneGpuInstrumentation","LivePresentationInstrumentation","PreviewNativeUiInstrumentation"):
  ET.SubElement(tree.getroot(),"instrumentation",{tag+"name":"org.codex.nfsugpreview."+runner,tag+"targetPackage":"org.codex.nfsugpreview",tag+"functionalTest":"true"})
 ET.SubElement(tree.getroot().find("application"),"activity",{tag+"name":"org.codex.nfsugpreview.LiveTestActivity",tag+"exported":"false",tag+"screenOrientation":"landscape"})
 ET.SubElement(tree.getroot().find("application"),"activity",{tag+"name":"org.codex.nfsugpreview.FixturePreviewActivity",tag+"exported":"true",tag+"screenOrientation":"landscape"})
 tree.write(manifest,encoding="utf-8",xml_declaration=True)
run([build/"aapt2.exe","link","-o",a.output/"resources.apk","-I",android,"--manifest",manifest],"resources")
staged_sources=[stage/p.relative_to(source) for p in sources]
generated=stage/"java/org/codex/nfsugpreview/PreviewBuild.java"
generated.write_text("package org.codex.nfsugpreview; final class PreviewBuild { static final boolean NATIVE_CAPTURE="+("true" if a.capture_native_root else "false")+"; }",encoding="utf-8")
staged_sources.append(generated)
run([jdk/"bin/javac.exe","--release","8","-encoding","UTF-8","-classpath",android,"-d",classes]+staged_sources,"javac")
run([jdk/"bin/jar.exe","cf",a.output/"classes.jar","-C",classes,"."],"classes-jar")
run([java,"-cp",build/"lib/d8.jar","com.android.tools.r8.D8","--min-api","26","--lib",android,"--output",dex,a.output/"classes.jar"],"dex")
unsigned=a.output/"unsigned.apk"
with zipfile.ZipFile(a.output/"resources.apk") as src,zipfile.ZipFile(unsigned,"w",zipfile.ZIP_DEFLATED) as dest:
 for info in src.infolist():dest.writestr(info,src.read(info.filename))
 dest.write(dex/"classes.dex","classes.dex")
 for abi in ("arm64-v8a","x86_64"):
  dest.write(libraries[abi],"lib/"+abi+"/libnfsug_android_core.so")
run([build/"zipalign.exe","-f","-P","16","4",unsigned,a.output/"aligned.apk"],"align")
key=a.keystore if a.keystore else a.output/"preview-debug.p12"
if not key.exists():
 run([jdk/"bin/keytool.exe","-genkeypair","-keystore",key,"-storetype","PKCS12","-storepass","android",
  "-keypass","android","-alias","preview","-keyalg","RSA","-keysize","2048","-validity","3650",
  "-dname","CN=NFSUG Local Debug Preview,O=Local Development,C=US"],"debug-key")
apk=a.output/"NFSUG-Android-Core-Preview.apk"
run([java,"-jar",build/"lib/apksigner.jar","sign","--ks",key,"--ks-key-alias","preview","--ks-pass","pass:android",
 "--key-pass","pass:android","--out",apk,a.output/"aligned.apk"],"sign")
run([java,"-jar",build/"lib/apksigner.jar","verify","--verbose","--print-certs",apk],"signature-verify")
run([build/"zipalign.exe","-c","-P","16","4",apk],"alignment-verify")
run([build/"aapt2.exe","dump","badging",apk],"package-inspect")
with zipfile.ZipFile(apk) as z:
 names=z.namelist()
 assert "classes.dex" in names and "AndroidManifest.xml" in names
 assert all(not n.lower().endswith((".gba",".state",".sav",".p12",".jks")) for n in names)
 report={"result":"PASS_SIGNED_APK_BUILD","apk":str(apk),"bytes":apk.stat().st_size,"sha256":hashlib.sha256(apk.read_bytes()).hexdigest(),
 "native_capture":bool(a.capture_native_root),"generated_build_config_sha256":hashlib.sha256(generated.read_bytes()).hexdigest(),"instrumentation":a.instrumentation,"runner":a.runner if a.instrumentation else None,"staged_input_hash":hashlib.sha256(manifest.read_bytes()).hexdigest(),"zip_entries":names,"rom_bundled":False,"private_key_bundled":False,"android_runtime_verified":False,"native_scene_renderer":False,
 "scope":"Original-core preview app cross-build/signature/package inspection only; runtime/device tests outstanding",
 "source_sha256":{name:hashlib.sha256(data).hexdigest() for name,data in source_bytes.items()}}
(a.output/"apk-build-report.json").write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ("zip_entries","source_sha256")},indent=2))
