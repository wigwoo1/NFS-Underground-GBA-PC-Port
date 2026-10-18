"""Compare Android historical auxiliary rows with identical host diagnostic output."""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,time
p=argparse.ArgumentParser()
for name in ("adb","root","runtime","reference","ndk"):p.add_argument("--"+name,type=Path,required=True)
p.add_argument("--keep-raw",action="store_true",help="Retain large reproducible raw diagnostic captures")
a=p.parse_args();here=Path(__file__).resolve().parent
source=a.root/"bundle_diagnostic.c";source.write_bytes((here/"bundle_diagnostic.c").read_bytes())
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+str(a.root)+";"+env["PATH"]
def local(args):
 result=subprocess.run([str(x) for x in args],env=env,capture_output=True)
 if result.returncode:
  (a.root/"diagnostic-local-failure.log").write_bytes(result.stdout+result.stderr)
  result.check_returncode()
 return result
def adb(args,timeout=40):return subprocess.run([str(a.adb),"-s","emulator-5556"]+[str(x) for x in args],check=True,capture_output=True,timeout=timeout)
local([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-I"+str(a.root/"source"),source,a.root/"capture-host.dll","-o",a.root/"bundle-host.exe"])
llvm=a.ndk/"toolchains/llvm/prebuilt/windows-x86_64"
local([llvm/"bin/clang.exe","--target=x86_64-none-linux-android26","--sysroot="+str(llvm/"sysroot"),"-O2","-fPIE","-pie","-I"+str(a.root/"source"),source,"-L"+str(a.root/"build-x86_64"),"-lnfsug_android_capture","-o",a.root/"bundle-x86_64"])
host=a.root/"bundle-check-host";host.mkdir(exist_ok=True)

result=local([a.root/"bundle-host.exe",a.runtime/"game.gba",a.runtime/"checkpoint.state",host]);assert b"PASS_ANDROID_OWNED_BUNDLE" in result.stdout
for _ in range(90):
 try:
  if adb(["shell","getprop","sys.boot_completed"],8).stdout.strip()==b"1":break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise SystemExit("Owned emulator unavailable")
assert adb(["emu","avd","name"]).stdout.decode().splitlines()[0].strip()=="NFSUG_API30"
remote="/data/local/tmp/nfsug_bundle_checks";adb(["shell","mkdir","-p",remote])
for file,name in ((a.root/"bundle-x86_64","bundle-check"),(a.root/"build-x86_64/libnfsug_android_capture.so","libnfsug_android_capture.so"),(a.runtime/"game.gba","game.gba"),(a.runtime/"checkpoint.state","checkpoint.state")):
 adb(["push",file,remote+"/"+name]);assert adb(["shell","sha256sum",remote+"/"+name]).stdout.decode().split()[0]==hashlib.sha256(file.read_bytes()).hexdigest()
adb(["shell","chmod","755",remote+"/bundle-check"])
result=adb(["shell","env","LD_LIBRARY_PATH="+remote,remote+"/bundle-check",remote+"/game.gba",remote+"/checkpoint.state",remote],180)
(a.root/"bundle-android-run.log").write_bytes(result.stdout+result.stderr);assert b"PASS_ANDROID_OWNED_BUNDLE" in result.stdout
out=a.root/"bundle-android";out.mkdir(exist_ok=True)
for name in ("frames.raw","audio.raw","bundles.bin","whole.nab","split.nab"):adb(["pull",remote+"/"+name,out/name],120)
refs=json.loads(a.reference.read_text())["original_frame_hashes"]
for directory in (host,out):
 with (directory/"frames.raw").open("rb") as f:
  for i,expected in enumerate(refs):assert hashlib.sha256(f.read(153600)).hexdigest()==expected,(directory,i)
  assert not f.read(1)
 assert hashlib.sha256((directory/"audio.raw").read_bytes()).hexdigest()=="eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e"
raw=(out/"bundles.bin").read_bytes();assert len(raw)==600*48 and raw==(host/"bundles.bin").read_bytes()
records=[struct.unpack_from("<6Q",raw,i*48) for i in range(600)]
assert [[r[0],r[1],r[2]] for r in records]==json.loads((a.root/"bundle-crc-reference.json").read_text())
samples={}
for name in ("whole.nab","split.nab"):
 data=(out/name).read_bytes();assert data==(host/name).read_bytes();samples[name]=hashlib.sha256(data).hexdigest()
 # Independently parse all compact row refs in both byte-identical samples.
 h=struct.unpack_from("<16Q",data);assert h[0:3]==(0x3142414e,1,len(data));layer=data[h[12]:h[12]+h[13]];lh=struct.unpack_from("<8I",layer)
 assert lh[0]==0x31504c4e and lh[2]==len(layer)==28512+lh[4]*4096
 assert all(r<lh[4] for r in struct.unpack_from("<4000H",layer,20512))
report=dict(result="PASS_ANDROID_OWNED_COMBINED_BUNDLE",api=adb(["shell","getprop","ro.build.version.sdk"]).stdout.decode().strip(),abi="x86_64",original_frames_each=600,original_audio_each=True,bundles=594,whole=481,split=113,initial_missing=[r[0] for r in records if not r[1]],decoded_rows_each=2096,crc32_matches_independent_python=True,crc32_and_fnv64_match_host=True,byte_identical_sample_sha256=samples,retained_after_core_close=True,short_buffer_atomic=True,stale_epoch_rejected=True,library_sha256=hashlib.sha256((a.root/"build-x86_64/libnfsug_android_capture.so").read_bytes()).hexdigest(),gpu_rendering=False,real_time_pacing=False,physical_device=False)
assert report["initial_missing"]==list(range(1,7))
(a.root/"bundle-android-report.json").write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if not a.keep_raw:
 removed=[]
 for directory in (host,out):
  for name in ("frames.raw","audio.raw"):
   f=(directory/name).resolve();assert f.parent==directory.resolve() and directory.resolve().parent==a.root.resolve()
   if f.exists():removed.append(dict(path=str(f),bytes=f.stat().st_size));f.unlink()
 adb(["shell","rm","-f",remote+"/frames.raw",remote+"/audio.raw"])
 (a.root/"bundle-successful-cleanup.json").write_text(json.dumps(removed,indent=2))
