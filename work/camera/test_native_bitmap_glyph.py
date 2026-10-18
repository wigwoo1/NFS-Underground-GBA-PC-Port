import ctypes as C,struct,csv,json
from pathlib import Path
p=Path(__file__).resolve().parent
class Glyph(C.Structure):_fields_=[(n,C.c_uint32) for n in ['width','height','draw_width','stride','flags','transparent','palette_offset']]
d=C.CDLL(str(p/'bitmap-glyph.dll'));f=d.nf_bitmap_glyph_decode;f.argtypes=[C.POINTER(Glyph),C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_size_t]
base=p/'prototype-runs/selection-motion-75af1f8d57734eeeba6768da9af1a943-bitmap-blits.csv';raw=Path(str(base)+'.glyphs.bin').read_bytes();off=0;pred=[];calls=0
while off<len(raw):
 h=struct.unpack_from('<16I',raw,off);off+=64;frame,pc,descriptor,glyph,dest,stride,pal,w,hh,draw,flags,transparent,source,size,lr,target=h;asset=raw[off:off+size];off+=size;g=Glyph(w,hh,draw,stride,flags,transparent,pal);a=C.create_string_buffer(asset);indices=C.create_string_buffer(size);coverage=C.create_string_buffer(size);assert f(C.byref(g),a,size,indices,coverage,size);calls+=1
 for i,write in enumerate(coverage.raw):
  if write:pred.append((dest+(i//w)*stride+i%w,source+i,asset[i],pal,indices.raw[i]))
actual=[]
for r in csv.DictReader(base.open()):
 pixel=int(r['pixel_address'],16);actual.append((pixel,int(r['source'],16),int(r['source_index']),int(r['palette_offset']),(int(r['value'],16)>>(8*(pixel&1)))&255))
assert pred==actual
valid=Glyph(2,2,2,240,1,0,255);a=C.create_string_buffer(bytes([0,1,2,255]));x=C.create_string_buffer(b'Q'*4,4);y=C.create_string_buffer(b'R'*4,4);assert f(C.byref(valid),a,4,x,y,4);assert x.raw==bytes([0,0,1,254]) and y.raw==bytes([0,1,1,1])
rejects=0
for field,value in [('width',0),('width',257),('height',257),('draw_width',3),('stride',1),('flags',2),('transparent',256),('palette_offset',256)]:
 g=Glyph(2,2,2,240,1,0,0);setattr(g,field,value);x=C.create_string_buffer(b'Q'*4,4);y=C.create_string_buffer(b'R'*4,4);assert not f(C.byref(g),a,4,x,y,4) and x.raw==b'Q'*4 and y.raw==b'R'*4;rejects+=1
report={'result':'PASS','native_glyphs':calls,'exact_original_ordered_pixel_writes':len(actual),'atomic_rejection_cases':rejects,'palette_wrap_test':True,'scope':'native asset decoding only; completion/page timing and GPU transport not integrated'};(p/'prototype-runs/native-bitmap-glyph-verification.json').write_text(json.dumps(report,indent=2));print(report)
