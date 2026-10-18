"""Compare captured road near-edge UVs with original fixed-point clipping."""
from pathlib import Path
import ctypes as C,json,struct,math
from scene_batches import records
p=Path('work/camera');d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nfs_visibility_wall_clip;fn.argtypes=[P:=C.c_void_p,P,P,C.c_int,C.c_uint,C.c_uint,P]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();recip=(C.c_uint32*32768).from_buffer_copy(rom[0x627700:0x647700])
def i(b,o):return struct.unpack_from('<i',b,o)[0]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def si(v):return ((v+2**31)%2**32)-2**31
def half(v):return ((v+32768)%65536)-32768
class Vertex(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('u',C.c_double),('v',C.c_double)]
gpu=C.CDLL(str((p/'road-near-clip-probe.dll').resolve())).nf_road_near_clip_probe
gpu.argtypes=[C.POINTER(Vertex),C.c_uint,C.POINTER(Vertex),C.c_double];gpu.restype=C.c_uint
project=d.nfs_visibility_surface_vertices;project.argtypes=[P,P,P,P,P,P,C.c_size_t,P]
correction=C.CDLL(str((p/'road-near-attributes.dll').resolve())).nf_road_near_attributes
correction.argtypes=[C.c_double,C.c_double,P,C.c_uint,C.c_uint,C.c_uint,C.c_int,P,P]
continuity_checks=0
edges=[]
for event in records(p/'world.bin'):
 if event['pc']!=0x030032f0:continue
 blocks=event['blocks'];desc=blocks[4][1];src=blocks[5][1];cam=struct.unpack('<12i',blocks[2][1]);mat=blocks[8][1]
 if u(desc,4) or not u(desc,8):continue
 assert i(blocks[3][1],16)==64,('captured near plane',event['id'],i(blocks[3][1],16))
 vertices=[]
 for j in range(u(desc,2)):
  s=src[j*68:(j+1)*68];o=blocks[10+j][1] or bytes(32)
  x=i(s,0)+h(o,0)+cam[9];z=i(s,4)+h(o,2)+cam[11]
  cz=half(si(x*cam[2]+z*cam[8])>>14)
  vertices.append((cz,i(s,32),i(s,36),u(s,46)))
 for j,a in enumerate(vertices):
  b=vertices[(j+1)%len(vertices)];z0,z1=a[0],b[0]
  if (z0<64)==(z1<64):continue
  delta=abs(z1-z0)
  if delta>=32768:continue
  scratch=bytearray(52);struct.pack_into('<2h',scratch,4,z0,z1);buf=C.create_string_buffer(bytes(scratch));heights=(C.c_uint32*4)();attrs=(C.c_uint32*4)(a[1]&0xffffffff,a[2]&0xffffffff,b[1]&0xffffffff,b[2]&0xffffffff)
  assert fn(buf,heights,attrs,64,a[3],desc[18],recip)==1
  target=0 if z0<64 else 2;t=(64-z0)/(z1-z0);observed=[];ideal=[];bounds=[]
  for axis in (0,1):
   actual=si(attrs[target+axis])/16384;expected=(a[1+axis]+(b[1+axis]-a[1+axis])*t)/16384
   # Exclude signed attribute difference overflow from this real-valued bound.
   difference=b[1+axis]-a[1+axis]
   if not -2**31<=difference<2**31:continue
   factor=(64-min(z0,z1))*int(recip[delta])/2**24
   exact_t=t if z0<64 else 1-t
   bound=(abs(difference)*abs(exact_t-factor)+1)/16384+1e-10
   assert abs(actual-expected)<=bound,(event['id'],j,axis,actual,expected,bound)
   observed.append(actual);ideal.append(expected);bounds.append(bound)
  if len(observed)==2:
   width=1<<u(mat,36);height=u(mat,38)//2
   animation=blocks[9][1];du=h(animation,4)/(256*width);dv=h(animation,6)/(512*height)
   inputs=(Vertex*2)(Vertex(0,0,z0,a[1]/16384+du,a[2]/16384+dv),Vertex(0,0,z1,b[1]/16384+du,b[2]/16384+dv));out=(Vertex*4)()
   count=gpu(inputs,2,out,64);assert count==3
   # First emitted point belongs to the closing b->a edge; the original
   # native edge remains a->b. Geometric interpolation is direction invariant.
   continuous=(out[0].u,out[0].v)
   assert max(abs(continuous[k]-(ideal[k]+(du,dv)[k])) for k in (0,1))<1e-12
   material_base=struct.unpack_from('<I',blocks[1][1],32)[0]+u(desc,8)*32
   assert 0x08000000<=material_base and material_base+32<=0x08000000+len(rom)
   source_mat=rom[material_base-0x08000000:material_base-0x08000000+32]
   params=(C.c_uint32*6)(1,0,0,u(source_mat,26),u(source_mat,10),int(bool(i(blocks[69][1],0))))
   projected=C.create_string_buffer(48);emitted=C.c_uint()
   assert project(buf,heights,attrs,params,recip,projected,48,C.byref(emitted))
   # The clipped start is emitted first, while clipped end is the single
   # emitted point. Identify by source-edge role, never screen coordinates.
   words=struct.unpack_from('<6i',projected.raw,0)
   q=65536 if params[5] else words[3]
   original=(words[4]/q/(width*.5)+du,words[5]/q/height+dv)
   def sample(uv):
    x=math.floor(uv[0]*width)%width;y=math.floor(uv[1]*height)%height
    packed=blocks[66][1];assert len(packed)>=width*height*2
    index=packed[y*width*2+x];palette=blocks[67][1]
    return (x,y,index,u(palette,index*2))
   raw_attrs=(C.c_int32*4)(a[1],a[2],b[1],b[2]);corrected=(C.c_double*2)()
   assert correction(z0,z1,raw_attrs,u(source_mat,26),u(source_mat,10),params[5],64,recip,corrected)
   candidate=(corrected[0]+du,corrected[1]+dv)
   assert max(abs(candidate[k]-original[k]) for k in (0,1))<1e-12,(event['id'],j,candidate,original)
   for axis in (0,1):
    if (z0,z1)[axis]==64:continue
    values=[]
    for epsilon in (-1e-7,1e-7):
     depth=[z0,z1];depth[axis]+=epsilon;value=(C.c_double*2)()
     assert correction(*depth,raw_attrs,u(source_mat,26),u(source_mat,10),params[5],64,recip,value)
     values.append(list(value))
    assert max(abs(values[0][k]-values[1][k]) for k in (0,1))<1e-7
    continuity_checks+=1
   rejected=(C.c_double*2)(123,456)
   assert not correction(65,66,raw_attrs,u(source_mat,26),u(source_mat,10),params[5],64,recip,rejected) and list(rejected)==[123,456]
   continuous=candidate
   gpu_sample=sample(continuous);original_sample=sample(original)
   errors=[abs(x-y) for x,y in zip(original,continuous)]
   edges.append(dict(event=event['id'],edge=j,z=[z0,z1],affine=bool(i(blocks[69][1],0)),uv_error=errors,texel_error=[errors[0]*width,errors[1]*height],continuous_sample=gpu_sample,original_sample=original_sample,texel_address_changed=gpu_sample[:2]!=original_sample[:2],palette_index_changed=gpu_sample[2]!=original_sample[2],color_changed=gpu_sample[3]!=original_sample[3]))
assert edges
assert all(not e['texel_address_changed'] and not e['color_changed'] for e in edges)
report=dict(result='PASS',continuity_checks=continuity_checks,captured_crossings=len(edges),affine_crossings=sum(e['affine'] for e in edges),perspective_crossings=sum(not e['affine'] for e in edges),texel_address_changes=sum(e['texel_address_changed'] for e in edges),palette_index_changes=sum(e['palette_index_changed'] for e in edges),color_changes=sum(e['color_changed'] for e in edges),maximum_uv_error=max(max(e['uv_error']) for e in edges),maximum_texel_error=max(max(e['texel_error']) for e in edges),worst_edges=sorted(edges,key=lambda e:max(e['texel_error']),reverse=True)[:10],changed_samples=[e for e in edges if e['texel_address_changed']],scope='Experimental source-attribute correction at138captured integer depth crossings matches native original clipping/projected UV and nearest texel/color exactly. Bilinear depth extension continuous across tested integer cells; does not establish near-plane topology transitions, smooth fullscene motion, GPU raster or live integration. Candidate not enabled in renderer.')
(p/'road-near-attribute-correction-tests.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ('worst_edges','changed_samples')})
