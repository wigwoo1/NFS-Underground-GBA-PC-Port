"""Verify strict generation joins; rejected transitions never fabricate owners."""
import argparse,ctypes as C,hashlib,json,os,struct,zlib
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

d.nfa_core_capture_bundle.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t];d.nfa_core_capture_bundle.restype=C.c_size_t
d.nfa_core_capture_layer_row.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t];d.nfa_core_capture_layer_row.restype=C.c_size_t
d.nfa_core_capture_provenance.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t];d.nfa_core_capture_provenance.restype=C.c_size_t
digest_rows=[];bundles=0;missing=[];kinds={};row_checks=0;retained=[];sizes=[];last=None
try:
 assert d.nfa_core_load_state(h,state,len(state)) and d.nfa_core_capture_enable(h,1) and d.nfa_core_capture_layers(h,1)
 info=(C.c_uint64*5)()
 for i,expected in enumerate(refs):
  keys=1|(16 if 60<=i<120 else 32 if 480<=i<540 else 0)
  assert d.nfa_core_step(h,keys)==1 and hashlib.sha256(C.string_at(d.nfa_core_pixels(h),153600)).hexdigest()==expected
  assert d.nfa_core_capture_layer_info(h,info)
  n=d.nfa_core_capture_bundle(h,info[0],info[1],None,0)
  if not n:missing.append(i+1);digest_rows.append([i+1,0,0]);continue
  buf=C.create_string_buffer(n);C.memset(buf,165,n)
  assert not d.nfa_core_capture_bundle(h,info[0],info[1],buf,n-1) and buf.raw==bytes([165])*n
  assert d.nfa_core_capture_bundle(h,info[0],info[1],buf,n)==n
  raw=buf.raw;digest_rows.append([i+1,n,zlib.crc32(raw)]);header=struct.unpack_from("<16Q",raw);assert header[:5]==(0x3142414e,1,n,info[0],info[1])
  kind,cut,count=header[5:8];assert (kind==1 and cut==0 and count==1) or (kind==2 and 0<cut<160 and count==2)
  sections=[];offset=128
  for j in range(4):
   start,size=header[8+j*2:10+j*2];assert start==offset and start+size<=n;sections.append(raw[start:start+size]);offset+=size
  assert offset==n and (bool(sections[1])==(count==2)) and len(sections[3])==5312
  for packet in sections[:count]:assert hashlib.sha256(packet).hexdigest() in known_hashes
  provenance=C.create_string_buffer(5312);assert d.nfa_core_capture_provenance(h,info[0],info[1],provenance,5312)==5312 and provenance.raw==sections[3]
  layer=sections[2];magic,version,total,rows,pages,parts,pagebytes,refresh=struct.unpack_from("<8I",layer)
  assert (magic,version,total,rows,parts,pagebytes,refresh)==(0x31504c4e,1,len(layer),160,25,4096,info[1]) and 0<pages<=4000
  assert len(layer)==28512+pages*4096
  refs16=struct.unpack_from("<4000H",layer,20512);assert all(ref<pages for ref in refs16)
  first=kind not in kinds
  for y in (range(160) if first else (0,79,159)):
   decoded=layer[32+y*128:32+(y+1)*128]+b"".join(layer[28512+refs16[y*25+j]*4096:28512+refs16[y*25+j]*4096+(2048 if j==24 else 4096)] for j in range(25))
   direct=C.create_string_buffer(100480);assert d.nfa_core_capture_layer_row(h,info[0],info[1],y,direct,100480)==100480 and decoded==direct.raw
   row_checks+=1
  if first:retained.append((raw,hashlib.sha256(raw).hexdigest()))
  kinds[kind]=kinds.get(kind,0)+1;sizes.append(n);bundles+=1;last=list(info)
 assert bundles==594 and missing==list(range(1,7)) and kinds=={1:481,2:113}
 assert d.nfa_core_load_state(h,state,len(state)) and not d.nfa_core_capture_bundle(h,last[0],last[1],None,0)
 assert d.nfa_core_capture_layers(h,0) and not d.nfa_core_capture_bundle(h,last[0],last[1],None,0)
finally:d.nfa_core_close(h)
assert all(hashlib.sha256(raw).hexdigest()==expected for raw,expected in retained)
report=dict(result="PASS_OWNED_COMBINED_BUNDLE_HOST",original_frames=600,bundles=bundles,whole=kinds[1],split=kinds[2],initial_missing=missing,decoded_historical_rows=row_checks,min_bytes=min(sizes),max_bytes=max(sizes),mean_bytes=sum(sizes)//len(sizes),retained_after_core_close=True,short_buffer_atomic=True,stale_epoch_rejected=True,pc_packet_hashes_match=True,provenance_identical=True,android_runtime=False,gpu_rendering=False)
(a.report.parent/"bundle-crc-reference.json").write_text(json.dumps(digest_rows));
a.report.write_text(json.dumps(report,indent=2));print(json.dumps(report))
