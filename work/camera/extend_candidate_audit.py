from pathlib import Path
p=Path('work/camera/test_texture_provenance.py');s=p.read_text();s=s.replace("d.nf_live_completed_wall_animation.argtypes=sig", "d.nf_live_completed_wall_animation.argtypes=sig\nd.nf_live_completed_snapshot_read.argtypes=sig+[C.c_size_t]\ncandidate_sources=[]")
s=s.replace("current={};ordinal=0",'''if h[4] in (140,141):
   def read_owned(address,size):
    out=C.create_string_buffer(size);assert d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],address,out,size);return out.raw
   state=read_owned(50331840,256);source=read_owned(139937176,68)
   base=struct.unpack_from('<H',source,44)[0];materials=struct.unpack_from('<I',state,32)[0]
   material=read_owned(materials+base*32,32);anim=struct.unpack_from('<H',material)[0]
   animation=read_owned(struct.unpack_from('<I',state,72)[0]+anim*8,8)
   frame=struct.unpack_from('<H',animation,2)[0];resolved=read_owned(materials+(base+frame)*32,32)
   texture=(struct.unpack_from('<I',state)[0]+struct.unpack_from('<I',resolved,4)[0])&0xffffffff
   width=1<<struct.unpack_from('<H',resolved,26)[0];height=struct.unpack_from('<H',resolved,10)[0]
   indices=read_owned(texture,width*height);palette=read_owned(0x05000000,512)
   candidate_sources.append(dict(serial=h[4],base=base,animation=anim,frame=frame,texture=texture,width=width,height=height,source_hash=hashlib.sha256(source).hexdigest(),index_hash=hashlib.sha256(indices).hexdigest(),palette_hash=hashlib.sha256(palette).hexdigest()))
   bad=C.create_string_buffer(b'X'*68);saved=bad.raw
   assert not d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6]+1,139937176,bad,68) and bad.raw==saved
   assert not d.nf_live_completed_snapshot_read(epoch,h[4],h[5],h[6],0xffffffff,bad,68) and bad.raw==saved
  current={};ordinal=0''')
s=s.replace("animation_samples=animation_samples,scope=", "animation_samples=animation_samples,candidate_sources=candidate_sources,scope=");p.write_text(s)
