from pathlib import Path
import struct,subprocess,os,json
from PIL import Image
p=Path('work/camera');checks=[]
for refresh in (8758,8762,8766,8769,8773,8776,8780):
 a=p/'motion-actual-scanline-assets';old=(a/f'{refresh}-owned-frame.bin').read_bytes();magic,r,gn,hn=struct.unpack_from('<4I',old);assert r==refresh
 image=(a/f'{refresh}-background-image.bin').read_bytes();mask=(a/f'{refresh}-background-coverage.bin').read_bytes()
 raw=bytearray(struct.pack('<5I',0x3246474e,r,gn,hn,76800)+old[16:]+image+mask)
 assert (a/f'{refresh}-owned-background-frame.bin').read_bytes()==raw,('live frame vs independent source coverage',refresh)
 # Disable OBJ/effects to isolate background GPU pixels, preserve historical palettes.
 for y in range(160):
  base=20+gn+y*34944;struct.pack_into('<H',raw,base+8,0x404);struct.pack_into('<3H',raw,base+8+0x50,0,0,0)
 packet=a/f'{refresh}-background-test-frame.bin';packet.write_bytes(raw);out=p/f'owned-background-{refresh}.ppm'
 run=subprocess.run([str((p/'owned-wall-gpu-preview.exe').resolve()),str(packet),str(out)],capture_output=True,text=True,env={**os.environ,'NF_GPU_BACKGROUND_ONLY':'1'});assert run.returncode==0,(run.returncode,run.stderr)
 im=Image.open(out)
 for y in range(160):
  for x in range(240):
   index=image[y*240+x] if mask[y*240+x] else 0
   c=struct.unpack_from('<H',raw,20+gn+y*34944+128+32768+index*2)[0];rgb=tuple(((c>>k)&31)*8+(((c>>k)&31)>>2) for k in (0,5,10))
   assert im.getpixel((int(300+(x+.5)*13.5),int((y+.5)*13.5)))==rgb,(refresh,x,y)
 checks.append(dict(refresh=refresh,exact_pixel_centers=38400))
 (a/f'{refresh}-owned-background-frame.bin').write_bytes(struct.pack('<5I',0x3246474e,r,gn,hn,76800)+old[16:]+image+mask)
report=dict(result='PASS_OWNED_BACKGROUND_GPU',checks=checks,scope='All source pixel centers at 4K; unowned stale rows leave backdrop intact. Diagnostic frame consumer only.')
(p/'owned-background-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
