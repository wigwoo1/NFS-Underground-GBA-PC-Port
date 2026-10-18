"""Capture original-pose complete multimodel scenes for draw-order verification."""
from pathlib import Path
import ctypes as C,struct,json,hashlib
p=Path('work/camera').resolve();o=p.parents[1]/'outputs/nfsug-native-renderer/camera-research';rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');save=p.parent/'driving.state';hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,save)]
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p];assert crt._putenv(b'NF_LIVE_ROAD_ATTRIBUTES=1')==0
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);retained=[]
@Sink
def sink(ctx,epoch,ptr,size):
 h=struct.unpack('<8I',C.string_at(ptr,32));retained.append((epoch,h[4],h[5],h[6]));retained[:]=retained[-16:];return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t];d.nf_live_completed_models_count.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p];d.nf_live_completed_native_multimodel_world_classified_owned.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(save).encode(),0)
exports=[]
wall_cases=[c for c in json.loads((o/"original-multimodel-near-case-capture.json").read_text())["cases"] if c["case"]["kind"]==2];wall_checks=[]
d.nf_live_completed_visibility_pose.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p]
d.nf_live_completed_region_at.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
d.nf_live_completed_snapshot_read.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t]
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1);blob=C.create_string_buffer(rom.read_bytes());assert d.nf_live_visibility_enable(blob,len(blob)-1,16*1024*1024);d.nf_live_surface_audit_enable(1)
 for i in range(3583):d.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0))
 for identity in retained:
  wanted=[c for c in wall_cases if c['identity']==list(identity)]
  if wanted:
   pose=(C.c_uint*26)();assert d.nf_live_completed_visibility_pose(*identity,pose)
   for ordinal in range(64):
    result=(C.c_ubyte*(256+16+32*52+64*24))()
    if not d.nf_live_completed_region_at(*identity,pose,ordinal,result):continue
    data=bytes(result);region=struct.unpack_from('<H',data,256)[0];base,table=struct.unpack_from('<2I',data,16);descriptor=(C.c_ubyte*48)();assert d.nf_live_completed_snapshot_read(*identity,table+region*48,descriptor,48);first,count=struct.unpack_from('<2H',bytes(descriptor));assert count<=32
    for edge in range(count):
     source=base+(first+edge)*68
     for case in wanted:
      if source!=int(case['case']['source'],16):continue
      scratch=data[272+edge*52:272+(edge+1)*52];expected=bytes.fromhex(case['original']['scratch_hex']);wall_checks.append(dict(identity=identity,source=hex(source),region_ordinal=ordinal,edge=edge,exact_scratch=scratch==expected,differences=[i for i,(a,b) in enumerate(zip(scratch,expected)) if a!=b],native_scratch_hex=scratch.hex(),original_scratch_hex=expected.hex()))
   missing=[c for c in wanted if not any(r['identity']==identity and r['source']==c['case']['source'] for r in wall_checks)]
   if missing:
    Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_void_p,C.c_size_t)
    d.nf_live_completed_surface_identity.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_uint,C.c_void_p]
    d.nf_live_completed_object_region.argtypes=d.nf_live_completed_surface_identity.argtypes
    d.nf_live_completed_render_read.argtypes=d.nf_live_completed_snapshot_read.argtypes
    d.nfs_visibility_region_reconstruct.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
    reciprocal=(C.c_uint*32768).from_buffer_copy(rom.read_bytes()[0x627700:0x647700])
    for ordinal in range(256):
     ids=(C.c_uint*5)()
     if not d.nf_live_completed_surface_identity(*identity,ordinal,ids):break
     for case in missing:
      if ids[2]!=int(case['case']['source'],16):continue
      owned=(C.c_ubyte*184)();assert d.nf_live_completed_object_region(*identity,ordinal,owned)
      record=bytes(owned)[168:184];st=(C.c_ubyte*256)();assert d.nf_live_completed_render_read(*identity,ids[1],st,256)
      matrix=struct.unpack_from('<I',bytes(st),84)[0];view=bytes(pose)[56:104]
      @Read
      def read(ctx,address,dst,size):
       if not d.nf_live_completed_snapshot_read(*identity,address,dst,size):return 0
       lo=max(address,matrix);hi=min(address+size,matrix+48)
       if lo<hi:C.memmove(dst+lo-address,view[lo-matrix:hi-matrix],hi-lo)
       return 1
      scratch=(C.c_ubyte*(32*52))();stream=(C.c_ubyte*(64*24))();assert d.nfs_visibility_region_reconstruct(st,C.create_string_buffer(record),read,None,reciprocal,scratch,len(scratch),stream,len(stream))==1
      base,table=struct.unpack_from('<2I',bytes(st),16);region=struct.unpack_from('<H',record)[0];descriptor=(C.c_ubyte*48)();assert d.nf_live_completed_snapshot_read(*identity,table+region*48,descriptor,48);first,n=struct.unpack_from('<2H',bytes(descriptor))
      edge=(ids[2]-base)//68-first;assert 0<=edge<n;actual=bytes(scratch)[edge*52:(edge+1)*52];expected=bytes.fromhex(case['original']['scratch_hex']);wall_checks.append(dict(identity=identity,source=hex(ids[2]),object_surface_ordinal=ordinal,edge=edge,exact_scratch=actual==expected,differences=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b],native_scratch_hex=actual.hex(),original_scratch_hex=expected.hex()))
  count=C.c_uint();assert d.nf_live_completed_models_count(*identity,C.byref(count))
  if count.value<2:continue
  ptr=C.c_void_p();size=C.c_size_t();stage=C.c_uint();assert d.nf_live_completed_native_multimodel_world_classified_owned(*identity,C.byref(ptr),C.byref(size),C.byref(stage)),(identity,stage.value)
  try:
   b=C.string_at(ptr,size.value);path=p/f'source-order-multimodel-{identity[1]}.packet';path.write_bytes(b);exports.append(dict(identity=identity,models=count.value,path=str(path),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
  finally:d.nf_scene_packet_free(ptr)
finally:d.nf_close()
assert len(wall_checks)==5,(len(wall_checks),wall_checks)
(o/'multimodel-wall-near-scratch-verification.json').write_text(json.dumps(dict(result='PASS' if all(c['exact_scratch'] for c in wall_checks) else 'MISMATCH',cases=wall_checks,scope='Native retained original-pose region reconstruction versus actual original prepared near-clipped wall scratch; does not verify continuous GPU coverage'),indent=2))
assert exports and hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,save)]
(o/'source-order-multimodel-exports.json').write_text(json.dumps(dict(result='PASS',original_updates=3583,exports=exports,rom_state_unchanged=True,scope='Original-pose multimodel classified complete-scene export; no interpolated motion/60fps proof'),indent=2));print(len(exports),max(e['models'] for e in exports))
