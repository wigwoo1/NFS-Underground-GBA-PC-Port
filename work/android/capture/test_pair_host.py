"""Verify strict generation joins; rejected transitions never fabricate owners."""
import argparse,ctypes as C,hashlib,json,os
from pathlib import Path
a=argparse.ArgumentParser()
for name in ("library","runtime","reference","report"):a.add_argument("--"+name,type=Path,required=True)
a=a.parse_args()
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):d=C.CDLL(str(a.library))
for name,args,ret in [("open",[C.c_char_p],C.c_void_p),("close",[C.c_void_p],None),("load_state",[C.c_void_p,C.c_void_p,C.c_size_t],C.c_int),("step",[C.c_void_p,C.c_uint32],C.c_int),("pixels",[C.c_void_p],C.c_void_p),("capture_enable",[C.c_void_p,C.c_int],C.c_int),("capture_layers",[C.c_void_p,C.c_int],C.c_int),("capture_layer_info",[C.c_void_p,C.POINTER(C.c_uint64)],C.c_int),("capture_pair",[C.c_void_p,C.c_uint,C.POINTER(C.c_uint64)],C.c_int)]:
 f=getattr(d,"nfa_core_"+name);f.argtypes=args;f.restype=ret
h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
state=(a.runtime/"checkpoint.state").read_bytes();refs=json.loads(a.reference.read_text())["original_frame_hashes"];pairs=[];rejected=0
try:
 assert d.nfa_core_load_state(h,state,len(state)) and d.nfa_core_capture_enable(h,1) and d.nfa_core_capture_layers(h,1)
 info=(C.c_uint64*5)();out=(C.c_uint64*8)()
 for i,expected in enumerate(refs):
  keys=1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0)
  assert d.nfa_core_step(h,keys)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected,i
  if not d.nfa_core_capture_layer_info(h,info):continue
  C.memset(out,165,C.sizeof(out));before=bytes(out)
  if d.nfa_core_capture_pair(h,info[1],out):
   row=list(out);assert row[0]==info[0] and row[2]<row[6]==info[1] and row[3] in (0,1) and row[4]>0 and row[5]>0 and row[7]>0
   pairs.append(row)
   sentinel=(C.c_uint64*8)(*[77]*8)
   assert not d.nfa_core_capture_pair(h,row[2],sentinel) and list(sentinel)==[77]*8
  else:assert bytes(out)==before;rejected+=1
 assert pairs,"No whole-scanout generation joins observed"
 assert d.nfa_core_load_state(h,state,len(state));sentinel=(C.c_uint64*8)(*[77]*8)
 assert not d.nfa_core_capture_pair(h,pairs[-1][6],sentinel) and list(sentinel)==[77]*8
 assert d.nfa_core_capture_layers(h,0) and not d.nfa_core_capture_pair(h,1,out)
finally:d.nfa_core_close(h)
report={"result":"PASS_STRICT_GEOMETRY_DISPLAY_JOIN_HOST","original_frames":600,"accepted":len(pairs),"rejected":rejected,"pairs":pairs,"stale_reset_rejected":True,"failure_output_unchanged":True,"split_scene_support":False,"gpu_rendering":False}
a.report.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="pairs"}))
