from pathlib import Path
import ctypes as C,json,hashlib
root=Path('work').resolve();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
def run(path,research):
 d=C.CDLL(str(path));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];packets=[]
 @Sink
 def receive(user,epoch,ptr,size):packets.append(hashlib.sha256(C.string_at(ptr,size)).hexdigest());return 1
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
 try:
  assert d.nf_native_scene_sink(receive,None)
  if research:
   d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t];data=rom.read_bytes();buf=C.create_string_buffer(data);assert d.nf_live_visibility_enable(buf,len(data),16*1024*1024);d.nf_live_surface_audit_enable(1)
  checkpoints=[]
  for frame in range(3000):
   # Initial known route, then alternating steering and acceleration-only windows.
   keys=1|(32 if 180<=frame<500 or 1200<=frame<1450 else 16 if 500<=frame<720 or 2000<=frame<2250 else 0)
   d.nf_frame(keys)
   if research and (frame+1)%500==0:
    stats=(C.c_uint32*3)();d.nf_live_billboard_stats(stats);checkpoints.append(dict(refresh=frame+1,counters=list(stats)));print(checkpoints[-1],flush=True)
  hashes=[]
  for address,size in [(0x02000000,0x40000),(0x03000000,0x8000),(0x06000000,0x18000)]:
   path=root/'camera'/('billboard-coverage-'+('research' if research else 'control')+f'-{address:x}.bin');d.nf_dump(str(path).encode(),address,size);hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
  return packets,hashes,checkpoints
 finally:d.nf_close()
a=run(root/'nfsprobe.dll',False);b=run(root/'camera/visibility-probe.dll',True);assert a[:2]==b[:2],(len(a[0]),len(b[0]))
report=dict(result='PASS',refreshes=3000,scene_packets=len(b[0]),packet_hashes_and_final_ram_identical=True,billboard_checkpoints=b[2],scope='Extended scripted driving from existing state; no other tracks/menus or motion-quality claim.')
(root/'camera/billboard-coverage-tests.json').write_text(json.dumps(report,indent=2));print(report)
