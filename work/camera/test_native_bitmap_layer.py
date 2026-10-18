import ctypes as C,struct,json
from pathlib import Path
p=Path(__file__).resolve().parent
class Glyph(C.Structure):_fields_=[(n,C.c_uint32) for n in ['width','height','draw_width','stride','flags','transparent','palette_offset']]
d=C.CDLL(str(p/'bitmap-layer.dll'));P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t
d.nf_bitmap_layer_create.argtypes=[U];d.nf_bitmap_layer_create.restype=P;d.nf_bitmap_layer_destroy.argtypes=[P];d.nf_bitmap_layer_glyph.argtypes=[P,U,C.c_uint32,C.POINTER(Glyph),P,Z];d.nf_bitmap_layer_plane.argtypes=[P,U,C.c_uint,P,P,Z];d.nf_bitmap_layer_invalidate.argtypes=[P,U,C.c_uint32,Z];d.nf_bitmap_layer_reset.argtypes=[P,U]
s=d.nf_bitmap_layer_create(7);assert s;expected=[bytearray(38400),bytearray(38400)];coverage=[bytearray(38400),bytearray(38400)];raw=(p/'prototype-runs/selection-motion-75af1f8d57734eeeba6768da9af1a943-bitmap-blits.csv.glyphs.bin').read_bytes();off=0;count=0
try:
 while off<len(raw):
  h=struct.unpack_from('<16I',raw,off);off+=64;frame,pc,descriptor,glyph,dest,stride,pal,w,height,dw,flags,transparent,source,size,lr,target=h;asset=raw[off:off+size];off+=size;g=Glyph(w,height,dw,stride,flags,transparent,pal);a=C.create_string_buffer(asset);assert d.nf_bitmap_layer_glyph(s,7,dest,C.byref(g),a,size);C.memset(a,0,size);page=int(dest>=0x0600a000);base=dest-(0x06000000+page*0xa000)
  for y in range(height):
   for x in range(dw):
    value=asset[y*w+x]
    if not(flags&1 and value==transparent):expected[page][base+y*stride+x]=(value+pal)&255;coverage[page][base+y*stride+x]=1
  count+=1
 for page in range(2):
  a=C.create_string_buffer(38400);b=C.create_string_buffer(38400);assert d.nf_bitmap_layer_plane(s,7,page,a,b,38400);assert a.raw==expected[page] and b.raw==coverage[page]
 d.nf_bitmap_layer_changed_mask.argtypes=[P,U,C.c_uint32,C.c_uint32,C.c_uint];checks=0
 for page in range(2):
  for offset in range(0,38400,4):
   value=int.from_bytes(expected[page][offset:offset+4],'little');address=0x06000000+page*0xa000+offset
   assert d.nf_bitmap_layer_changed_mask(s,7,address,value,4)==0
   wanted=sum((1<<i) for i in range(4) if coverage[page][offset+i])
   assert d.nf_bitmap_layer_changed_mask(s,7,address,value^0xffffffff,4)==wanted
   checks+=2
 assert d.nf_bitmap_layer_changed_mask(s,8,0x06000000,0xffffffff,4)==0
 assert d.nf_bitmap_layer_changed_mask(s,7,0x06000000,0xffffffff,5)==0
 sentinel=C.create_string_buffer(b'Q'*38400,38400);mask=C.create_string_buffer(b'R'*38400,38400);assert not d.nf_bitmap_layer_plane(s,8,0,sentinel,mask,38400) and sentinel.raw==b'Q'*38400 and mask.raw==b'R'*38400
 assert d.nf_bitmap_layer_invalidate(s,7,0x06000000,0x14000)
 for page in range(2):
  assert d.nf_bitmap_layer_plane(s,7,page,sentinel,mask,38400) and not any(mask.raw)
 assert d.nf_bitmap_layer_reset(s,9) and not d.nf_bitmap_layer_plane(s,7,0,sentinel,mask,38400)
finally:d.nf_bitmap_layer_destroy(s)
r={'result':'PASS','owned_glyph_commands':count,'covered_store_checks':checks,'two_page_indices_and_coverage_exact':True,'source_buffer_mutation_safe':True,'clear_and_epoch_rejection':True,'scope':'Owned native glyph-plane and changed-store mask component verification; live renderer timing is tested separately.'};(p/'prototype-runs/native-bitmap-layer-verification.json').write_text(json.dumps(r,indent=2));print(r)
