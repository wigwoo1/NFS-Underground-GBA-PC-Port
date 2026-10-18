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

d.nfa_core_capture_provenance.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t];d.nfa_core_capture_provenance.restype=C.c_size_t
observations=[];flags=[];verified=0;last=None
try:
 assert d.nfa_core_load_state(h,state,len(state)) and d.nfa_core_capture_enable(h,1) and d.nfa_core_capture_layers(h,1)
 info=(C.c_uint64*5)();whole=(C.c_uint64*8)();split=(C.c_uint64*12)()
 stream=(a.report.parent/"provenance.bin").open("wb")
 for i,expected in enumerate(refs):
  keys=1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0)
  assert d.nfa_core_step(h,keys)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected
  assert d.nfa_core_capture_layer_info(h,info)
  n=d.nfa_core_capture_provenance(h,info[0],info[1],None,0);assert n==5312
  buf=C.create_string_buffer(n);C.memset(buf,165,n)
  assert not d.nfa_core_capture_provenance(h,info[0],info[1],buf,n-1) and buf.raw==bytes([165])*n
  assert d.nfa_core_capture_provenance(h,info[0],info[1],buf,n)==n
  assert not d.nfa_core_capture_provenance(h,info[0]+1000,info[1],None,0)
  assert not d.nfa_core_capture_provenance(h,info[0],info[1]+100000,None,0)
  words=struct.unpack("<664Q",buf.raw);assert list(words[:5])==list(info) and words[6:8]==(160,1)
  stream.write(buf.raw);last=list(info)
  rows=[words[24+y*4:28+y*4] for y in range(160)]
  candidates=[]
  for index in range(2):
   meta=words[8+index*8:16+index*8]
   if not meta[7]:candidates.append(dict(present=False));continue
   epoch,serial,begin,end,page,generation,version,present=meta
   display=all((row[0]&7)==4 and not (row[0]&128) and ((row[0]>>4)&1)==page for row in rows)
   versions=all(row[3]==version==words[5] for row in rows)
   generations=all(row[1+page]==generation for row in rows)
   candidates.append(dict(present=True,serial=serial,end=end,page=page,generation=generation,version=version,full_page=display,audit_matches=versions,all_generations_match=generations,after_end=info[1]>end,equal_end=info[1]==end,row_generation_first=rows[0][1+page],row_generation_last=rows[-1][1+page]))
  accepted=bool(d.nfa_core_capture_display_owner(h,info[1],whole));splitok=bool(d.nfa_core_capture_split(h,info[1],split))
  independent=sum(c.get("present") and c.get("full_page") and c.get("audit_matches") and c.get("all_generations_match") and (c.get("after_end") or c.get("equal_end")) for c in candidates)
  assert accepted==(independent==1)
  if not accepted and not splitok:observations.append(dict(step=i+1,refresh=info[1],owners=candidates))
  verified+=1
 stream.close()
 assert d.nfa_core_load_state(h,state,len(state)) and not d.nfa_core_capture_provenance(h,last[0],last[1],None,0)
finally:d.nfa_core_close(h)
report=dict(result="PASS_HISTORICAL_PROVENANCE_HOST",frames_verified=verified,bytes_each=5312,independent_owner_decisions=True,short_buffer_atomic=True,stale_epoch_rejected=True,unavailable=len(observations),observations=observations)
a.report.write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!="observations"}))
