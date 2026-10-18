from pathlib import Path
import ctypes as C,subprocess,struct,json,numpy as np
p=Path('work/camera').resolve();d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_layer_capture_row.argtypes=[C.c_uint,C.c_void_p,C.c_uint]
rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
assert d.nf_init(rom,b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 for i in range(499):d.nf_frame(1|(32 if i>=180 else 0))
 assert d.nf_layer_capture_arm();d.nf_frame(33);assert d.nf_layer_capture_status()==3
 buf=C.create_string_buffer(100480);rows=[]
 for y in range(160):
  assert d.nf_layer_capture_row(y,buf,100480);b=buf.raw;rows.append(b[:128]+b[128+0x10000:])
finally:d.nf_close()
reports=[]
for case in ('captured','effect_bands'):
 inputs=[bytearray(b) for b in rows]
 if case=='effect_bands':
  for y,b in enumerate(inputs):
   struct.pack_into('<H',b,8+0x50,0x3f3f|((y//7%2)<<6));struct.pack_into('<H',b,8+0x52,(y%17)|((16-y%17)<<8));struct.pack_into('<H',b,8+12,y//11%4);struct.pack_into('<H',b,128+32768,(y*193)&32767)
 source=p/f'hud-batch-{case}.bin';source.write_bytes(b''.join(inputs));outputs=[]
 for variant in ('reference','batched'):
  target=p/f'hud-batch-{case}-{variant}.rgba';subprocess.check_call([str(p/f'hud-gpu-{variant}.exe'),str(source),str(target)]);outputs.append(np.fromfile(target,np.uint32)&0xffffff)
 diff=outputs[0]!=outputs[1];assert not diff.any(),(case,int(diff.sum()),np.flatnonzero(diff)[:8].tolist());reports.append(dict(case=case,checked_pixels=3840*2160))
r=dict(result='PASS',samples=reports,scope='Exact4Koutput before/after candidate row assembly and effect batching for actual scanline-owned refresh500 plus changing per-row effect/backdrop/priority inputs; no gameplay timing proof');(p/'hud-batching-tests.json').write_text(json.dumps(r,indent=2));print(r)
