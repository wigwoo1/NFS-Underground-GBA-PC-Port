from pathlib import Path
import ctypes as C,json,hashlib
root=Path('work').resolve();rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
def run(path,research,state):
 d=C.CDLL(str(path));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];packets=[]
 @Sink
 def receive(user,epoch,ptr,size):packets.append(hashlib.sha256(C.string_at(ptr,size)).hexdigest());return 1
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(root/state).encode(),0)
 try:
  assert d.nf_native_scene_sink(receive,None)
  if research:
   d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t];data=rom.read_bytes();buf=C.create_string_buffer(data);assert d.nf_live_visibility_enable(buf,len(data),16*1024*1024);d.nf_live_surface_audit_enable(1)
  checkpoints=[]
  for frame in range(300):
   # Initial known route, then alternating steering and acceleration-only windows.
   keys=1|(32 if 180<=frame<500 or 1200<=frame<1450 else 16 if 500<=frame<720 or 2000<=frame<2250 else 0)
   d.nf_frame(keys)
   if research and (frame+1)%300==0:
    stats=(C.c_uint32*3)();d.nf_live_billboard_stats(stats);checkpoints.append(dict(refresh=frame+1,counters=list(stats)));print(checkpoints[-1],flush=True)
  hashes=[]
  for address,size in [(0x02000000,0x40000),(0x03000000,0x8000),(0x06000000,0x18000)]:
   path=root/'camera'/('billboard-coverage-'+('research' if research else 'control')+f'-{address:x}.bin');d.nf_dump(str(path).encode(),address,size);hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
  return packets,hashes,checkpoints
 finally:d.nf_close()
results=[]
for state in ['race.state','latest.state','integration-0.state','fix-menu/stage-10.state']:
 a=run(root/'nfsprobe.dll',False,state);b=run(root/'camera/visibility-probe.dll',True,state);assert a[:2]==b[:2],(state,len(a[0]),len(b[0]))
 results.append(dict(state=state,refreshes=300,packets=len(b[0]),identical=True,billboard_checkpoints=b[2]));print(results[-1],flush=True)
report=dict(result='PASS',scenes=results,scope='Read-only saved-scene probes; counters cumulative within process, no motion-quality claim.')
(root/'camera/billboard-alternate-coverage-tests.json').write_text(json.dumps(report,indent=2));print(report)
