"""Verify strict generation joins; rejected transitions never fabricate owners."""
import argparse,ctypes as C,hashlib,json,os,struct
from pathlib import Path
a=argparse.ArgumentParser()
for name in ("library","runtime","reference","report"):a.add_argument("--"+name,type=Path,required=True)
a=a.parse_args()
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):d=C.CDLL(str(a.library))
for name,args,ret in [("open",[C.c_char_p],C.c_void_p),("close",[C.c_void_p],None),("load_state",[C.c_void_p,C.c_void_p,C.c_size_t],C.c_int),("step",[C.c_void_p,C.c_uint32],C.c_int),("pixels",[C.c_void_p],C.c_void_p),("capture_enable",[C.c_void_p,C.c_int],C.c_int),("capture_layers",[C.c_void_p,C.c_int],C.c_int),("capture_layer_info",[C.c_void_p,C.POINTER(C.c_uint64)],C.c_int),("capture_pair",[C.c_void_p,C.c_uint,C.POINTER(C.c_uint64)],C.c_int)]:
 f=getattr(d,"nfa_core_"+name);f.argtypes=args;f.restype=ret
d.nfa_core_capture_split.argtypes=[C.c_void_p,C.c_uint,C.POINTER(C.c_uint64)];d.nfa_core_capture_split.restype=C.c_int
h=d.nfa_core_open(os.fsencode(a.runtime/"game.gba"));assert h
d.nfa_core_capture_owned_packet.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t];d.nfa_core_capture_owned_packet.restype=C.c_size_t
splits=[];owner_copies=0;known_hashes={row[2] for row in json.loads(a.reference.read_text())["packets"]}
state=(a.runtime/"checkpoint.state").read_bytes();refs=json.loads(a.reference.read_text())["original_frame_hashes"];pairs=[];rejected=0
try:
 assert d.nfa_core_load_state(h,state,len(state)) and d.nfa_core_capture_enable(h,1) and d.nfa_core_capture_layers(h,1)
 info=(C.c_uint64*5)();out=(C.c_uint64*8)()
 for i,expected in enumerate(refs):
  keys=1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0)
  assert d.nfa_core_step(h,keys)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected,i
  if not d.nfa_core_capture_layer_info(h,info):continue
  split=(C.c_uint64*12)(*[77]*12)
  if d.nfa_core_capture_split(h,info[1],split):
   record=list(split);assert record[0]==info[0] and record[1]<record[2] and record[3]<record[4]==record[10]==info[1] and record[5]!=record[6] and 0<record[11]<160
   splits.append(record)
   for serial,page in ((record[1],record[5]),(record[2],record[6])):
    n=d.nfa_core_capture_owned_packet(h,record[0],serial,None,0);assert n>92
    buf=C.create_string_buffer(n);C.memset(buf,165,n)
    assert not d.nfa_core_capture_owned_packet(h,record[0],serial,buf,n-1) and buf.raw==bytes([165])*n
    assert d.nfa_core_capture_owned_packet(h,record[0],serial,buf,n)==n
    header=struct.unpack_from("<8I",buf.raw);assert header[4]==serial and header[7]==page and hashlib.sha256(buf.raw).hexdigest() in known_hashes
    owner_copies+=1
   assert not d.nfa_core_capture_owned_packet(h,record[0]+1000,record[1],None,0)
  else:assert list(split)==[77]*12
  C.memset(out,165,C.sizeof(out));before=bytes(out)
  if d.nfa_core_capture_pair(h,info[1],out):
   row=list(out);assert row[0]==info[0] and row[2]<row[6]==info[1] and row[3] in (0,1) and row[4]>0 and row[5]>0 and row[7]>0
   pairs.append(row)
   sentinel=(C.c_uint64*8)(*[77]*8)
   assert not d.nfa_core_capture_pair(h,row[2],sentinel) and list(sentinel)==[77]*8
  else:assert bytes(out)==before;rejected+=1
 assert pairs and splits,"No split joins observed"
 assert d.nfa_core_load_state(h,state,len(state));sentinel=(C.c_uint64*8)(*[77]*8)
 assert not d.nfa_core_capture_pair(h,pairs[-1][6],sentinel) and list(sentinel)==[77]*8
 assert not d.nfa_core_capture_owned_packet(h,splits[-1][0],splits[-1][1],None,0)
 split=(C.c_uint64*12)(*[77]*12);assert not d.nfa_core_capture_split(h,splits[-1][10],split) and list(split)==[77]*12
 assert d.nfa_core_capture_layers(h,0) and not d.nfa_core_capture_pair(h,1,out)
finally:d.nfa_core_close(h)
report={"result":"PASS_TWO_OWNER_SPLIT_DISPLAY_JOIN_HOST","original_frames":600,"accepted":len(pairs),"rejected":rejected,"pairs":pairs,"stale_reset_rejected":True,"failure_output_unchanged":True,"split_scene_support":True,"splits":splits,"split_count":len(splits),"owner_copies":owner_copies,"gpu_rendering":False}
a.report.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ("pairs","splits")}))
