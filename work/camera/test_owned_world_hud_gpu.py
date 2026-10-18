from pathlib import Path
import subprocess,json,hashlib,os,struct
from PIL import Image
p=Path('work/camera');checks=[]
for refresh in (8758,8762,8766,8769,8773,8776,8780):
 out=p/f'owned-world-hud-{refresh}.ppm';run=subprocess.run([str((p/'owned-wall-gpu-preview.exe').resolve()),str(p/f'motion-actual-scanline-assets/{refresh}-owned-frame.bin'),str(out)],capture_output=True,text=True)
 assert run.returncode==0,(refresh,run.stdout,run.stderr);im=Image.open(out);assert im.size==(3840,2160)
 checks.append(dict(refresh=refresh,gl_result=run.stdout.strip(),rgb_sha256=hashlib.sha256(im.tobytes()).hexdigest()))
raw=bytearray((p/'motion-actual-scanline-assets/8758-owned-frame.bin').read_bytes());import struct
gn=struct.unpack_from('<I',raw,8)[0];struct.pack_into('<I',raw,16+gn+159*34944,9999)
bad=p/'owned-frame-mismatched.bin';bad.write_bytes(raw);output=p/'owned-frame-rejected.ppm'
run=subprocess.run([str((p/'owned-wall-gpu-preview.exe').resolve()),str(bad),str(output)],capture_output=True,text=True);assert run.returncode==24 and not output.exists();assert 'native_gl' not in run.stderr
raw=bytearray((p/'motion-actual-scanline-assets/8758-owned-frame.bin').read_bytes());gn=struct.unpack_from('<I',raw,8)[0];colors=[]
for y in range(160):
 base=16+gn+y*34944;struct.pack_into('<H',raw,base+8,0x404);struct.pack_into('<3H',raw,base+8+0x50,0,0,0)
 color=(y*137)&32767;struct.pack_into('<H',raw,base+128+32768,color);colors.append(tuple(((color>>shift)&31)*8+(((color>>shift)&31)>>2) for shift in (0,5,10)))
packet=p/'owned-frame-backdrop-test.bin';packet.write_bytes(raw);output=p/'owned-frame-backdrop-test.ppm'
run=subprocess.run([str((p/'owned-wall-gpu-preview.exe').resolve()),str(packet),str(output)],capture_output=True,text=True,env={**os.environ,'NF_GPU_BACKGROUND_ONLY':'1'});assert run.returncode==0,run.stderr
im=Image.open(output)
for y,color in enumerate(colors):
 py=int((y+.5)*13.5);assert im.getpixel((1920,py))==color,(y,im.getpixel((1920,py)),color)
backdrop=dict(exact_owned_scanline_colors=160,scope='Synthetic changing owned BGR555 backdrop, no OBJ/global effects, checked actual native4KGPU output.')
r=dict(result='PASS_OWNED_WORLD_HUD_GPU_4K',checks=checks,backdrop=backdrop,scope='Seven offscreen raw world scenes plus original owned scanline OBJ/palette/OAM/effect snapshots through existing native HUD compositor. Bitmap text/sky/scene effects not complete; HUD vs original pixel parity and live timing remain unverified.')
(p/'owned-world-hud-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks))
