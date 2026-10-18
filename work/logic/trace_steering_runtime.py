from __future__ import annotations
import ctypes as C, json, os, struct
from pathlib import Path

PROJECT = Path(r"G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port")
ROM = Path(r"G:\EXTRA DATA DRIVE\Desktop\Emulators\GBA\GBA ROMS\Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba")
TRYOUT = PROJECT / "tryout" / "NFSUG-mGBA-Renderer-Preview-20261012"
DLL = PROJECT / "work" / "logic" / "thumbtrace-diagnostic" / "nfsprobe.dll"
STATE = PROJECT / "work" / "logic" / "driving-diagnostic.state"
OUT = PROJECT / "work" / "logic" / "steering_runtime_trace.json"
P, U, I = C.c_void_p, C.c_uint32, C.c_int
dll_directory = os.add_dll_directory(str(DLL.parent))
msys_directory = os.add_dll_directory(r"C:\msys64\mingw64\bin")
lib = C.CDLL(str(DLL))
lib.nf_init.argtypes=[C.c_char_p,C.c_char_p];lib.nf_init.restype=I
lib.nf_state.argtypes=[C.c_char_p,I];lib.nf_state.restype=I
lib.nf_frame.argtypes=[U]
lib.nf_calls.argtypes=[C.c_char_p]
lib.nf_debug.argtypes=[U]
lib.nf_scene_enable.argtypes=[I]
lib.nf_debug_memory_config.argtypes=[U,U];lib.nf_debug_memory_config.restype=I
lib.nf_debug_data.argtypes=[C.POINTER(I)];lib.nf_debug_data.restype=C.POINTER(U)
lib.nf_debug_memory_data.argtypes=[C.POINTER(U),C.POINTER(U)];lib.nf_debug_memory_data.restype=C.POINTER(C.c_uint8)
lib.nf_close.argtypes=[]

PCs=[("direct_input_branch",0x08009730,6),
     ("helper_entry",0x08008C94,2),
     ("helper_return",0x08009056,6),
     ("steering_accumulator_write",0x080097EE,6)]
scenarios=[("left_plus_accel",33),("right_plus_accel",17),("accel_only",1)]
all_runs=[]
assert lib.nf_init(str(ROM).encode(),b""), "mGBA could not load the expected ROM"
lib.nf_scene_enable(1)  # Turns on the passive ARM observer used by nf_debug; no game instructions are replaced.
try:
    for name,keys in scenarios:
        call_path=PROJECT/"work"/"logic"/f"thumb_calls_{name}.csv"
        lib.nf_calls(str(call_path).encode())
        for label,pc,mem_reg in PCs:
            assert lib.nf_state(str(STATE).encode(),0), "isolated checkpoint did not load"
            lib.nf_debug(pc)
            assert lib.nf_debug_memory_config(mem_reg,256), "debug-memory config failed"
            seen=0; samples=[]
            for frame in range(1,121):
                lib.nf_frame(keys)
                n=I(); regs_ptr=lib.nf_debug_data(C.byref(n));
                if n.value>seen:
                    mcount=U(); msize=U(); mem_ptr=lib.nf_debug_memory_data(C.byref(mcount),C.byref(msize))
                    for index in range(seen,n.value):
                        regs=[int(regs_ptr[index*16+j]) for j in range(16)]
                        row=bytes(mem_ptr[index*256:index*256+msize.value]) if mem_ptr and mcount.value>index else b""
                        vals={"r0":regs[0],"r1":regs[1],"r2":regs[2],"r3":regs[3],"r5":regs[5],"r6":regs[6],"r7":regs[7],"r8":regs[8],"r9":regs[9],"r10":regs[10],"r11":regs[11],"r12":regs[12],"sp":regs[13],"lr":regs[14],"pc":regs[15]-2,"frame":frame,"memory_base":regs[mem_reg]}
                        offsets=(0x2c,0x58,0x134,0x138,0x13c,0x158,0x15c,0x160) if mem_reg==6 else (0x58,)
                        for off in offsets:
                            if off+4<=len(row): vals[f"m_{off:03x}_s32"]=struct.unpack_from("<i",row,off)[0]
                        if label=="helper_entry" and len(row)>=0x5c: vals["helper_context_plus_58_u32"]=struct.unpack_from("<I",row,0x58)[0]
                        samples.append(vals)
                    seen=n.value
            all_runs.append({"scenario":name,"keys":keys,"pc_label":label,"pc":f"0x{pc:08X}","samples_captured":len(samples),"samples":samples,"call_trace":str(call_path)})
        lib.nf_calls(None)
finally:
    lib.nf_calls(None)
    lib.nf_close()
OUT.write_text(json.dumps({"rom_sha256":"53817AEC76A623DC2C7782DDF841F89F369AEBE5A92A28C9AFC69FEAF914A593","state":"isolated tryout checkpoint copy","frames_per_pass":120,"scenarios":[{"name":n,"keys":k} for n,k in scenarios],"runs":all_runs},indent=2),encoding="utf-8")
for run in all_runs:
    vals=run["samples"]
    r0=sorted({v["r0"] for v in vals})[:8]
    r7=sorted({v["r7"] for v in vals})[:8]
    steering=sorted({v.get("m_02c_s32") for v in vals if "m_02c_s32" in v})[:8]
    print(run["scenario"],run["pc_label"],"samples",len(vals),"r0",r0,"r7",r7,"steering",steering)
print(f"wrote {OUT}")