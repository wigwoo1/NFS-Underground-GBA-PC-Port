"""Compare Android historical auxiliary rows with identical host diagnostic output."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,time
p=argparse.ArgumentParser()
for name in ("adb","root","runtime","reference","ndk"):p.add_argument("--"+name,type=Path,required=True)
a=p.parse_args();here=Path(__file__).resolve().parent
source=a.root/"layers_diagnostic.c";source.write_bytes((here/"layers_diagnostic.c").read_bytes())
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+str(a.root)+";"+env["PATH"]
def local(args):return subprocess.run([str(x) for x in args],env=env,check=True,capture_output=True)
def adb(args,timeout=40):return subprocess.run([str(a.adb),"-s","emulator-5556"]+[str(x) for x in args],check=True,capture_output=True,timeout=timeout)
local([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-I"+str(a.root/"source"),source,a.root/"capture-host.dll","-o",a.root/"layers-host.exe"])
llvm=a.ndk/"toolchains/llvm/prebuilt/windows-x86_64"
local([llvm/"bin/clang.exe","--target=x86_64-none-linux-android26","--sysroot="+str(llvm/"sysroot"),"-O2","-fPIE","-pie","-I"+str(a.root/"source"),source,"-L"+str(a.root/"build-x86_64"),"-lnfsug_android_capture","-o",a.root/"layers-x86_64"])
host=a.root/"layers-host";host.mkdir(exist_ok=True)
result=local([a.root/"layers-host.exe",a.runtime/"game.gba",a.runtime/"checkpoint.state",host]);assert b"PASS_AUXILIARY" in result.stdout
for _ in range(90):
 try:
  if adb(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator unavailable")
assert adb(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
remote="/data/local/tmp/nfsug_auxiliary_rows";adb(["shell","mkdir","-p",remote])
for file,name in ((a.root/"layers-x86_64","layers-check"),(a.root/"build-x86_64/libnfsug_android_capture.so","libnfsug_android_capture.so"),(a.runtime/"game.gba","game.gba"),(a.runtime/"checkpoint.state","checkpoint.state")):
 adb(["push",file,remote+"/"+name]);assert adb(["shell","sha256sum",remote+"/"+name]).stdout.decode().split()[0]==hashlib.sha256(file.read_bytes()).hexdigest()
adb(["shell","chmod","755",remote+"/layers-check"])
result=adb(["shell","env","LD_LIBRARY_PATH="+remote,remote+"/layers-check",remote+"/game.gba",remote+"/checkpoint.state",remote],120)
(a.root/"layers-android-run.log").write_bytes(result.stdout+result.stderr);assert b"PASS_AUXILIARY" in result.stdout
out=a.root/"layers-android";out.mkdir(exist_ok=True)
for name in ("frames.raw","rows.bin"):adb(["pull",remote+"/"+name,out/name],120)
refs=json.loads(a.reference.read_text())["original_frame_hashes"][:40]*2
for directory in (host,out):
 with (directory/"frames.raw").open("rb") as f:
  for i,expected in enumerate(refs):assert hashlib.sha256(f.read(153600)).hexdigest()==expected,(directory,i)
  assert not f.read(1)
 assert (directory/"rows.bin").stat().st_size==80*(40+3*100480)
assert (host/"rows.bin").read_bytes()==(out/"rows.bin").read_bytes(),"Android historical rows differ from host"
raw=(out/"rows.bin").read_bytes();stride=40+3*100480
for i in range(40):
 first=raw[i*stride:(i+1)*stride];second=raw[(40+i)*stride:(41+i)*stride]
 assert struct.unpack_from("<Q",second)[0]>struct.unpack_from("<Q",first)[0]
 assert first[8:]==second[8:],i
report={"result":"PASS_ANDROID_HISTORICAL_AUXILIARY_ROWS","api":adb(["shell","getprop","ro.build.version.sdk"]).stdout.decode().strip(),"abi":"x86_64","host_original_frame_checks":80,"android_original_frame_checks":80,"row_copies_each":240,"all_row_bytes_equal_host":True,"deterministic_state_replay":True,"stale_epoch_rejected":True,"short_buffer_atomic":True,"pause_preserved":True,"disable_rejected":True,"rows_sha256":hashlib.sha256(raw).hexdigest(),"library_sha256":hashlib.sha256((a.root/"build-x86_64/libnfsug_android_capture.so").read_bytes()).hexdigest(),"gpu_rendering":False,"geometry_pairing":False,"real_time_pacing":False,"physical_device":False}
(a.root/"layers-android-report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
