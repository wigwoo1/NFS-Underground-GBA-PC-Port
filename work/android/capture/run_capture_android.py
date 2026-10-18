"""Compare real Android core/capture output against original frame/audio references."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,time
a=argparse.ArgumentParser()
for name in ("adb","root","runtime","reference"):a.add_argument("--"+name,type=Path,required=True)
a=a.parse_args()
def run(args,timeout=30):
 return subprocess.run([str(a.adb),"-s","emulator-5556"]+args,check=True,capture_output=True,timeout=timeout)
for i in range(90):
 try:
  if run(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator boot was not observed")
assert run(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
remote="/data/local/tmp/nfsug_capture_checks"
run(["shell","mkdir","-p",remote])
for file,target in ((a.root/"build-x86_64/libnfsug_android_capture.so","libnfsug_android_capture.so"),
 (a.root/"capture-check-x86_64","capture-check-x86_64"),(a.runtime/"game.gba","game.gba"),(a.runtime/"checkpoint.state","checkpoint.state")):
 run(["push",str(file),remote+"/"+target])
 assert run(["shell","sha256sum",remote+"/"+target]).stdout.decode().split()[0]==hashlib.sha256(file.read_bytes()).hexdigest()
run(["shell","chmod","755",remote+"/capture-check-x86_64"])
reference=json.loads(a.reference.read_text())["original_frame_hashes"]
expected_packets=json.loads((a.root/"capture-host-tests.json").read_text())["packets"]
reports=[]
for enabled in (0,1):
 name="capture-on" if enabled else "capture-off";directory=remote+"/"+name
 run(["shell","mkdir","-p",directory]);out=a.root/name;out.mkdir(exist_ok=True)
 result=run(["shell","env","LD_LIBRARY_PATH="+remote,remote+"/capture-check-x86_64",remote+"/game.gba",remote+"/checkpoint.state",directory,str(enabled)],180)
 text=result.stdout.decode();(out/"diagnostic.log").write_text(text,encoding="utf-8");report=json.loads(text)
 assert report["result"]=="PASS_ANDROID_CAPTURE_DIAGNOSTIC" and report["frames"]==600
 for filename in ("frames.raw","audio.raw","packets.bin","after_detach.raw","after_reopen.raw"):
  run(["pull",directory+"/"+filename,str(out/filename)],120)
 for filename,expected in (("frames.raw",reference),("after_detach.raw",reference[:16]),("after_reopen.raw",reference[:16])):
  with (out/filename).open("rb") as stream:
   for i,value in enumerate(expected):
    data=stream.read(153600);assert len(data)==153600 and hashlib.sha256(data).hexdigest()==value,(name,filename,i)
   assert not stream.read(1)
 audio=hashlib.sha256((out/"audio.raw").read_bytes()).hexdigest()
 assert audio=="eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e",audio
 rows=[]
 with (out/"packets.bin").open("rb") as stream:
  while True:
   header=stream.read(24)
   if not header:break
   assert len(header)==24
   frame,size,epoch=struct.unpack("<3Q",header);data=stream.read(size);assert len(data)==size
   words=struct.unpack_from("<8I",data)
   rows.append({"frame":frame,"epoch":epoch,"serial":words[4],"bytes":size,"sha256":hashlib.sha256(data).hexdigest()})
 assert rows==(expected_packets if enabled else []),"Android packets differ from same observer on host"
 if enabled:
  for filename in ("after_load.raw","after_load_packet.bin"):run(["pull",directory+"/"+filename,str(out/filename)],60)
  with (out/"after_load.raw").open("rb") as stream:
   for expected in reference[:16]:assert hashlib.sha256(stream.read(153600)).hexdigest()==expected
   assert not stream.read(1)
  newest=[p for p in expected_packets if p["frame"]<=16][-1]
  assert hashlib.sha256((out/"after_load_packet.bin").read_bytes()).hexdigest()==newest["sha256"]
  report["capture_resumed_after_state_load"]=True
 assert report["packets"]==len(rows)
 report.update(original_frame_hashes=600,detach_and_reopen_hashes=32,audio_sha256=audio,packet_hashes_match_host=True)
 reports.append(report);print(name+": original frames/audio, packet hashes and lifecycle PASS",flush=True)
summary={"result":"PASS_ANDROID_CAPTURE_ORIGINAL_OUTPUT_PARITY","api":run(["shell","getprop","ro.build.version.sdk"]).stdout.decode().strip(),
 "abi":run(["shell","getprop","ro.product.cpu.abi"]).stdout.decode().strip(),"cases":reports,
 "library_sha256":hashlib.sha256((a.root/"build-x86_64/libnfsug_android_capture.so").read_bytes()).hexdigest(),
 "gpu_rendering":False,"real_time_pacing":False,"physical_device":False,
 "scope":"Unpaced diagnostic original-frame stepping on Android, capture off/on; not playable native rendering or 60-fps gameplay."}
(a.root/"capture-android-tests.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
