import ctypes as C,struct,json
from pathlib import Path
from PIL import Image
p=Path('work/camera');base=p/'prototype-runs/selection-motion-2d5c10231bc24bf2abfc18d19cbfc694';raw=Path(str(base)+'-original-full-3620.bin').read_bytes();original=Path(str(base)+'-original-pixels-3620.bin').read_bytes();d=C.CDLL(str((p/'obj-tile-held-audit.dll').resolve()));P=C.c_void_p;Z=C.c_size_t;H=C.c_uint16;U=C.c_uint;f=d.nf_obj_mode4_window_scanline;f.argtypes=[P,Z,P,Z,P,Z,H,H,H,H,H,P,P,U,P];decoded=bytearray();background=bytearray()
for y in range(160):
 r=raw[y*100480:(y+1)*100480];regs=r[8:104];v=C.create_string_buffer(r[128:128+0x18000]);pal=C.create_string_buffer(r[128+0x18000:128+0x18000+1024]);o=C.create_string_buffer(r[-1024:]);matrix=(C.c_int32*6)(*struct.unpack_from('<6i',r,104));win=(H*6)(*struct.unpack_from('<6H',regs,64));out=(U*240)();display=struct.unpack_from('<H',regs)[0];bg=struct.unpack_from('<H',regs,12)[0];blend,alpha,bright=struct.unpack_from('<3H',regs,80);assert f(v,0x18000,pal,1024,o,1024,display,bg,blend,alpha,bright,matrix,win,y,out);decoded.extend(bytes(out));assert f(v,0x18000,pal,1024,o,1024,display&~0x1000,bg,blend,alpha,bright,matrix,win,y,out);background.extend(bytes(out))
changes=[i for i in range(38400) if decoded[i*4:i*4+3]!=original[i*4:i*4+3]];report={'decoded_rows':160,'RGB_mismatched_pixels':len(changes),'top_mismatches':sum(i//240<32 for i in changes),'bottom_mismatches':sum(i//240>=144 for i in changes),'scope':'CPU complete original mode4 source composition versus captured original display; diagnostic only'};print(report);(p/'prototype-runs/held-full-composition-audit.json').write_text(json.dumps(report,indent=2));Image.frombytes('RGBA',(240,160),bytes(decoded)).resize((960,640)).save(p/'prototype-runs/held-full-composition-cpu.png')

Image.frombytes('RGB',(240,160),bytes(c for i,c in enumerate(background) if i%4!=3)).resize((960,640)).save(p/'prototype-runs/held-background-only.png')
regions={}
for name,(x0,y0,x1,y1) in {'header':(0,0,75,12),'label':(75,30,165,40)}.items():
 regions[name]={'background_matches_full':sum(background[(y*240+x)*4:(y*240+x)*4+3]==decoded[(y*240+x)*4:(y*240+x)*4+3] for y in range(y0,y1) for x in range(x0,x1)), 'pixels':(x1-x0)*(y1-y0)}
(p/'prototype-runs/held-label-layer-isolation.json').write_text(json.dumps(regions,indent=2));print(regions)
