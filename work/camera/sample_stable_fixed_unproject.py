from pathlib import Path
import ctypes as C,json,struct,math,sys
policy=int(sys.argv[1]) if len(sys.argv)>1 else 0;assert policy in (0,1)
p=Path('work/camera');r=json.loads((p/'stable-road-owned-continuous-clipped-rings.json').read_text());geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);fn=C.CDLL(str((p/'road-edge-continuous.dll').resolve())).nf_road_edge_continuous;fn.argtypes=[C.c_void_p]*4;checks=[]
def unproject(q,value):
 def integer(i,j):
  index=i>>4
  if not 0<=index<32768:return None
  reciprocal=struct.unpack_from('<I',rom,0x627700+index*4)[0];product=(reciprocal*(j>>8))&0xffffffff
  if product>=0x80000000:product-=0x100000000
  return product>>4
 qi=math.floor(q);vi=math.floor(value);fq=q-qi;fv=value-vi;result=0
 for i in range(2):
  for j in range(2):
   weight=(fq if i else 1-fq)*(fv if j else 1-fv)
   if not weight:continue
   term=integer(qi+i,vi+j)
   if term is None:return None
   result+=term*weight
 return result
for road,g in zip(r['checks'],geo['roads']):
 ring=road['clipped_ring'];edges=[]
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]
  if a[1]>b[1]:a,b=b,a
  if a[1]==b[1]:continue
  out=(C.c_double*4)();assert fn((C.c_double*6)(*a),(C.c_double*6)(*b),table,out);edges.append((a,b,list(out)))
 fixture=(p/f"stable-road-{road['command']}-gpu-input.bin").read_bytes();magic,n,w,h=struct.unpack_from('<4I',fixture);indices=fixture[16+n*40+4:];assert len(indices)==w*h
 original=(p/f"stable-road-{road['command']}-all-original-samples.bin").read_bytes();mismatches=baseline=overlap=outside=0
 for off in range(0,len(original),5):
  dest,expected=struct.unpack_from('<IB',original,off);old=expected;x,y=dest%240,dest//240;sx=(int((x+.5)*13.5)+.5)/13.5;sy=(int((y+.5)*13.5)+.5)/13.5;sy=y if policy else sy;boundary=[]
  for a,b,slopes in edges:
   if not a[1]<=sy<b[1]:continue
   dy=sy-a[1];boundary.append([a[0]+slopes[0]*dy,a[4]+slopes[1]*dy,a[5]+slopes[2]*dy,a[3]+slopes[3]*dy])
  boundary.sort(key=lambda v:v[0])
  if len(boundary)<2 or boundary[-1][0]<=boundary[0][0]:outside+=1;continue
  a,b=boundary[0],boundary[-1];start=math.floor(a[0]/2)*2;width=math.floor((b[0]-a[0])/2)+2;pair=(x-start)//2
  if not start<=x<start+width*2:outside+=1;continue
  inverse=struct.unpack_from('<I',rom,0x627700+width*4)[0]>>8;t=pair*inverse/65536;v=[a[k]+t*(b[k]-a[k]) for k in (1,2,3)]
  if v[2]<=0:outside+=1;continue
  if width<=32:
   if a[3]<=0 or b[3]<=0:outside+=1;continue
   ends=[[unproject(endpoint[3],endpoint[k+1]) for k in (0,1)] for endpoint in (a,b)]
   if any(v is None for row in ends for v in row):outside+=1;continue
   uv=[(ends[0][k]+t*(ends[1][k]-ends[0][k]))/(65536*road['normalization'][k]) for k in (0,1)]
  else:
   origin=(pair//16)*16;fraction=(pair%16)/16;ends=[]
   for offset in (origin,origin+16):
    bt=offset*inverse/65536;bv=[a[k]+bt*(b[k]-a[k]) for k in (1,2,3)]
    if bv[2]<=0:break
    values=[unproject(bv[2],bv[k]) for k in (0,1)]
    if any(v is None for v in values):break
    ends.append([values[k]/(65536*road['normalization'][k]) for k in (0,1)])
   if len(ends)!=2:outside+=1;continue
   uv=[ends[0][k]+fraction*(ends[1][k]-ends[0][k]) for k in (0,1)]
  tx=(2*math.floor(uv[0]*(w/2))+x%2)%w;ty=math.floor(uv[1]*h)%h;actual=indices[ty*w+tx];overlap+=1;mismatches+=actual!=expected;baseline+=0
 checks.append(dict(command=road['command'],all_original_samples=len(original)//5,continuous_overlap=overlap,outside=outside,index_mismatches=mismatches,baseline_comparison_available=False))
report=dict(integer_row_origin=bool(policy),result='MEASURED',checks=checks,scope='Owned native rings/bounds continuous clip and edge arithmetic with original padded pair width/interior reciprocal/paired texture lanes, optional integer row origin. All original pixels compared, no baseline-overlap restriction; 16pair block and narrow affine divisions included; integer-exact bilinear word-cell unprojection extension included, original per-block increment rounding and doubledrow correction absent, GPU, fullscene or motion proof.');(p/f'stable-road-continuous-fixed-unproject-{policy}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))




