from pathlib import Path
import struct,subprocess,json,numpy as np
p=Path('work/camera').resolve();data=(p/'hud-batch-captured.bin').read_bytes();reports=[]
for case in range(5):
 rows=[]
 for y in range(160):
  row=bytearray(data[y*34944:(y+1)*34944]);effect=y//8%4;targets=(y*197+case*907)&0x3f3f
  struct.pack_into('<H',row,88,targets|(effect<<6));struct.pack_into('<H',row,90,(y%32)|(((y+case*7)%32)<<8));struct.pack_into('<H',row,92,(y+case*3)%32);struct.pack_into('<H',row,20,y//5%4)
  if case==4:
   row[128:32896]=bytes(32768);row[33920:34944]=bytes(1024)
   for i in range(128):struct.pack_into('<H',row,33920+i*8,512)
   struct.pack_into('<3H',row,33920,40,32,512|(3<<10));struct.pack_into('<3H',row,33928,40|0x400,32,514)
   row[128+0x4000:128+0x4020]=bytes([0x11])*32;struct.pack_into('<H',row,32896+514,31)
   struct.pack_into('<H',row,88,0x10|((y%4)<<6)|(0x400 if y&1 else 0));struct.pack_into('<H',row,20,0)
  rows.append(row)
 source=p/f'hud-brightness-{case}.bin';source.write_bytes(b''.join(rows));target=p/f'hud-brightness-{case}.rgba';ref=p/f'hud-brightness-{case}-cpu.rgba'
 subprocess.check_call([str(p/'hud-gpu-batched.exe'),str(source),str(target),str(ref)])
 actual=np.fromfile(target,np.uint32).reshape(2160,3840)[::-1]&0xffffff;expected=np.fromfile(ref,np.uint32).reshape(2160,3840)&0xffffff;diff=actual!=expected
 assert not diff.any(),(case,int(diff.sum()),np.argwhere(diff)[:8].tolist())
 reports.append(dict(case=case,checked_pixels=3840*2160))
r=dict(result='PASS',samples=reports,scope='Prepared scanline HUD GPU effects vs full native candidate and composition oracle, all four effects/targets/coefficients, captured sprites and adversarial transparent higher-priority semi sprite retaining preprocessed lower color; synthetic native background, not physical scanout')
(p/'hud-brightness-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r)
