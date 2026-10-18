exec(open('work/camera/test_obj_original_assets.py').read().split('frame=499;')[0])
oracle=C.CDLL(str(p/'obj-oracle.dll'));oracle.nf_obj_oracle.argtypes=[C.c_void_p]*3+[C.c_uint,C.c_void_p]
frame=499;v=(p/f'layer-inventory-{frame}-vram.bin').read_bytes();pal=(p/f'layer-inventory-{frame}-palette.bin').read_bytes();original=(p/f'layer-inventory-{frame}-oam.bin').read_bytes();display=0x1004|64;cases=0;pixels=0
for index in range(128):
 a,b,c,_=struct.unpack_from('<4H',original,index*8);a=(a&~255)|10;b=(b&~511)|80;o=bytearray(original)
 for j in range(128):struct.pack_into('<3H',o,j*8,512,0,0)
 struct.pack_into('<3H',o,index*8,a,b,c);out=(C.c_uint32*16384)();dims=(C.c_uint*2)();matrix=(C.c_int16*4)(*[struct.unpack_from('<h',original,((b>>9)&31)*32+6+j*8)[0] for j in range(4)])
 ok=aff(v,len(v),pal,len(pal),a,b,c,display,matrix,out,16384,dims) if a&256 else api(v,len(v),pal,len(pal),a,b,c,display,out,16384,dims)
 if not ok:continue
 ref=(C.c_uint32*(240*160))();assert oracle.nf_obj_oracle(v,pal,bytes(o),display,ref);backdrop=ref[0]&0xffffff;w,h=dims
 for y in range(h):
  for x in range(w):
   expected=(out[y*w+x]&0xffffff) if out[y*w+x] else backdrop;actual=ref[(y+10)*240+x+80]&0xffffff;assert actual==expected,(index,x,y,hex(actual),hex(expected));pixels+=1
 cases+=1
r=dict(result='PASS',original_oam_assets=cases,compared_pixels=pixels,scope='Isolatedone-spriteoriginalmGBAsoftwareoraclewithownedmemory; regular/affineoriginalassets,1Dlayout,blenddisabled;priority/window/blendnotverified');(p/'obj-original-oracle-tests.json').write_text(json.dumps(r,indent=2));print(r)
