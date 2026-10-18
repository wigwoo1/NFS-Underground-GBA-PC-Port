"""Run existing world decoder/mesh tests on the owned emulator with C-verified fixtures."""
from pathlib import Path
import argparse,hashlib,json,subprocess,time,zipfile
p=argparse.ArgumentParser()
for name in ("adb","build","world_data","mesh_data"):p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
a=p.parse_args();reference=json.loads((a.world_data/"world-decode-report.json").read_text());mesh=json.loads((a.mesh_data/"world-mesh-report.json").read_text());assert reference["result"]=="PASS_WORLD_MATERIAL_ORDER_PARITY" and mesh["result"]=="PASS_NATIVE_WORLD_ENDPOINT_MESH_PARITY"
manifest=dict(valid_packets=reference["valid_packets"],malformed_packets=reference["malformed_packets"],surfaces=reference["surfaces"],meshes=mesh["meshes"],source_corrected_rejected=mesh["source_corrected_modes_rejected"])
archive=a.build/"world-runtime-fixtures.zip"
with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
 z.writestr("manifest.json",json.dumps(manifest))
 for folder,prefix,extensions in ((a.world_data/"fixtures","fixtures",(".nsp",)),(a.world_data/"decoded","text",(".txt",)),(a.mesh_data/"decoded","mesh",(".camera",".mesh"))):
  for f in sorted(folder.iterdir()):
   if f.is_file() and f.suffix in extensions:z.write(f,prefix+"/"+f.name)
def run(args,timeout=40):return subprocess.run([str(a.adb),"-s","emulator-5556"]+[str(x) for x in args],check=True,capture_output=True,timeout=timeout)
for _ in range(90):
 try:
  if run(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator unavailable")
assert run(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
build=json.loads((a.build/"apk-build-report.json").read_text());assert build["instrumentation"]
print(run(["install","-r",a.build/"NFSUG-Android-Core-Preview.apk"]).stdout.decode(),flush=True)
remote="/data/local/tmp/nfsug-world-runtime.zip";run(["push",archive,remote]);run(["shell","run-as","org.codex.nfsugpreview","mkdir","-p","files"])
try:run(["shell","run-as","org.codex.nfsugpreview","cp",remote,"files/world-runtime-fixtures.zip"])
finally:run(["shell","rm","-f",remote])
assert run(["exec-out","run-as","org.codex.nfsugpreview","sha256sum","files/world-runtime-fixtures.zip"]).stdout.decode().split()[0]==hashlib.sha256(archive.read_bytes()).hexdigest()
run(["logcat","-c"])
r=run(["shell","am","instrument","-w","-r","org.codex.nfsugpreview/.WorldInstrumentation"],120);text=r.stdout.decode();(a.build/"world-runtime-run.log").write_text(text,encoding="utf-8");print(text,flush=True)
(a.build/"world-runtime-logcat.log").write_bytes(run(["logcat","-d","-s","NFSUGWorldTest:E","AndroidRuntime:E","*:S"]).stdout)
assert "PASS_ANDROID_WORLD_DECODE_MESH" in text and "INSTRUMENTATION_CODE: -1" in text
report=json.loads(run(["exec-out","run-as","org.codex.nfsugpreview","cat","files/world-runtime-report.json"]).stdout);report.update(apk_sha256=build["sha256"],corpus_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),scope="Android CPU decoder/endpoint mesh parity, not world GPU rendering or full-scene gameplay.")
(a.build/"world-runtime-report.json").write_text(json.dumps(report,indent=2));print("Android world/material/order/mesh parity PASS",flush=True)
