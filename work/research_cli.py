from pathlib import Path
import ctypes as C,argparse,json,hashlib,os
from PIL import Image
parser=argparse.ArgumentParser()
parser.add_argument('rom');parser.add_argument('--state');parser.add_argument('--frames',type=int,default=600);parser.add_argument('--keys',type=lambda v:int(v,0),default=0);parser.add_argument('--native',action='store_true')
a=parser.parse_args();root=Path(__file__).resolve().parents[1];out=root/'build/capture';out.mkdir(parents=True,exist_ok=True)
rom=Path(a.rom).resolve();state=Path(a.state).resolve() if a.state else None
os.chdir(out)
d=C.CDLL(str(root/'build/nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p
d.nf_capture.argtypes=[C.c_char_p];d.nf_polygons.argtypes=[C.c_char_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
if not d.nf_init(str(rom).encode(),b'display-writes.csv'):raise SystemExit('Unsupported or unreadable ROM')
if state and not d.nf_state(str(state).encode(),0):raise SystemExit('Snapshot load failed')
d.nf_native(a.native);d.nf_capture(b'spans.bin');d.nf_polygons(b'polygons.bin')
rows=[];flips=0;old=d.nf_read(0x04000000,2)&16
for f in range(a.frames):
 d.nf_frame(a.keys);q=d.nf_read(0x04000000,2);flips+=(q&16)!=old;old=q&16
 rows.append({'frame':f,'dispcnt':q,'pixels_sha256':hashlib.sha256(C.string_at(d.nf_pixels(),240*160*4)).hexdigest()})
Image.frombytes('RGBA',(240,160),C.string_at(d.nf_pixels(),240*160*4)).convert('RGB').save('screen.png')
for addr,n,name in [(0x03000000,0x8000,'iwram'),(0x02000000,0x40000,'ewram'),(0x06000000,0x18000,'vram'),(0x05000000,1024,'palette')]:d.nf_dump((name+'.bin').encode(),addr,n)
result={'frames':a.frames,'page_flips':flips,'native_calls':d.nf_native_calls(),'native_rejected':d.nf_native_rejected(),'cadence':rows}
Path('capture.json').write_text(json.dumps(result,indent=2));d.nf_close();print(f'Saved capture in {out}')
