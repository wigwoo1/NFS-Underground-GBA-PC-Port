"""Run offscreen GPU diagnostic only on owned NFSUG AVD; no ROM required."""
import argparse,hashlib,json,subprocess,tempfile,time
from pathlib import Path
p=argparse.ArgumentParser()
for name in ("adb","build","sample"):p.add_argument("--"+name,type=Path,required=True)
p.add_argument("--synthetic-fixture",action="store_true")
a=p.parse_args()
def run(args,timeout=40):return subprocess.run([str(a.adb),"-s","emulator-5556"]+[str(x) for x in args],check=True,capture_output=True,timeout=timeout)
for _ in range(90):
 try:
  if run(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator not booted")
assert run(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
report=json.loads((a.build/"apk-build-report.json").read_text());assert report["instrumentation"]
print(run(["install","-r",a.build/"NFSUG-Android-Core-Preview.apk"]).stdout.decode(),flush=True)
remote="/data/local/tmp/nfsug-indexed-scene-whole.nab";data=a.sample.read_bytes();run(["push",a.sample,remote]);run(["shell","run-as","org.codex.nfsugpreview","mkdir","-p","files"])
try:run(["shell","run-as","org.codex.nfsugpreview","cp",remote,"files/indexed-scene-whole.nab"])
finally:run(["shell","rm","-f",remote])
assert run(["exec-out","run-as","org.codex.nfsugpreview","sha256sum","files/indexed-scene-whole.nab"]).stdout.decode().split()[0]==hashlib.sha256(data).hexdigest()
run(["logcat","-c"])
result=run(["shell","am","instrument","-w","-r","org.codex.nfsugpreview/.IndexedSceneGpuInstrumentation"],180)
text=result.stdout.decode();(a.build/"indexed-scene-run.log").write_text(text,encoding="utf-8");print(text,flush=True)
(a.build/"indexed-scene-logcat.log").write_bytes(run(["logcat","-d","-s","NFSUGSceneGPU:E","AndroidRuntime:E","*:S"]).stdout)
assert "PASS_ANDROID_INDEXED_SCENE_GLES" in text and "INSTRUMENTATION_CODE: -1" in text
r=json.loads(run(["exec-out","run-as","org.codex.nfsugpreview","cat","files/indexed-scene-report.json"]).stdout);r.update(synthetic_fixture=a.synthetic_fixture,apk_sha256=report["sha256"],fixture_sha256=hashlib.sha256(data).hexdigest(),scope="Ordered unlit scene offscreen GPU diagnostic, not full-scene/playable native rendering or real-time cadence.")
(a.build/"indexed-scene-report.json").write_text(json.dumps(r,indent=2))
for name in ("indexed-scene-240.png","indexed-scene-4k.png"):(a.build/name).write_bytes(run(["exec-out","run-as","org.codex.nfsugpreview","cat","files/"+name]).stdout)
print("Android ordered-scene diagnostic GPU/source-pixel/context checks PASS",flush=True)
