import runpy,ctypes as C,json
from pathlib import Path
ns=runpy.run_path('work/camera/test_decoded_palette_table_captured_candidate.py');materials=ns['materials'];libs=ns['libs'];w,h,stride,source,palette,tr=materials[0];source=bytearray(source);palette=bytearray(palette);src=(C.c_uint8*len(source)).from_buffer(source);pal=(C.c_uint8*len(palette)).from_buffer(palette);checked=0
try:
 for change in range(4):
  if change==1:source[0]=(source[0]+1)%256
  if change==2:palette[source[0]*2]^=31
  transparent=change==3;out=[]
  for d in libs:
   buf=C.create_string_buffer(w*h*4);assert d.decode(w,h,stride,src,pal,transparent,buf,len(buf))==1;out.append(buf.raw)
  assert out[0]==out[1]
  i=source[0];color=int.from_bytes(palette[i*2:i*2+2],'little');rgba=bytes([((color>>(k*5)&31)<<3)|(color>>(k*5)&31)>>2 for k in range(3)]+[0 if transparent and not i else 255]);assert out[0][:4]==rgba;checked+=1
 for d in libs:
  assert d.decode(1025,h,stride,src,pal,0,C.create_string_buffer(4),4)==0
finally:
 for d in libs:
  d.clear();v=(C.c_uint64*3)();d.nf_owned_decoded_texture_stats(v);assert v[2]==0
out=dict(result='PASS_PALETTE_TABLE_MUTATION_OWNERSHIP',mutations=checked,invalid_dimension_rejected=True,cleared_bytes_zero=True,scope='Captured mutable source/palette with unchanged addresses and transparency-key changes; exact32/64 RGBA and independent first-pixel oracle. No renderer timing or full4K proof.')
Path('work/camera/prototype-runs/decoded-palette-table-mutation-20261009.json').write_text(json.dumps(out,indent=2));print(out)
