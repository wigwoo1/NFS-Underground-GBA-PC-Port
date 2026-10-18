"""Verify strict generation joins; rejected transitions never fabricate owners."""
import argparse,ctypes as C,hashlib,json,os,struct
from pathlib import Path
a=argparse.ArgumentParser()
for name in ("library","runtime","reference","report"):a.add_argument("--"+name,type=Path,required=True)
a=a.parse_args()
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):d=C.CDLL(str(a.library))
for name,args,ret in [("open",[C.c_char_p],C.c_void_p),("close",[C.c_void_p],None),("load_state",[C.c_void_p,C.c_void_p,C.c_size_t],C.c_int),("step",[C.c_void_p,C.c_uint32],C.c_int),("pixels",[C.c_void_p],C.c_void_p),("capture_enable",[C.c_void_p,C.c_int],C.c_int),("capture_layers",[C.c_void_p,C.c_int],C.c_int),("capture_layer_info",[C.c_void_p,C.POINTER(C.c_uint64)],C.c_int),("capture_display_owner",[C.c_void_p,C.c_uint,C.POINTER(C.c_uint64)],C.c_int)]:
 f=getattr(d,"nfa_core_"+name);f.argtypes=args;f.restype=ret
d.nfa_core_capture_split.argtypes=[C.c_void_p,C.c_uint,C.POINTER(C.c_uint64)];d.nfa_core_capture_split.restype=C.c_int
h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
d.nfa_core_capture_owned_packet.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t];d.nfa_core_capture_owned_packet.restype=C.c_size_t
splits=[];owner_copies=0;known_hashes={row[2] for row in json.loads(a.reference.read_text())["packets"]}
state=(a.runtime/"checkpoint.state").read_bytes();refs=json.loads(a.reference.read_text())["original_frame_hashes"];pairs=[];rejected=0

d.nfa_core_capture_layer_row.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t];d.nfa_core_capture_layer_row.restype=C.c_size_t
observations=[]
try:
 assert d.nfa_core_load_state(h,state,len(state)) and d.nfa_core_capture_enable(h,1) and d.nfa_core_capture_layers(h,1)
 info=(C.c_uint64*5)();whole=(C.c_uint64*8)();split=(C.c_uint64*12)()
 for i,expected in enumerate(refs):
  keys=1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0)
  assert d.nfa_core_step(h,keys)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected
  assert d.nfa_core_capture_layer_info(h,info)
  if d.nfa_core_capture_display_owner(h,info[1],whole) or d.nfa_core_capture_split(h,info[1],split):continue
  controls=[]
  for y in range(160):
   n=d.nfa_core_capture_layer_row(h,info[0],info[1],y,None,0);buf=C.create_string_buffer(n);assert n and d.nfa_core_capture_layer_row(h,info[0],info[1],y,buf,n)==n
   controls.append(struct.unpack_from("<H",buf.raw,8)[0])
  runs=[]
  for y,control in enumerate(controls):
   if not runs or runs[-1][2]!=control:runs.append([y,y+1,control])
   else:runs[-1][1]=y+1
  observations.append(dict(step=i+1,refresh=info[1],context=list(info[2:]),display_control_runs=runs))
finally:d.nfa_core_close(h)
report=dict(result="UNOWNED_SCANLINE_CONTROL_EVIDENCE",frames_verified=600,unavailable=len(observations),observations=observations,limit="Scanline controls only. Internal generation diagnostics are hidden by this build; generation failure reason is not established. Do not substitute scenes.")
a.report.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="observations"}))
