"""Execute same-core JNI capture checks on owned Android emulator only."""
import argparse,hashlib,json,subprocess,time,tempfile
from pathlib import Path
a=argparse.ArgumentParser()
for name in ("adb","build","capture_data","runtime","reference"):a.add_argument("--"+name.replace("_","-"),type=Path,required=True)
a.add_argument("--bundle-data",type=Path,required=True)
a=a.parse_args()
def run(args,timeout=30):return subprocess.run([str(a.adb),"-s","emulator-5556"]+args,check=True,capture_output=True,timeout=timeout)
for i in range(90):
 try:
  if run(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator not booted")
assert run(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
report=json.loads((a.build/"apk-build-report.json").read_text());assert report["native_capture"] and report["instrumentation"]
reference=json.loads(a.reference.read_text());rgba=[]
with (a.capture_data/"capture-off/frames.raw").open("rb") as frames:
 for expected in reference["original_frame_hashes"]:
  raw=bytearray(frames.read(153600));assert len(raw)==153600 and hashlib.sha256(raw).hexdigest()==expected
  raw[3::4]=b"\xff"*38400;rgba.append(hashlib.sha256(raw).hexdigest())
 assert not frames.read(1)
fixtures={
 "capture-test.gba":(a.runtime/"game.gba").read_bytes(),
 "capture-test.state":(a.runtime/"checkpoint.state").read_bytes(),
 "capture-rgba-hashes.txt":("\n".join(rgba)+"\n").encode(),
 "capture-packet-hashes.txt":("\n".join(row[2] for row in reference["packets"])+"\n").encode()}
combined=a.bundle_data
fixtures["bundle-crc-reference.tsv"]=(combined/"bundle-crc-reference.tsv").read_bytes()
for name in ("whole-rows.txt","split-rows.txt"):fixtures[name]=(combined/"bundle-android"/name).read_bytes()
print(run(["install","-r",str(a.build/"NFSUG-Android-Core-Preview.apk")]).stdout.decode(),flush=True)
run(["shell","run-as","org.codex.nfsugpreview","mkdir","-p","files"])
for name,data in fixtures.items():
 # adb exec-in can terminate early on this Windows transport; push a complete
 # temporary file first, then copy it into the test application's private files.
 remote="/data/local/tmp/nfsug-"+name
 with tempfile.TemporaryDirectory(prefix="nfsug-fixture-") as temporary:
  local=Path(temporary)/name;local.write_bytes(data)
  run(["push",str(local),remote],60)
 try:
  run(["shell","run-as","org.codex.nfsugpreview","cp",remote,"files/"+name])
 finally:
  run(["shell","rm","-f",remote])
 assert run(["exec-out","run-as","org.codex.nfsugpreview","sha256sum","files/"+name]).stdout.decode().split()[0]==hashlib.sha256(data).hexdigest()
run(["logcat","-c"])
result=run(["shell","am","instrument","-w","-r","org.codex.nfsugpreview/.BundleInstrumentation"],300)
text=result.stdout.decode();(a.build/"bundle-jni-run.log").write_text(text,encoding="utf-8");print(text,flush=True)
(a.build/"bundle-jni-logcat.log").write_bytes(run(["logcat","-d","-s","NFSUGBundleJNI:E","AndroidRuntime:E","*:S"]).stdout)
assert "PASS_ANDROID_COMBINED_SCENE_JNI" in text and "INSTRUMENTATION_CODE: -1" in text
result=json.loads(run(["exec-out","run-as","org.codex.nfsugpreview","cat","files/bundle-jni-report.json"]).stdout)
result.update(apk_sha256=report["sha256"],fixture_sha256={name:hashlib.sha256(data).hexdigest() for name,data in fixtures.items()},
 scope="Actual same-core JNI/owned combined Java snapshot checks on API30 x86_64. Original framebuffer output; no native scene rendering or real-time cadence proof.")
(a.build/"bundle-jni-report.json").write_text(json.dumps(result,indent=2))
print("JNI original-frame, native-packet and ownership checks PASS",flush=True)
