"""Retained stable scene source contexts, no screen reconstruction."""
from pathlib import Path
import struct,json,hashlib,ctypes as C
p=Path('work/camera');source=p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-bundle.bin';b=source.read_bytes();h=struct.unpack_from('<8I',b);assert h[0]==0x4252464e and h[7]==len(b)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=rom[0x627700:0x647700];recip=struct.unpack('<32768I',table)
d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));fn=d.nf_road_perspective_plan;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
def si(x):return ((x+2**31)%2**32)-2**31
def unproject(q,a):
 index=si(q)>>4;assert 0<=index<32768
 return si(recip[index]*(si(a)>>8))>>4
Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
pixel_fn=d.nf_road_span_pixels;pixel_fn.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p,C.c_uint]
checks=[];errors=[];allspans=0;verified_pairs=0
for i in range(h[3]):
 pas,ordinal,offset,size=struct.unpack_from('<4I',b,32+i*16);asset=b[offset:offset+size];a=struct.unpack_from('<10I',asset);assert a[0]==0x4552464e and a[2]==h[2] and len(asset)==a[9]+a[8]
 texture=asset[a[9]:];assert texture==rom[a[7]-0x08000000:a[7]-0x08000000+a[8]]
 perspective=0;local=[];address_changes=index_pair_changes=index_lane_changes=0;examples=[]
 for j in range(a[5]):
  s=struct.unpack_from('<20I',asset,40+j*80);assert s[2] in (0x03003190,0x030056d8);allspans+=1
  if s[2]!=0x03003190:continue
  perspective+=1;c=s[4:20];q,u,v=c[10],c[8],c[9];dq=si((si(c[13]-q)*si(c[4]))>>12);du=si(si((si(c[11]-u)>>8)*c[4])>>4);dv=si(si((si(c[12]-v)>>8)*c[4])>>4)
  out=C.create_string_buffer(2048);final=C.create_string_buffer(64);n=C.c_uint();assert fn(struct.pack('<16I',*c),table,out,32,C.byref(n),final);at=0
  for r in range(n.value):
   run=struct.unpack_from('<16I',out.raw,r*64)
   @Read
   def read_texture(user,address,target,size):
    off=address-a[7]
    if off<0 or off+size>len(texture):return 0
    C.memmove(target,texture[off:off+size],size);return 1
   sampled=C.create_string_buffer(run[7]*2);assert pixel_fn(struct.pack('<12I',*run[:12]),read_texture,None,sampled,run[7])
   for k in range(run[7]):
    ideal=(si(unproject(si(q+dq*at//16),si(u+du*at//16))+c[14]),si(unproject(si(q+dq*at//16),si(v+dv*at//16))+c[15]));block=(si(run[8]+k*run[10]),si(run[9]+k*run[11]));local.append(max(abs(x-y) for x,y in zip(ideal,block))/65536)
    def texel(uv):
     address=2*((uv[0]&c[1])>>16)+2*(((uv[1]&c[2])>>16)<<c[0]);assert address+2<=len(texture)
     return address,texture[address:address+2]
    block_address,block_indices=texel(block);ideal_address,ideal_indices=texel(ideal)
    assert sampled.raw[k*2:k*2+2]==block_indices;verified_pairs+=1
    address_changes+=block_address!=ideal_address;index_pair_changes+=block_indices!=ideal_indices;index_lane_changes+=sum(x!=y for x,y in zip(block_indices,ideal_indices))
    if block_indices!=ideal_indices and len(examples)<8:examples.append(dict(span=j,pair=at,block_address=block_address,per_sample_address=ideal_address,block_indices=list(block_indices),per_sample_indices=list(ideal_indices)))
    at+=1
  assert at==c[7]
 errors.extend(local);checks.append(dict(pass_index=pas,ordinal=ordinal,spans=a[5],perspective_spans=perspective,texture_sha256=hashlib.sha256(texture).hexdigest(),address_changes=address_changes,index_pair_changes=index_pair_changes,index_lane_changes=index_lane_changes,examples=examples,samples=len(local),max_difference=max(local,default=0)))
assert checks and errors and verified_pairs==len(errors);errors.sort();report=dict(result='MEASURED',serial=h[2],native_writer_verified_pairs=verified_pairs,assets=len(checks),spans=allspans,samples=len(errors),nonzero_samples=sum(x>0 for x in errors),max_difference=max(errors),p95_difference=errors[int(.95*(len(errors)-1))],address_changes=sum(c['address_changes'] for c in checks),index_pair_changes=sum(c['index_pair_changes'] for c in checks),index_lane_changes=sum(c['index_lane_changes'] for c in checks),checks=checks,source_sha256=hashlib.sha256(b).hexdigest(),scope='Actual retained serial137 road contexts and immutable ROM textures. Original16sample versus per-sample reciprocal at identical block slopes, with exact material masks and owned source paired-index lookup; not actual GPU UV or proof of visual discrepancy cause. Source spans used for measurement only, no renderer reconstruction.')
(p/'stable-road-block-sampling.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
