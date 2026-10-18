"""Build identical shared PC scene decoding/ownership code for Android and host."""
import argparse,hashlib,json,os,re,struct,subprocess
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument("--ndk",type=Path,required=True);a.add_argument("--ninja",type=Path,required=True)
a.add_argument("--cmake",type=Path,required=True);a.add_argument("--output",type=Path,required=True)
a=a.parse_args()
source=Path(__file__).resolve().parent
camera=source.parents[1]/"camera"
a.output.mkdir(parents=True,exist_ok=True)
shared=a.output/"shared";shared.mkdir(exist_ok=True)
queue=["scene_packet.c","snapshot_store.c","presentation_timeline.c","rigid_motion.c"];copied={}
while queue:
 name=queue.pop()
 if name in copied:continue
 data=(camera/name).read_bytes();target=shared/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 copied[name]={"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
 for inc in re.findall(r'^\s*#include\s+"([^"]+)"',data.decode("utf-8",errors="ignore"),re.M):
  child=(Path(name).parent/inc).as_posix();assert ".." not in Path(child).parts;queue.append(child)
project=a.output/"project";project.mkdir(exist_ok=True)
inputs={}
for name in ("CMakeLists.txt","platform_exports.h","nfsug_scene_owner.c","nfsug_scene_owner.h","test_scene_android.c"):
 data=(source/name).read_bytes();(project/name).write_bytes(data);inputs[name]=hashlib.sha256(data).hexdigest()
(a.output/"shared-source-provenance.json").write_text(json.dumps({"source":str(camera),"files":copied},indent=2))
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+env["PATH"]
def run(args,name):
 with (a.output/(name+".log")).open("w") as log:subprocess.run([str(x) for x in args],check=True,env=env,stdout=log,stderr=subprocess.STDOUT)
 print(name+" passed",flush=True)
run([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-shared","-I"+str(shared),project/"nfsug_scene_owner.c"]+
 [shared/n for n in ("scene_packet.c","snapshot_store.c","presentation_timeline.c","rigid_motion.c")]+["-lm","-o",a.output/"scene-host.dll"],"host-build")
required={"nf_android_scene_open","nf_android_scene_close","nf_android_scene_info","nf_android_scene_copy","nf_android_scene_section",
 "nf_scene_packet_view","nf_scene_packet_build","nf_snapshot_create","nf_pose_decode"}
targets=[]
for abi,machine in (("arm64-v8a",183),("x86_64",62)):
 build=a.output/("build-"+abi)
 run([a.cmake,"-S",project,"-B",build,"-G","Ninja","-DCMAKE_MAKE_PROGRAM="+str(a.ninja),
  "-DCMAKE_TOOLCHAIN_FILE="+str(a.ndk/"build/cmake/android.toolchain.cmake"),"-DANDROID_ABI="+abi,
  "-DANDROID_PLATFORM=android-26","-DCMAKE_BUILD_TYPE=Release","-DNF_SHARED_SCENE="+str(shared),"-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"],"configure-"+abi)
 run([a.cmake,"--build",build,"--parallel","4"],"build-"+abi)
 lib=build/"libnfsug_android_scene.so";data=lib.read_bytes()
 assert data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(3,machine)
 phoff=struct.unpack_from("<Q",data,32)[0];stride,count=struct.unpack_from("<HH",data,54)
 aligns=[struct.unpack_from("<II6Q",data,phoff+i*stride)[-1] for i in range(count) if struct.unpack_from("<I",data,phoff+i*stride)[0]==1]
 assert aligns and all(n>=16384 for n in aligns)
 tool=a.ndk/"toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe"
 symbols=subprocess.run([str(tool),"--dyn-syms","--wide",str(lib)],check=True,capture_output=True,text=True).stdout
 (a.output/("exports-"+abi+".log")).write_text(symbols)
 defined=set()
 for line in symbols.splitlines():
  row=line.split()
  if len(row)>=8 and row[3]=="FUNC" and row[4] in ("GLOBAL","WEAK") and row[6]!="UND":defined.add(row[7])
 assert required<=defined,required-defined
 targets.append({"abi":abi,"machine":machine,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"load_alignments":aligns,"defined_required_exports":sorted(required)})
diagnostics=[]
ndk_tools=a.ndk/"toolchains/llvm/prebuilt/windows-x86_64"
for abi,target in (("x86_64","x86_64-none-linux-android26"),("arm64-v8a","aarch64-none-linux-android26")):
 executable=a.output/("scene-check-"+abi)
 run([ndk_tools/"bin/clang.exe","--target="+target,"--sysroot="+str(ndk_tools/"sysroot"),"-O2","-fPIE","-pie",
  "-I"+str(project),project/"test_scene_android.c","-L"+str(a.output/("build-"+abi)),"-lnfsug_android_scene","-o",executable],"native-test-build-"+abi)
 diagnostics.append({"abi":abi,"sha256":hashlib.sha256(executable.read_bytes()).hexdigest(),"bytes":executable.stat().st_size})
report={"result":"PASS_ANDROID_SHARED_SCENE_BUILD","shared_sources":copied,"wrapper_sources":inputs,"targets":targets,"native_diagnostics":diagnostics,
 "capture_bridge_integrated":False,"gpu_renderer_integrated":False,"android_runtime_verified":False,
 "scope":"Shared PC scene packet/snapshot/motion code plus immutable-owner API cross-build, not native Android rendering."}
(a.output/"scene-build-report.json").write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ("shared_sources","wrapper_sources")},indent=2))
