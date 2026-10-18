"""Run injected-touch instrumentation only on the owned NFSUG emulator."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument("--adb",type=Path,required=True)
a.add_argument("--test-build",type=Path,required=True)
a.add_argument("--production","--published",dest="published",type=Path,required=True)
a.add_argument("--output",type=Path,required=True)
a=a.parse_args()
a.output.mkdir(parents=True,exist_ok=True)
def run(args,timeout=40):
 return subprocess.run([str(a.adb),"-s","emulator-5556"]+args,check=True,capture_output=True,timeout=timeout)
name=run(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()
assert name=="NFSUG_API30","Refusing to replace a package on a different emulator"
assert run(["shell","getprop","sys.boot_completed"]).stdout.strip()==b"1","Owned emulator is not booted"
test=json.loads((a.test_build/"apk-build-report.json").read_text())
published=json.loads((a.published/"apk-build-report.json").read_text())
assert test["instrumentation"] is True
assert test.get("native_capture",False)==published.get("native_capture",False)
assert test.get("generated_build_config_sha256")==published.get("generated_build_config_sha256")
matched={name:value for name,value in published["source_sha256"].items() if name.startswith("java/")}
assert len(matched)>=7
assert all(test["source_sha256"].get(name)==value for name,value in matched.items()),"Production Java differs from reference APK"
libraries={}
with zipfile.ZipFile(a.test_build/"NFSUG-Android-Core-Preview.apk") as tested,zipfile.ZipFile(a.published/"NFSUG-Android-Core-Preview.apk") as old:
 for abi in ("arm64-v8a","x86_64"):
  name="lib/"+abi+"/libnfsug_android_core.so"
  left=hashlib.sha256(tested.read(name)).hexdigest();right=hashlib.sha256(old.read(name)).hexdigest()
  assert left==right,"Production JNI library differs from reference APK"
  libraries[abi]=left
print(run(["install","-r",str(a.test_build/"NFSUG-Android-Core-Preview.apk")]).stdout.decode(),flush=True)
run(["logcat","-c"])
result=run(["shell","am","instrument","-w","-r","org.codex.nfsugpreview/.TouchInstrumentation"],timeout=60)
text=result.stdout.decode();(a.output/"instrumentation-run.log").write_text(text,encoding="utf-8");print(text,flush=True)
log=run(["logcat","-d","-s","NFSUGTouchTest:E","AndroidRuntime:E","NFSUGPreview:I","*:S"]).stdout
(a.output/"instrumentation-logcat.log").write_bytes(log)
assert "PASS_ANDROID_INJECTED_TOUCH" in text and "INSTRUMENTATION_CODE: -1" in text,"Android instrumentation failed"
report=json.loads(run(["exec-out","run-as","org.codex.nfsugpreview","cat","files/touch-instrumentation-report.json"]).stdout)
assert report["result"]=="PASS_ANDROID_INJECTED_TOUCH"
report.update(test_apk_sha256=hashlib.sha256((a.test_build/"NFSUG-Android-Core-Preview.apk").read_bytes()).hexdigest(),
 reference_production_apk_sha256=hashlib.sha256((a.published/"NFSUG-Android-Core-Preview.apk").read_bytes()).hexdigest(),
 matching_production_java=matched,matching_native_libraries=libraries,
 scope="Injected Android MotionEvents and actual Home/resume on an isolated API30 emulator. Matching reference production sources/native libraries; test instrumentation APK is separate. Not physical touch/device or complete-race proof.")
(a.output/"touch-verification-summary.json").write_text(json.dumps(report,indent=2))
print("PASS: Android injected-touch checks with matching reference production inputs",flush=True)
