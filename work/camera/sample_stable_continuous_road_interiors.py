from pathlib import Path
import ctypes as C,json,struct,math
p=Path('work/camera');r=json.loads((p/'stable-road-owned-continuous-clipped-rings.json').read_text());geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);fn=C.CDLL(str((p/'road-edge-continuous.dll').resolve())).nf_road_edge_continuous;fn.argtypes=[C.c_void_p]*4;checks=[]
for road,g in zip(r['checks'],geo['roads']):
 ring=road['clipped_ring'];edges=[]
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]
  if a[1]>b[1]:a,b=b,a
  if a[1]==b[1]:continue
  out=(C.c_double*4)();assert fn((C.c_double*6)(*a),(C.c_double*6)(*b),table,out);edges.append((a,b,list(out)))
 fixture=(p/f"stable-road-{road['command']}-gpu-input.bin").read_bytes();magic,n,w,h=struct.unpack_from('<4I',fixture);indices=fixture[16+n*40+4:];assert len(indices)==w*h
 original=(p/f"stable-road-{road['command']}-cpu-samples.bin").read_bytes();mismatches=baseline=overlap=outside=0
 for off in range(0,len(original),6):
  dest,old,expected=struct.unpack_from('<IBB',original,off);x,y=dest%240,dest//240;sx=(int((x+.5)*13.5)+.5)/13.5;sy=(int((y+.5)*13.5)+.5)/13.5;boundary=[]
  for a,b,slopes in edges:
   if not a[1]<=sy<b[1]:continue
   dy=sy-a[1];boundary.append([a[0]+slopes[0]*dy,a[4]+slopes[1]*dy,a[5]+slopes[2]*dy,a[3]+slopes[3]*dy])
  boundary.sort(key=lambda v:v[0])
  if len(boundary)<2 or not boundary[0][0]<=sx<=boundary[-1][0] or boundary[-1][0]<=boundary[0][0]:outside+=1;continue
  a,b=boundary[0],boundary[-1];t=(sx-a[0])/(b[0]-a[0]);v=[a[k]+t*(b[k]-a[k]) for k in (1,2,3)]
  if v[2]<=0:outside+=1;continue
  uv=[v[k]/v[2]/road['normalization'][k] for k in (0,1)];tx=math.floor(uv[0]*w)%w;ty=math.floor(uv[1]*h)%h;actual=indices[ty*w+tx];overlap+=1;mismatches+=actual!=expected;baseline+=old!=expected
 checks.append(dict(command=road['command'],original_baseline_samples=len(original)//6,continuous_overlap=overlap,outside=outside,index_mismatches=mismatches,baseline_mismatches_same_subset=baseline))
report=dict(result='MEASURED',checks=checks,scope='Owned native rings/bounds continuous clip and edge arithmetic with ideal interior interpolation at actual native centers. Baseline overlap fixture restricts original comparison; no packed pair/block correction, GPU, fullscene or motion proof.');(p/'stable-road-continuous-interior-sampling.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
