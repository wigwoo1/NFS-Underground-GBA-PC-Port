"""Compare Android historical auxiliary rows with identical host diagnostic output."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,time
p=argparse.ArgumentParser()
for name in ("adb","root","runtime","reference","ndk"):p.add_argument("--"+name,type=Path,required=True)
p.add_argument("--keep-raw",action="store_true",help="Retain large reproducible raw diagnostic captures")
a=p.parse_args();here=Path(__file__).resolve().parent
source=a.root/"provenance_diagnostic.c";source.write_bytes((here/"provenance_diagnostic.c").read_bytes())
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+str(a.root)+";"+env["PATH"]
def local(args):
 result=subprocess.run([str(x) for x in args],env=env,capture_output=True)
 if result.returncode:
  (a.root/"diagnostic-local-failure.log").write_bytes(result.stdout+result.stderr)
  result.check_returncode()
 return result
def adb(args,timeout=40):return subprocess.run([str(a.adb),"-s","emulator-5556"]+[str(x) for x in args],check=True,capture_output=True,timeout=timeout)
local([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-I"+str(a.root/"source"),source,a.root/"capture-host.dll","-o",a.root/"provenance-host.exe"])
llvm=a.ndk/"toolchains/llvm/prebuilt/windows-x86_64"
local([llvm/"bin/clang.exe","--target=x86_64-none-linux-android26","--sysroot="+str(llvm/"sysroot"),"-O2","-fPIE","-pie","-I"+str(a.root/"source"),source,"-L"+str(a.root/"build-x86_64"),"-lnfsug_android_capture","-o",a.root/"provenance-x86_64"])
host=a.root/"provenance-check-host";host.mkdir(exist_ok=True)
result=local([a.root/"provenance-host.exe",a.runtime/"game.gba",a.runtime/"checkpoint.state",host,"1"]);assert b"PASS_ANDROID_CAPTURE_DIAGNOSTIC" in result.stdout
for _ in range(90):
 try:
  if adb(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator unavailable")
assert adb(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
remote="/data/local/tmp/nfsug_provenance_checks";adb(["shell","mkdir","-p",remote])
for file,name in ((a.root/"provenance-x86_64","provenance-check"),(a.root/"build-x86_64/libnfsug_android_capture.so","libnfsug_android_capture.so"),(a.runtime/"game.gba","game.gba"),(a.runtime/"checkpoint.state","checkpoint.state")):
 adb(["push",file,remote+"/"+name]);assert adb(["shell","sha256sum",remote+"/"+name]).stdout.decode().split()[0]==hashlib.sha256(file.read_bytes()).hexdigest()
adb(["shell","chmod","755",remote+"/provenance-check"])
result=adb(["shell","env","LD_LIBRARY_PATH="+remote,remote+"/provenance-check",remote+"/game.gba",remote+"/checkpoint.state",remote,"1"],180)
(a.root/"provenance-android-run.log").write_bytes(result.stdout+result.stderr);assert b"PASS_ANDROID_CAPTURE_DIAGNOSTIC" in result.stdout
out=a.root/"provenance-android";out.mkdir(exist_ok=True)

for name in ("frames.raw","audio.raw","joins.bin","splits.bin","owners.bin","provenance.bin","packets.bin"):adb(["pull",remote+"/"+name,out/name],120)
refs=json.loads(a.reference.read_text())["original_frame_hashes"]
for directory in (host,out):
 with (directory/"frames.raw").open("rb") as f:
  for i,expected in enumerate(refs):assert hashlib.sha256(f.read(153600)).hexdigest()==expected,(directory,i)
  assert not f.read(1)
 assert hashlib.sha256((directory/"audio.raw").read_bytes()).hexdigest()=="eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e"
 assert (directory/"joins.bin").stat().st_size==600*80
assert (host/"joins.bin").read_bytes()==(out/"joins.bin").read_bytes(),"Android ownership decisions differ from host"
raw=(out/"joins.bin").read_bytes();rows=[struct.unpack_from("<10Q",raw,i*80) for i in range(600)]
pairs=[list(row[2:]) for row in rows if row[1]]

reference=json.loads((a.root/"display-owner-host-report.json").read_text());assert pairs==reference["pairs"]
assert (host/"splits.bin").read_bytes()==(out/"splits.bin").read_bytes()
assert (host/"owners.bin").read_bytes()==(out/"owners.bin").read_bytes()
splitbytes=(out/"splits.bin").read_bytes();assert len(splitbytes)==600*112
splits=[list(struct.unpack_from("<14Q",splitbytes,i*112)[2:]) for i in range(600) if struct.unpack_from("<14Q",splitbytes,i*112)[1]]
assert splits==reference["splits"] and len(splits)==113
known={row[2] for row in json.loads(a.reference.read_text())["packets"]};copied=0
with (out/"owners.bin").open("rb") as f:
 for split in splits:
  for serial,page in ((split[1],split[5]),(split[2],split[6])):
   epoch,actual,size=struct.unpack("<3Q",f.read(24));data=f.read(size)
   assert epoch==split[0] and actual==serial and len(data)==size and hashlib.sha256(data).hexdigest() in known
   header=struct.unpack_from("<8I",data);assert header[4]==serial and header[7]==page;copied+=1
 assert not f.read(1)
assert copied==226

assert len(pairs)==481
history=(out/"provenance.bin").read_bytes();assert len(history)==600*5312 and history==(host/"provenance.bin").read_bytes()
assert history==(a.root/"provenance.bin").read_bytes(),"C diagnostics disagree with independent ctypes provenance"
independent=[]
for frame in range(600):
 w=struct.unpack_from("<664Q",history,frame*5312);rows=[w[24+y*4:28+y*4] for y in range(160)];matches=[]
 for owner in range(2):
  m=w[8+owner*8:16+owner*8]
  if m[7] and m[0]==w[0] and w[1]>=m[3] and m[6]==w[5] and all((r[0]&7)==4 and not (r[0]&128) and ((r[0]>>4)&1)==m[4] and r[1+m[4]]==m[5] and r[3]==m[6] for r in rows):matches.append(m)
 accepted=struct.unpack_from("<10Q",raw,frame*80)[1]
 assert bool(accepted)==(len(matches)==1)
 if accepted:independent.append(frame+1)
else:assert len(independent)==481
packet_hashes=[]
with (out/"packets.bin").open("rb") as f:
 while True:
  header=f.read(24)
  if not header:break
  frame,size,epoch=struct.unpack("<3Q",header);data=f.read(size);assert len(data)==size;packet_hashes.append([epoch,size,hashlib.sha256(data).hexdigest()])
assert packet_hashes==json.loads(a.reference.read_text())["packets"]
report={"result":"PASS_ANDROID_COMPLETION_REFRESH_PROVENANCE","api":adb(["shell","getprop","ro.build.version.sdk"]).stdout.decode().strip(),"abi":"x86_64","original_frames_each":600,"audio_digest_each":True,"whole_refreshes":len(pairs),"split_refreshes":len(splits),"owned_packet_copies":copied,"unavailable_refreshes":6,"all_decision_and_owner_bytes_equal_host":True,"owner_hashes_match_pc":True,"stale_reset_rejected":True,"short_buffers_unchanged":True,"library_sha256":hashlib.sha256((a.root/"build-x86_64/libnfsug_android_capture.so").read_bytes()).hexdigest(),"split_stream_sha256":hashlib.sha256(splitbytes).hexdigest(),"provenance_bytes_equal_independent_host":True,"independent_all_row_owner_checks":True,"pc_identical_published_packets":len(packet_hashes),"provenance_sha256":hashlib.sha256(history).hexdigest(),"gpu_rendering":False,"real_time_pacing":False,"physical_device":False}
(a.root/"provenance-android-report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

# Reports and small provenance/decision streams remain available. Large raw
# payloads are regenerable and otherwise consume over 1 GB per successful run.
if not a.keep_raw:
 removed=[]
 names=("frames.raw","audio.raw","owners.bin","packets.bin","after_load.raw","after_detach.raw","after_reopen.raw")
 for directory in (host,out):
  for name in names:
   file=(directory/name).resolve();assert file.parent==directory.resolve() and directory.resolve().parent==a.root.resolve()
   if file.exists():removed.append(dict(path=str(file),bytes=file.stat().st_size));file.unlink()
 adb(["shell","rm","-f"]+[remote+"/"+name for name in names])
 (a.root/"successful-run-cleanup.json").write_text(json.dumps(dict(removed=removed,bytes=sum(x["bytes"] for x in removed)),indent=2))
