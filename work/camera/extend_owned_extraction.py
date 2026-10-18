from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text().replace('candidate_sources=[];candidate_palettes=[]','candidate_sources=[];candidate_palettes=[];candidate_extractions=[];earlier_identity=None')
s=s.replace('d.nf_live_palette_draw.argtypes=sig+[C.c_void_p]','''d.nf_live_palette_draw.argtypes=sig+[C.c_void_p]
d.nf_live_completed_surface_arguments.argtypes=sig
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d.nf_extract_wall.argtypes=[Read,C.c_void_p]+[C.c_uint32]*6+[C.c_void_p]*4
d.nf_surface_free.argtypes=[C.c_void_p]''')
s=s.replace('global previous,last','global previous,last,earlier_identity')
s=s.replace('current={};ordinal=0','''if h[4]==140:earlier_identity=(epoch,h[4],h[5],h[6])
  current={};ordinal=0''')
s=s.replace('assert d.nf_live_completed_texture_provenance(*args,p)','''assert d.nf_live_completed_texture_provenance(*args,p)
   if h[4]==141 and tuple(ident)==(2,50331840,139937176,37,0):
    captured=(C.c_uint32*6)();assert d.nf_live_completed_surface_arguments(*args,captured)
    def earlier_read(address,size):
     data=C.create_string_buffer(size);assert d.nf_live_completed_snapshot_read(*earlier_identity,address,data,size);return data.raw
    st=earlier_read(captured[0],256);src=earlier_read(captured[2],68);base=struct.unpack_from('<H',src,44)[0];mb=struct.unpack_from('<I',st,32)[0]
    mat=earlier_read(mb+base*32,32);an=earlier_read(struct.unpack_from('<I',st,72)[0]+struct.unpack_from('<H',mat)[0]*8,8)
    resolved_address=mb+(base+struct.unpack_from('<H',an,2)[0])*32;mat=earlier_read(resolved_address,32)
    assert captured[5]&256
    synthetic=bytearray(48);struct.pack_into('<HHI',synthetic,36,struct.unpack_from('<H',mat,26)[0],struct.unpack_from('<H',mat,10)[0],(struct.unpack_from('<I',st)[0]+struct.unpack_from('<I',mat,4)[0])&0xffffffff)
    pal=(root/'camera/candidate-palette-140.bin').read_bytes();scratch=0x0f000000
    @Read
    def reader(ctx,address,out,size):
     if address==scratch and size==48:data=synthetic
     elif address==0x05000000 and size==512:data=pal
     else:
      return d.nf_live_completed_snapshot_read(*earlier_identity,address,out,size)
     C.memmove(out,bytes(data),size);return 1
    surface=C.c_void_p();size=C.c_size_t();light=C.c_void_p();ls=C.c_size_t()
    assert d.nf_extract_wall(reader,None,captured[0],captured[1],captured[2],scratch,resolved_address,captured[5],C.byref(surface),C.byref(size),C.byref(light),C.byref(ls))
    data=C.string_at(surface,size.value);assert hashlib.sha256(data[172:]).hexdigest()==textures[index]
    # Compare the complete record, including cyclic endpoint geometry and UV.
    cursor=8
    for wi in range(index):
     vn,ww,hh=struct.unpack_from('<3I',world,cursor);cursor+=12+vn*40+ww*hh*4
    assert data==world[cursor:cursor+size.value]
    (root/'camera/candidate-owned-140-surface.bin').write_bytes(data)
    candidate_extractions.append(dict(source_scene=140,reference_scene=141,descriptor=captured[1],bytes=size.value,exact=True,limitation='Descriptor address and draw flags discovered from later draw; source bytes/material/palette from earlier owned scene.'))
    d.nf_surface_free(surface);d.nf_surface_free(light)''')
s=s.replace('candidate_palettes=candidate_palettes,scope=', 'candidate_palettes=candidate_palettes,candidate_extractions=candidate_extractions,scope=');p.write_text(s)
