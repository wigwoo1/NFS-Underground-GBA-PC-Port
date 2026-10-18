"""Build isolated capture core from staged observer and existing Android mGBA."""
import argparse,hashlib,json,os,struct,subprocess
from pathlib import Path
a=argparse.ArgumentParser()
for name in ("output","ndk","ninja","cmake","core_build"):a.add_argument("--"+name.replace("_","-"),type=Path,required=True)
a.add_argument("--jni",action="store_true")
a.add_argument("--visibility-capacity",type=int,choices=(20,64),default=20)
a=a.parse_args();here=Path(__file__).resolve().parent;source=a.output/"source"
subprocess.run([os.sys.executable,str(here/"stage_capture.py"),"--output",str(a.output)],check=True)
for name in ("nfsug_capture.h","capture_diagnostic.c"):(source/name).write_bytes((here/name).read_bytes())
cpu=json.loads((a.output/"source-provenance.json").read_text())["cpu_sources"]
project=here.parents[2]
package=project/"work/v2/package/NFSUG-Native-Renderer-source"
args=["-O2","-shared","-ffunction-sections","-fdata-sections","-DBUILD_STATIC","-DM_CORE_GBA","-DUSE_DEBUGGERS","-DNF_VISIBILITY_CAPTURE","-DNF_VISIBILITY_QUEUE_CAPACITY="+str(a.visibility_capacity),"-DNF_ROAD_ATTRIBUTE_CORRECTION","-DNF_PACKET_NO_FILES","-D_GNU_SOURCE",
 "-I"+str(source),"-I"+str(source/"camera"),"-I"+str(package/"deps/mgba-0.10.5/include"),"-I"+str(package/"build/mgba-nfsug/include"),
 str(source/"nfsug_android_core.c"),str(source/"observer.c"),str(source/"native_span.c")]+[str(source/"camera"/n) for n in cpu]+[
 str(package/"build/mgba-nfsug/libmgba.a"),"-lws2_32","-lshlwapi","-lole32","-luuid","-lm","-Wl,--gc-sections","-o",str(a.output/"capture-host.dll")]
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+env["PATH"]
def run(command,name):
 with (a.output/(name+".log")).open("w") as log:subprocess.run([str(x) for x in command],env=env,check=True,stdout=log,stderr=subprocess.STDOUT)
 print(name+" passed",flush=True)
run([r"C:\msys64\mingw64\bin\gcc.exe"]+args,"host-build")
targets=[];ndk=a.ndk/"toolchains/llvm/prebuilt/windows-x86_64"
required={"nfa_core_open","nfa_core_step","nfa_core_load_state","nfa_core_capture_enable","nfa_core_capture_stats","nfa_core_capture_copy","nfa_core_capture_layers","nfa_core_capture_layer_info","nfa_core_capture_layer_row","nfa_core_capture_pair","nfa_core_capture_owned_packet","nfa_core_capture_split","nfa_core_capture_display_owner","nfa_core_capture_provenance","nfa_core_capture_bundle","nfa_core_capture_source_world_enable","nfa_core_capture_source_world"}
for abi,target,machine in (("x86_64","x86_64-none-linux-android26",62),("arm64-v8a","aarch64-none-linux-android26",183)):
 build=a.output/(("build-jni-" if a.jni else "build-")+abi)
 run([a.cmake,"-S",source,"-B",build,"-G","Ninja","-DCMAKE_MAKE_PROGRAM="+str(a.ninja),"-DCMAKE_TOOLCHAIN_FILE="+str(a.ndk/"build/cmake/android.toolchain.cmake"),
 "-DANDROID_ABI="+abi,"-DNF_VISIBILITY_QUEUE_CAPACITY="+str(a.visibility_capacity),"-DANDROID_PLATFORM=android-26","-DCMAKE_BUILD_TYPE=Release","-DNF_CAPTURE_JNI="+("ON" if a.jni else "OFF"),"-DNF_MGBA_SOURCE="+str(a.core_build/"mgba-source"),"-DNF_MGBA_BUILD="+str(a.core_build/("build-"+abi))],"configure-"+abi)
 run([a.cmake,"--build",build,"--parallel","4"],"build-"+abi)
 lib=build/("libnfsug_android_core.so" if a.jni else "libnfsug_android_capture.so");data=lib.read_bytes()
 assert data[:6]==b"\x7fELF\x02\x01" and struct.unpack_from("<HH",data,16)==(3,machine)
 offset=struct.unpack_from("<Q",data,32)[0];stride,count=struct.unpack_from("<HH",data,54)
 aligns=[struct.unpack_from("<II6Q",data,offset+i*stride)[-1] for i in range(count) if struct.unpack_from("<I",data,offset+i*stride)[0]==1]
 assert aligns and all(n>=16384 for n in aligns)
 symbols=subprocess.run([str(ndk/"bin/llvm-readelf.exe"),"--dyn-syms","--wide",str(lib)],check=True,capture_output=True,text=True).stdout
 (a.output/("exports-"+abi+".log")).write_text(symbols)
 defined=set()
 for line in symbols.splitlines():
  row=line.split()
  if len(row)>=8 and row[3]=="FUNC" and row[4] in ("GLOBAL","WEAK") and row[6]!="UND":defined.add(row[7])
 if a.jni:
  required.update("Java_org_codex_nfsugpreview_NativeCore_"+name for name in ("openNative","closeNative","stepNative","pauseNative","timingNative","frameNative","audioNative","snapshotNative","restoreNative","captureSupportedNative","captureEnableNative","captureStatsNative","capturePacketNative","captureLayersNative","captureSceneNative","captureSourceWorldEnableNative","captureSourceWorldNative"))
 assert required<=defined
 assert not {"nf_init","nf_60","nf_speed","nf_frame","nf_pace","nf_dt"}&defined
 if a.jni:
  targets.append({"abi":abi,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"machine":machine,"load_alignments":aligns,
   "library":str(lib.relative_to(a.output)),"legacy_speed_apis_exported":False})
  continue
 executable=a.output/("capture-check-"+abi)
 run([ndk/"bin/clang.exe","--target="+target,"--sysroot="+str(ndk/"sysroot"),"-O2","-fPIE","-pie","-I"+str(source),source/"capture_diagnostic.c",
 "-L"+str(build),"-lnfsug_android_capture","-o",executable],"diagnostic-build-"+abi)
 targets.append({"abi":abi,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"machine":machine,"load_alignments":aligns,
 "diagnostic_sha256":hashlib.sha256(executable.read_bytes()).hexdigest(),"legacy_speed_apis_exported":False})
native_inputs=dict(json.loads((a.output/"source-provenance.json").read_text())["staged_traffic_extension"]["maintained_source_sha256"])
for name in ("nfsug_android_core.c","nfsug_android_core.h","nfsug_android_jni.c"):
 native_inputs["work/android/"+name]=hashlib.sha256((project/"work/android"/name).read_bytes()).hexdigest()
for file in here.iterdir():
 if file.is_file():native_inputs["work/android/capture/"+file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
report={"result":"PASS_ANDROID_BORROWED_CAPTURE_BUILD","jni":a.jni,"visibility_capacity":a.visibility_capacity,"native_inputs":native_inputs,"targets":targets,"app_updated":False,"gpu_rendering":False,"android_runtime":False}
(a.output/("capture-jni-build-report.json" if a.jni else "capture-build-report.json")).write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
