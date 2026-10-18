from pathlib import Path
import json,struct,math,ctypes as C
p=Path('work/camera');m=json.loads((p/'stable-road-emission-source-map.json').read_text());g=json.loads((p/'stable-road-geometric-inputs.json').read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',rom[0x627700:0x647700]);checks=[];d=C.CDLL(str((p/'road-polygon-clip.dll').resolve()));step=d.nf_road_edge_step;step.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];rt=(C.c_uint32*32768)(*table);verified=0
si=lambda x:(x&0xffffffff)-0x100000000 if x&0x80000000 else x&0xffffffff
for road,geo in zip(m['checks'],g['roads']):
 ring=[x['six_words'] for x in road['mapping']];rows=[]
 for i,a in enumerate(ring):
  b=ring[(i+1)%len(ring)]
  if b[1]<a[1]:a,b=b,a
  h=b[1]-a[1]
  if not h or h>=32768:continue
  slopes=[si((table[h]>>8)*(b[0]-a[0]))]+[si((si(b[k]-a[k])*table[h])>>24) for k in (4,5,3)]
  if a[1]<160 and b[1]>0:
   context=(C.c_uint32*18)();context[8]=2;context[11]=2;context[13]=160;pair=(C.c_int32*12)(*a,*b);fb=(C.c_uint32*4)(0x0600a000,0,0,240);out=(C.c_uint32*18)();assert step(context,0,0,pair,2,rt,fb,out)==1;assert [si(out[k]) for k in (4,5,6,7)]==slopes;verified+=1
  for y in range(max(0,a[1]),min(160,b[1])):
   dy=y-a[1];ideal=[a[k]+(b[k]-a[k])*dy/h for k in (0,4,5,3)];fixed=[si((a[0]<<16)+slopes[0]*dy)/65536]+[si(a[k]+slopes[j+1]*dy) for j,k in enumerate((4,5,3))]
   if fixed[3]<=0 or ideal[3]<=0:continue
   uv_error=[(fixed[k+1]/fixed[3]-ideal[k+1]/ideal[3])*geo['width' if k==0 else 'height']/((1<<geo['source_attributes_header'][1])*.5 if k==0 else geo['source_attributes_header'][2]*.5) for k in range(2)]
   rows.append(dict(edge=i,y=y,fixed_x=fixed[0],ideal_x=ideal[0],x_error=fixed[0]-ideal[0],uv_error_texels=uv_error,in_horizontal_view=0<=fixed[0]<240))
 checks.append(dict(source=road['source'],edge_row_samples=len(rows),visible_x_samples=sum(r['in_horizontal_view'] for r in rows),max_x_error=max(abs(r['x_error']) for r in rows),max_uv_error_texels=max(abs(v) for r in rows for v in r['uv_error_texels']),rows=rows))
report=dict(native_edge_slope_checks=verified,result='MEASURED',checks=checks,scope='Original emitted source-ordered ring edges: recovered integer reciprocal/truncation slopes versus ideal linear slopes on same endpoints. Unclipped ring, not horizontal clipping/span scheduling/texture pixel parity. Original projected values diagnostic only.');(p/'stable-road-edge-slope-measurement.json').write_text(json.dumps(report,indent=2));print(json.dumps([{k:v for k,v in c.items() if k!='rows'} for c in checks],indent=2))

