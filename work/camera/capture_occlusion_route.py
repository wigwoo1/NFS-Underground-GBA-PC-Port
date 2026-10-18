"""Read-only original updates, diverse steering, owned original-pose snapshots."""
import ctypes as C,hashlib,json,struct,uuid
from pathlib import Path
p=Path(__file__).resolve().parent;prefix=p/'prototype-runs'/('occlusion-route-'+uuid.uuid4().hex)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state'
hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p];assert crt._putenv(b'NF_LIVE_ROAD_ATTRIBUTES=1')==0
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int]
d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);latest=[]
@Sink
def sink(ctx,epoch,ptr,size):
 h=struct.unpack('<8I',C.string_at(ptr,32));latest[:]=[(epoch,h[4],h[5],h[6])];return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
d.nf_live_completed_native_multimodel_world_classified_owned.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
exports=[];ledger=[]
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 blob=C.create_string_buffer(rom.read_bytes());assert d.nf_live_visibility_enable(blob,len(blob)-1,16*1024*1024);d.nf_live_surface_audit_enable(1)
 for i in range(6000):
  steering=32 if i%1200 in range(180,500) else 16 if i%1200 in range(500,720) else 0
  keys=1|steering;d.nf_frame(keys);ledger.append(keys)
  if (i+1)%250 or not latest:continue
  identity=latest[0];ptr=C.c_void_p();size=C.c_size_t();stage=C.c_uint()
  assert d.nf_live_completed_native_multimodel_world_classified_owned(*identity,C.byref(ptr),C.byref(size),C.byref(stage)),(i,identity,stage.value)
  try:data=C.string_at(ptr,size.value)
  finally:d.nf_scene_packet_free(ptr)
  path=Path(str(prefix)+f'-{i+1:04d}.packet');path.write_bytes(data)
  exports.append(dict(original_updates=i+1,identity=identity,path=str(path),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  d.nf_dump(str(prefix).encode()+('-'+name+'.bin').encode(),base,size)
finally:d.nf_close()
baseline=C.CDLL(str(p.parent/'nfsprobe.dll'));baseline.nf_init.argtypes=[C.c_char_p]*2;baseline.nf_state.argtypes=[C.c_char_p,C.c_int];baseline.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
assert baseline.nf_init(str(rom).encode(),b'') and baseline.nf_state(str(state).encode(),0)
ram_checks=[]
try:
 for keys in ledger:baseline.nf_frame(keys)
 for name,base,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=Path(str(prefix)+'-replay-'+name+'.bin');baseline.nf_dump(str(path).encode(),base,size)
  actual=Path(str(prefix)+'-'+name+'.bin').read_bytes();expected=path.read_bytes()
  assert len(actual)==len(expected)==size and actual==expected,name+' original RAM mismatch'
  ram_checks.append(dict(region=name,bytes=size,sha256=hashlib.sha256(actual).hexdigest(),exact_original_ram=True))
finally:baseline.nf_close()
assert hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
report=dict(result='PASS',original_updates=6000,exports=exports,input_keys=ledger,rom_state_sha256=hashes,ram_checks=ram_checks,exact_original_ram=True,scope='Owned complete original-pose scenes every250 original updates on periodic steering route; stable bridge independently replays all inputs and compares complete RAM. This offscreen extraction is not live timing/motion proof.')
target=Path(str(prefix)+'-exports.json');target.write_text(json.dumps(report,indent=2));print(target,flush=True)
