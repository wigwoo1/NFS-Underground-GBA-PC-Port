"""Compile/run actual JNI in a Windows JVM, comparing independent core output."""
import argparse,ctypes as C,hashlib,json,os,subprocess
from pathlib import Path
a=argparse.ArgumentParser()
a.add_argument("--jdk",type=Path,required=True)
a.add_argument("--output",type=Path,required=True)
a.add_argument("--runtime",type=Path,required=True)
a.add_argument("--core-library",type=Path,required=True)
a=a.parse_args()
source=Path(__file__).resolve().parent
a.output.mkdir(parents=True,exist_ok=True)
classes=a.output/"classes";classes.mkdir(exist_ok=True)
headers=a.output/"headers";headers.mkdir(exist_ok=True)
env=os.environ.copy();env["PATH"]=r"C:\msys64\mingw64\bin;"+env["PATH"]
def run(args):subprocess.run([str(x) for x in args],check=True,env=env)
run([a.jdk/"bin/javac.exe","--release","8","-h",headers,"-d",classes,
 source/"java/org/codex/nfsugpreview/NativeCore.java",source/"tests/org/codex/nfsugpreview/CoreBoundaryTest.java"])
package=source.parent/"v2/package/NFSUG-Native-Renderer-source"
run([r"C:\msys64\mingw64\bin\gcc.exe","-O2","-shared","-DBUILD_STATIC","-DM_CORE_GBA","-DUSE_DEBUGGERS",
 "-I"+str(package/"deps/mgba-0.10.5/include"),"-I"+str(package/"build/mgba-nfsug/include"),
 "-I"+str(a.jdk/"include"),"-I"+str(a.jdk/"include/win32"),
 "-include",headers/"org_codex_nfsugpreview_NativeCore.h",
 source/"nfsug_android_core.c",source/"nfsug_android_jni.c",package/"build/mgba-nfsug/libmgba.a",
 "-lws2_32","-lshlwapi","-lole32","-luuid","-Wl,--gc-sections","-o",a.output/"nfsug_android_core.dll"])
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):
 d=C.CDLL(str(a.core_library))
 d.nfa_core_open.argtypes=[C.c_char_p];d.nfa_core_open.restype=C.c_void_p
 d.nfa_core_load_state.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 d.nfa_core_step.argtypes=[C.c_void_p,C.c_uint32]
 d.nfa_core_pixels.argtypes=[C.c_void_p];d.nfa_core_pixels.restype=C.c_void_p
 d.nfa_core_close.argtypes=[C.c_void_p]
 state=(a.runtime/"checkpoint.state").read_bytes()
 h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
 hashes=[]
 try:
  assert d.nfa_core_load_state(h,state,len(state))
  for i in range(600):
   assert d.nfa_core_step(h,1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0))==1
   pixels=bytearray(C.string_at(d.nfa_core_pixels(h),240*160*4))
   pixels[3::4]=b"\xff"*(240*160)
   hashes.append(hashlib.sha256(pixels).hexdigest())
 finally:d.nfa_core_close(h)
reference=a.output/"rgba-reference.txt";reference.write_text("\n".join(hashes)+"\n")
run([a.jdk/"bin/java.exe","-Xcheck:jni","-Djava.library.path="+str(a.output),"-cp",classes,
 "org.codex.nfsugpreview.CoreBoundaryTest",a.runtime/"game.gba",a.runtime/"checkpoint.state",reference,a.output/"jni-host-report.json"])
