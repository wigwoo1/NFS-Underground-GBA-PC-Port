"""Execute shared scene component diagnostics on the owned Android emulator."""
import argparse,hashlib,json,subprocess,time
from pathlib import Path
a=argparse.ArgumentParser();a.add_argument("--adb",type=Path,required=True);a.add_argument("--root",type=Path,required=True);a=a.parse_args()
def run(args,timeout=12):return subprocess.run([str(a.adb),"-s","emulator-5556"]+args,check=True,capture_output=True,timeout=timeout)
for i in range(90):
 try:
  if run(["shell","getprop","sys.boot_completed"]).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator boot was not observed")
assert run(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
remote="/data/local/tmp/nfsug_scene_checks"
run(["shell","mkdir","-p",remote])
library=a.root/"build-x86_64/libnfsug_android_scene.so";binary=a.root/"scene-check-x86_64"
for f in (library,binary):run(["push",str(f),remote+"/"+f.name])
fixtures=json.loads((a.root/"fixtures/manifest.json").read_text())
for row in fixtures:
 f=a.root/"fixtures"/row["name"];assert hashlib.sha256(f.read_bytes()).hexdigest()==row["sha256"]
 run(["push",str(f),remote+"/"+f.name])
 actual=run(["shell","sha256sum",remote+"/"+f.name]).stdout.decode().split()[0]
 assert actual==row["sha256"],row["name"]
run(["shell","chmod","755",remote+"/"+binary.name])
result=run(["shell","env","LD_LIBRARY_PATH="+remote,remote+"/"+binary.name]+[remote+"/"+r["name"] for r in fixtures],timeout=30)
text=result.stdout.decode();(a.root/"scene-android-output.log").write_text(text,encoding="utf-8")
report=json.loads(text);assert report["result"]=="PASS_ANDROID_NATIVE_SCENE_OWNERSHIP"
report.update(api=run(["shell","getprop","ro.build.version.sdk"]).stdout.decode().strip(),
 abi=run(["shell","getprop","ro.product.cpu.abi"]).stdout.decode().strip(),
 library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
 executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
 verified_fixture_sha256=fixtures,physical_device=False,
 scope="Actual Android native-library execution on API30 x86_64 emulator with real captured packet data. Not JNI/live producer integration, rendered scenes or gameplay.")
(a.root/"scene-android-tests.json").write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!="verified_fixture_sha256"},indent=2),flush=True)
