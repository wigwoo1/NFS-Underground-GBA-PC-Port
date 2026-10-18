"""Explicit synthetic HUD effect/window stress fixture; geometry remains captured."""
from pathlib import Path
import argparse,struct,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();raw=a.input.read_bytes();chunks=[]
for i in range(4):off,size=struct.unpack_from('<QQ',raw,64+i*16);chunks.append(raw[off:off+size])
layer=bytearray(chunks[2]);provenance=bytearray(chunks[3]);pages=struct.unpack_from('<I',layer,16)[0];obj_page=pages;layer+=bytes([0x11])*1024+bytes([0x22])*3072
for y in range(160):
 old_ref=struct.unpack_from('<H',layer,20512+(y*25+24)*2)[0];page=bytearray(layer[28512+old_ref*4096:28512+(old_ref+1)*4096]);struct.pack_into('<H',page,0,((y*3)&31)|(((y*7)&31)<<5)|(((y*11)&31)<<10));struct.pack_into('<H',page,514,(y&31)|(((y+7)&31)<<5)|(((y+17)&31)<<10));struct.pack_into('<H',page,516,((31-y)&31)|(((y+13)&31)<<5)|(((y+3)&31)<<10))
 for i in range(128):struct.pack_into('<4H',page,1024+i*8,512,0,0,0)
 for i in range(2):
  mode=((y//2+i)%2);a0=((y-4)&255)|(mode<<10);b=(3<<14)|(8+i*40);c=(512+i*32)|(((y+i)%4)<<10);struct.pack_into('<3H',page,1024+i*8,a0,b,c)
 pal_page=pages+1+y;layer+=page;struct.pack_into('<H',layer,20512+(y*25+20)*2,obj_page);struct.pack_into('<H',layer,20512+(y*25+24)*2,pal_page);header=32+y*128;old_display=struct.unpack_from('<H',layer,header+8)[0];display=(old_display&16)|4|64|0x1000|0x6000|(0x400 if (y//16)%2 else 0);struct.pack_into('<H',layer,header+8,display);struct.pack_into('<H',layer,header+8+12,(y//4)%4);w0=(35<<8|35) if y%10==0 else (33<<8|113);win0=[63,31,47,4][(y//4)%4];win1=[4,63,31,47][(y//8)%4];outside=[63,31,47,4,0,32][(y//8)%6];
 if y==90:win0=31;outside=32
 struct.pack_into('<6H',layer,header+8+64,w0,200<<8|24,0x00a0,0x00a0,win0|(win1<<8),outside);effect=(y//32)%4;first=[0,4,16,32,20,36,48,52][(y//4)%8];second=[0,0x400,0x1000,0x2000,0x3400][(y//8)%5];struct.pack_into('<3H',layer,header+8+0x50,effect<<6|first|second,[0,0x0808,0x1010,0x1f1f][y%4],y%32);struct.pack_into('<Q',provenance,(24+y*4)*8,display)
struct.pack_into('<I',layer,16,pages+161);struct.pack_into('<I',layer,8,len(layer));out=bytearray(raw[:128])
for i,part in enumerate(chunks[:2]+[layer,provenance]):struct.pack_into('<QQ',out,64+i*16,len(out),len(part));out+=part
struct.pack_into('<Q',out,16,len(out));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(out);a.output.with_suffix('.json').write_text(json.dumps({'sha256':hashlib.sha256(out).hexdigest(),'synthetic_hud':True,'captured_geometry':True,'effect_modes':[0,1,2,3],'window_modes':['wrapped','empty','overlap'],'alpha_inputs':[0,0x0808,0x1010,0x1f1f],'brightness_inputs':'0..31,clamped16','per_row_obj_and_bg_priority':True,'source_ownership_header_updated':True},indent=2));print('Synthetic per-row HUD stress fixture ready')
