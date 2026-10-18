from pathlib import Path
import ctypes as C,struct,json,hashlib
from PIL import Image,ImageDraw
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));api=d.nf_obj_image;api.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]+[C.c_uint16]*4+[C.c_void_p,C.c_size_t,C.c_void_p]
aff=d.nf_obj_affine_image;aff.argtypes=api.argtypes[:8]+[C.c_void_p]+api.argtypes[8:]
frame=499;v=(p/f'layer-inventory-{frame}-vram.bin').read_bytes();pal=(p/f'layer-inventory-{frame}-palette.bin').read_bytes();oam=(p/f'layer-inventory-{frame}-oam.bin').read_bytes();display=struct.unpack_from('<H',(p/f'layer-inventory-{frame}-register-shadow.bin').read_bytes())[0];images=[];rejected=[]
for index in range(128):
 a,b,c,_=struct.unpack_from('<4H',oam,index*8);out=(C.c_uint32*16384)();dims=(C.c_uint*2)()
 matrix=(C.c_int16*4)(*[struct.unpack_from('<h',oam,((b>>9)&31)*32+6+j*8)[0] for j in range(4)])
 ok=aff(v,len(v),pal,len(pal),a,b,c,display,matrix,out,16384,dims) if a&256 else api(v,len(v),pal,len(pal),a,b,c,display,out,16384,dims)
 if not ok:rejected.append(index);continue
 w,h=dims;raw=bytes(out)[:w*h*4];im=Image.frombytes('RGBA',(w,h),raw)
 if not im.getbbox():continue
 images.append((index,im,dict(index=index,width=w,height=h,mode=(a>>10)&3,x=b&511,y=a&255,tile=c&1023,sha256=hashlib.sha256(raw).hexdigest())))
sheet=Image.new('RGB',(1024,((len(images)+7)//8)*150),(35,35,35));draw=ImageDraw.Draw(sheet)
for j,(index,im,_) in enumerate(images):
 x=(j%8)*128;y=(j//8)*150;im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);sheet.paste(im,(x,y),im);draw.text((x+4,y+132),str(index),fill='white')
sheet.save(p/'obj-original-assets-contact.png');report=dict(result='DECODED',scope='Native regularandaffineOBJassetsfromcapturedoriginalOAM/VRAM/palette; window/blend/prioritycompositionnotrendered',refresh=frame+1,decoded_nontransparent=len(images),rejected_indices=rejected,assets=[x[2] for x in images]);(p/'obj-original-assets-tests.json').write_text(json.dumps(report,indent=2));print(len(images),len(rejected))
