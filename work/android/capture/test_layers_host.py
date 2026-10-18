"""Verify historical layer rows without claiming geometry pairing or GPU output."""
import ctypes as C,hashlib,json,os,argparse,struct
from pathlib import Path
a=argparse.ArgumentParser()
for name in ("library","runtime","reference","report"):a.add_argument("--"+name,type=Path,required=True)
a=a.parse_args()
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):d=C.CDLL(str(a.library))
for name,args,ret in [
 ("open",[C.c_char_p],C.c_void_p),("close",[C.c_void_p],None),
 ("load_state",[C.c_void_p,C.c_void_p,C.c_size_t],C.c_int),
 ("step",[C.c_void_p,C.c_uint32],C.c_int),
 ("pixels",[C.c_void_p],C.c_void_p),
 ("capture_enable",[C.c_void_p,C.c_int],C.c_int),
 ("capture_layers",[C.c_void_p,C.c_int],C.c_int),
 ("capture_layer_info",[C.c_void_p,C.POINTER(C.c_uint64)],C.c_int),
 ("capture_layer_row",[C.c_void_p,C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t],C.c_size_t)]:
 f=getattr(d,"nfa_core_"+name);f.argtypes=args;f.restype=ret
state=(a.runtime/"checkpoint.state").read_bytes();reference=json.loads(a.reference.read_text())["original_frame_hashes"]
h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
try:
 assert d.nfa_core_load_state(h,state,len(state)) and d.nfa_core_capture_enable(h,1)
 info=(C.c_uint64*5)(*[77]*5)
 assert not d.nfa_core_capture_layer_info(h,info) and list(info)==[77]*5
 assert d.nfa_core_capture_layers(h,1)
 def sample():
  rows=[];latest=None;copies=0
  for frame in range(40):
   keys=1
   assert d.nfa_core_step(h,keys)==1
   assert hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==reference[frame]
   if not d.nfa_core_capture_layer_info(h,info):continue
   epoch,refresh,*context=info;latest=(epoch,refresh)
   rowhash=[]
   for y in (0,79,159):
    n=d.nfa_core_capture_layer_row(h,epoch,refresh,y,None,0);assert n==100480,n
    out=C.create_string_buffer(n);C.memset(out,165,n)
    assert not d.nfa_core_capture_layer_row(h,epoch,refresh,y,out,n-1) and out.raw==bytes([165])*n
    assert d.nfa_core_capture_layer_row(h,epoch,refresh,y,out,n)==n
    assert struct.unpack_from("<II",out.raw)==(refresh,y)
    rowhash.append(hashlib.sha256(out.raw).hexdigest());copies+=1
   rows.append([frame,refresh,context,rowhash])
  assert rows
  return rows,latest,copies
 first,old,copies=sample()
 assert d.nfa_core_load_state(h,state,len(state))
 sentinel=C.create_string_buffer(bytes([165])*100480)
 assert not d.nfa_core_capture_layer_row(h,*old,0,sentinel,100480) and sentinel.raw[:100480]==bytes([165])*100480
 assert not d.nfa_core_capture_layer_info(h,info)
 second,latest,more=sample();assert first==second
 assert d.nfa_core_capture_layers(h,0) and not d.nfa_core_capture_layer_info(h,info)
 assert not d.nfa_core_capture_layer_row(h,*latest,0,None,0)
finally:d.nfa_core_close(h)
report={"result":"PASS_HISTORICAL_AUXILIARY_ROWS","original_frame_checks":80,"copied_rows":copies+more,"refreshes_per_replay":len(first),"deterministic_state_replay":True,"stale_epoch_rejected":True,"short_buffer_unchanged":True,"gpu_rendering":False,"geometry_pairing":False}
a.report.write_text(json.dumps(report,indent=2));print(json.dumps(report))
