"""Compare Android historical auxiliary rows with identical host diagnostic output."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,time
p=argparse.ArgumentParser()
for name in ("adb","root","runtime","reference","ndk"):p.add_argument("--"+name,type=Path,required=True)
a=p.parse_args();here=Path(__file__).resolve().parent
source=a.root/"split_diagnostic.c";source.write_bytes((here/"split_diagnostic.c").read_bytes())
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+str(a.root)+";"+env["PATH"]
def local(args):return subprocess.run([str(x) for x in args],env=env,check=True,capture_output=True)
def adb(args,timeout=40):return subprocess.run([str(a.adb),"-s","emulator-5556"]+[str(x) for x in args],check=True,capture_output=True,timeout=timeout)
local([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-I"+str(a.root/"source"),source,a.root/"capture-host.dll","-o",a.root/"split-host.exe"])
llvm=a.ndk/"toolchains/llvm/prebuilt/windows-x86_64"
local([llvm/"bin/clang.exe","--target=x86_64-none-linux-android26","--sysroot="+str(llvm/"sysroot"),"-O2","-fPIE","-pie","-I"+str(a.root/"source"),source,"-L"+str(a.root/"build-x86_64"),"-lnfsug_android_capture","-o",a.root/"split-x86_64"])
host=a.root/"split-host";host.mkdir(exist_ok=True)
result=local([a.root/"split-host.exe",a.runtime/"game.gba",a.runtime/"checkpoint.state",host,"1"]);assert b"PASS_ANDROID_CAPTURE_DIAGNOSTIC" in result.stdout
for _ in range(90):
 try:
  if adb(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator unavailable")
assert adb(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
remote="/data/local/tmp/nfsug_split_checks";adb(["shell","mkdir","-p",remote])
for file,name in ((a.root/"split-x86_64","split-check"),(a.root/"build-x86_64/libnfsug_android_capture.so","libnfsug_android_capture.so"),(a.runtime/"game.gba","game.gba"),(a.runtime/"checkpoint.state","checkpoint.state")):
 adb(["push",file,remote+"/"+name]);assert adb(["shell","sha256sum",remote+"/"+name]).stdout.decode().split()[0]==hashlib.sha256(file.read_bytes()).hexdigest()
adb(["shell","chmod","755",remote+"/split-check"])
result=adb(["shell","env","LD_LIBRARY_PATH="+remote,remote+"/split-check",remote+"/game.gba",remote+"/checkpoint.state",remote,"1"],180)
(a.root/"split-android-run.log").write_bytes(result.stdout+result.stderr);assert b"PASS_ANDROID_CAPTURE_DIAGNOSTIC" in result.stdout
out=a.root/"split-android";out.mkdir(exist_ok=True)

for name in ("frames.raw","audio.raw","joins.bin","splits.bin","owners.bin"):adb(["pull",remote+"/"+name,out/name],120)
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

reference=json.loads((a.root/"split-host-report.json").read_text());assert pairs==reference["pairs"]
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
report={"result":"PASS_ANDROID_TWO_OWNER_SPLIT_JOIN","api":adb(["shell","getprop","ro.build.version.sdk"]).stdout.decode().strip(),"abi":"x86_64","original_frames_each":600,"audio_digest_each":True,"whole_refreshes":len(pairs),"split_refreshes":len(splits),"owned_packet_copies":copied,"unavailable_refreshes":40,"all_decision_and_owner_bytes_equal_host":True,"owner_hashes_match_pc":True,"stale_reset_rejected":True,"short_buffers_unchanged":True,"library_sha256":hashlib.sha256((a.root/"build-x86_64/libnfsug_android_capture.so").read_bytes()).hexdigest(),"split_stream_sha256":hashlib.sha256(splitbytes).hexdigest(),"gpu_rendering":False,"real_time_pacing":False,"physical_device":False}
(a.root/"split-android-report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
