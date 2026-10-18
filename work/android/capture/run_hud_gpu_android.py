"""Run offscreen GPU diagnostic only on owned NFSUG AVD; no ROM required."""
import argparse,hashlib,json,subprocess,tempfile,time
from pathlib import Path
p=argparse.ArgumentParser()
for name in ("adb","build","sample"):p.add_argument("--"+name,type=Path,required=True)
p.add_argument("--synthetic-fixture",action="store_true")
p.add_argument("--host-report",type=Path,required=True)
a=p.parse_args()
host=json.loads(a.host_report.read_text());build=json.loads((a.build/'apk-build-report.json').read_text());assert host['result']=='PASS_HISTORICAL_HUD_FRAME_C_PARITY'
for name,digest in host['source_sha256'].items():assert build['source_sha256'][name.replace('\\','/')]==digest,'Stale C-verified HUD source '+name
assert hashlib.sha256(a.sample.read_bytes()).hexdigest() in [v['snapshot_sha256'] for v in host['fixtures'].values()],'Snapshot lacks exact C frame reference'

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
remote="/data/local/tmp/nfsug-hud-gpu-scene.nab";data=a.sample.read_bytes();run(["push",a.sample,remote]);run(["shell","run-as","org.codex.nfsugpreview","mkdir","-p","files"])
try:run(["shell","run-as","org.codex.nfsugpreview","cp",remote,"files/hud-gpu-scene.nab"])
finally:run(["shell","rm","-f",remote])
assert run(["exec-out","run-as","org.codex.nfsugpreview","sha256sum","files/hud-gpu-scene.nab"]).stdout.decode().split()[0]==hashlib.sha256(data).hexdigest()
run(["logcat","-c"])
result=run(["shell","am","instrument","-w","-r"]+(["-e","synthetic","true"] if a.synthetic_fixture else [])+["org.codex.nfsugpreview/.HudGpuInstrumentation"],180)
text=result.stdout.decode();(a.build/"hud-gpu-run.log").write_text(text,encoding="utf-8");print(text,flush=True)
(a.build/"hud-gpu-logcat.log").write_bytes(run(["logcat","-d","-s","NFSUGSceneGPU:E","AndroidRuntime:E","*:S"]).stdout)
assert "PASS_ANDROID_HUD_GPU_COMPOSITION" in text and "INSTRUMENTATION_CODE: -1" in text
r=json.loads(run(["exec-out","run-as","org.codex.nfsugpreview","cat","files/hud-gpu-report.json"]).stdout);r.update(synthetic_fixture=a.synthetic_fixture,apk_sha256=report["sha256"],fixture_sha256=hashlib.sha256(data).hexdigest(),scope="Original OBJ HUD over native geometry offscreen GPU diagnostic, not full-scene/playable native rendering or real-time cadence.")
(a.build/"hud-gpu-report.json").write_text(json.dumps(r,indent=2))
for name in ("hud-gpu-240.png","hud-gpu-4k.png"):(a.build/name).write_bytes(run(["exec-out","run-as","org.codex.nfsugpreview","cat","files/"+name]).stdout)
print("Android ordered-scene diagnostic GPU/source-pixel/context checks PASS",flush=True)
