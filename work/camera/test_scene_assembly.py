from pathlib import Path
import ctypes as C,json,struct
root=Path('work/camera');d=C.CDLL(str((root/'scene_assembly.dll').resolve()))
P=C.c_void_p;Z=C.c_size_t;U=C.c_uint32
d.nf_assembly_create.restype=P
d.nf_assembly_reset.argtypes=[P];d.nf_assembly_destroy.argtypes=[P]
d.nf_assembly_surface.argtypes=[P,P,P,Z,P,Z]
d.nf_assembly_model.argtypes=[P,P,P,Z]
d.nf_assembly_finish.argtypes=[P,U,U,U,U,P,Z,C.POINTER(P),C.POINTER(Z)]
d.nf_scene_packet_free.argtypes=[P]
def parts(packet):
 sections=[]
 for i in range(5):
  offset,size=struct.unpack_from('<2I',packet,36+i*12);sections.append(packet[offset:offset+size])
 model,world,order,lighting,identity=sections
 count=struct.unpack_from('<I',world,4)[0];wp=lp=8;surfaces=[]
 for i in range(count):
  n,w,h=struct.unpack_from('<3I',world,wp);size=12+n*40+w*h*4
  lit=struct.unpack_from('<I',lighting,lp)[0];ls=20+w*h*64 if lit else 4
  surfaces.append((identity[8+i*20:28+i*20],world[wp:wp+size],lighting[lp:lp+ls]));wp+=size;lp+=ls
 return model,identity[-20:],surfaces,struct.unpack_from(f'<{count+1}I',order,8),lighting[lp:]
def copied_call(fn,assembly,*blobs):
 buffers=[C.create_string_buffer(b) for b in blobs]
 if len(buffers)==3:ok=fn(assembly,buffers[0],buffers[1],len(blobs[1]),buffers[2],len(blobs[2]))
 else:ok=fn(assembly,buffers[0],buffers[1],len(blobs[1]))
 for b in buffers:C.memset(b,0xCD,len(b))
 return ok
assembly=d.nf_assembly_create();assert assembly;checked=total=0
try:
 for path in sorted((root/'packet-sequence').glob('scene-*.packet')):
  reference=path.read_bytes();model,mid,surfaces,order,table=parts(reference)
  for index in order:
   if index==0xFFFFFFFF:assert copied_call(d.nf_assembly_model,assembly,mid,model)
   else:assert copied_call(d.nf_assembly_surface,assembly,*surfaces[index])
  meta=struct.unpack_from('<4I',reference,16);out=P();size=Z()
  assert d.nf_assembly_finish(assembly,*meta,table,len(table),C.byref(out),C.byref(size))
  # Releasing all staged components must not invalidate the published packet.
  d.nf_assembly_reset(assembly)
  assert C.string_at(out,size.value)==reference,path.name
  total+=size.value;checked+=1;d.nf_scene_packet_free(out)
 assert checked==48
 failures=0
 def rejected():
  global failures
  out=P(123);size=Z(456)
  assert not d.nf_assembly_finish(assembly,*meta,table,len(table),C.byref(out),C.byref(size))
  assert out.value==123 and size.value==456
  failures+=1;d.nf_assembly_reset(assembly)
 rejected() # No visible model.
 assert copied_call(d.nf_assembly_model,assembly,mid,model)
 assert not copied_call(d.nf_assembly_model,assembly,mid,model)
 rejected() # Multiple models poison this unsupported scene.
 for bad_surface,bad_light in [(surfaces[0][1][:-1],surfaces[0][2]),(surfaces[0][1],b'\x02\0\0\0')]:
  assert not copied_call(d.nf_assembly_surface,assembly,surfaces[0][0],bad_surface,bad_light)
  assert not copied_call(d.nf_assembly_model,assembly,mid,model)
  rejected()
 malformed=bytearray(model);struct.pack_into('<d',malformed,24,float('nan'))
 assert copied_call(d.nf_assembly_model,assembly,mid,bytes(malformed));rejected()
 for _ in range(128):assert copied_call(d.nf_assembly_surface,assembly,*surfaces[0])
 assert not copied_call(d.nf_assembly_surface,assembly,*surfaces[0]);rejected()
 report={'result':'PASS','complete_packets_byte_identical':checked,'verified_bytes':total,'source_and_packet_ownership_verified':True,'rejected_incomplete_or_invalid_scenes':failures,'scope':'Native assembly from prepared per-draw components; live boundary hooks and publication remain pending.'}
 (root/'scene-assembly-tests.json').write_text(json.dumps(report,indent=2));print(report)
finally:d.nf_assembly_destroy(assembly)
