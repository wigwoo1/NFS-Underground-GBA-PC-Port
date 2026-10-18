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
# Independent diagnostic oracle. Never native renderer geometry.
oracle=json.loads((p/'stable-road-full-span-replay.json').read_text());assert oracle['result']=='PASS'
r['checks']=[dict(command=c['ordinal'],clipped_ring=c['clipped_source_stream'],bounds=c['bounds'],normalization=[(1<<g['source_attributes_header'][1])*.5,g['source_attributes_header'][2]*.5]) for c,g in zip(oracle['checks'],geo['roads'])]
for road,g in zip(r['checks'],geo['roads']):
 ring=road['clipped_ring'];edges=[]
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]
  if a[1]>b[1]:a,b=b,a
  if a[1]==b[1]:continue
  out=(C.c_double*4)();assert fn((C.c_double*6)(*a),(C.c_double*6)(*b),table,out);edges.append((a,b,list(out)))
 row_origin={};scan=max(road['bounds'][2],min(v[1] for v in ring));doubled=False
 while scan<road['bounds'][3]:
  active=[]
  for a,b,slopes in edges:
   if a[1]<=scan<b[1]:
    dy=scan-a[1];active.append((a[0]+slopes[0]*dy,a[3]+slopes[3]*dy))
  active.sort()
  if len(active)>=2 and active[-1][0]>active[0][0] and active[0][1]>0xc000:doubled=True
  row_origin[int(scan)]=scan
  if doubled:row_origin[int(scan)+1]=scan
  scan+=2 if doubled else 1
 fixture=(p/f"stable-road-{road['command']}-gpu-input.bin").read_bytes();magic,n,w,h=struct.unpack_from('<4I',fixture);indices=fixture[16+n*40+4:];assert len(indices)==w*h
 original=(p/f"stable-road-{road['command']}-all-original-samples.bin").read_bytes();mismatches=baseline=overlap=outside=0;differences=[]
 for off in range(0,len(original),5):
  dest,expected=struct.unpack_from('<IB',original,off);old=expected;x,y=dest%240,dest//240;sx=(int((x+.5)*13.5)+.5)/13.5;sy=(int((y+.5)*13.5)+.5)/13.5;sy=row_origin.get(y,y) if policy else sy;boundary=[]
  for a,b,slopes in edges:
   if not a[1]<=sy<b[1]:continue
   dy=sy-a[1];boundary.append([a[0]+slopes[0]*dy,a[4]+slopes[1]*dy,a[5]+slopes[2]*dy,a[3]+slopes[3]*dy])
  boundary.sort(key=lambda v:v[0])
  if len(boundary)<2 or boundary[-1][0]<=boundary[0][0]:outside+=1;continue
  a,b=boundary[0],boundary[-1];start=math.floor(a[0]/2)*2;width=math.floor((b[0]-a[0])/2)+2;pair=(x-start)//2
  if not start<=x<start+width*2:outside+=1;continue
  inverse=struct.unpack_from('<I',rom,0x627700+width*4)[0]>>8;t=pair*inverse/65536;v=[a[k]+t*(b[k]-a[k]) for k in (1,2,3)]
  if v[2]<=0:outside+=1;continue
  si=lambda value:C.c_int32(int(value)).value
  if width<=32:
   ends=[[unproject(endpoint[3],endpoint[k+1]) for k in (0,1)] for endpoint in (a,b)]
   if any(value is None for row in ends for value in row):outside+=1;continue
   fixed=[si(ends[0][k]+pair*(si(inverse*(si(ends[1][k]-ends[0][k])>>8))>>8)) for k in (0,1)]
  else:
   block=pair//16;within=pair%16
   increments=[(si((si(int(b[k])-int(a[k]))>>8)*inverse)>>4) for k in (1,2)]
   dq=si((si(int(b[3])-int(a[3]))*inverse)>>12)
   ends=[]
   for step in (block,block+1):
    q=si(a[3]+step*dq);values=[unproject(q,si(a[k+1]+step*increments[k])) for k in (0,1)]
    if any(value is None for value in values):break
    ends.append(values)
   if len(ends)!=2:outside+=1;continue
   fixed=[si(ends[0][k]+within*(si(ends[1][k]-ends[0][k])>>4)) for k in (0,1)]
  uv=[fixed[k]/(65536*road['normalization'][k]) for k in (0,1)]
  tx=(2*math.floor(uv[0]*(w/2))+x%2)%w;ty=math.floor(uv[1]*h)%h;actual=indices[ty*w+tx];overlap+=1;mismatches+=actual!=expected;baseline+=0
  if actual!=expected:differences.append(dict(x=x,y=y,row_origin=sy,start=start,width=width,pair=pair,expected=expected,actual=actual,left_edge=a,right_edge=b))
 checks.append(dict(command=road['command'],all_original_samples=len(original)//5,continuous_overlap=overlap,outside=outside,index_mismatches=mismatches,baseline_comparison_available=False,differences=differences))
report=dict(integer_row_origin=bool(policy),result='MEASURED',checks=checks,scope='ORACLE ONLY verified original clipped rings and exact integer edge slopes with original padded pair width/interior reciprocal/paired texture lanes, optional integer row origin. Captured original source-pipeline output used only to isolate evaluator, never native renderer geometry or polygon correspondence. All original pixels compared; 16pair block and narrow affine divisions included; integer-exact bilinear word-cell unprojection extension included, original per-block increment rounding included, source-derived sticky doubledrow schedule included, GPU, fullscene or motion proof.');(p/f'stable-road-original-rounded-rows-oracle-{policy}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))









