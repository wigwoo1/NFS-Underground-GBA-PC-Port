from pathlib import Path
import struct,json,math
from scene_batches import records
root=Path('work/camera')
def si(v):v&=0xffffffff;return v-0x100000000 if v&0x80000000 else v
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def i(b,o):return struct.unpack_from('<i',b,o)[0]
def half(v):return ((v+32768)&65535)-32768
matched=0;maximum=0;max_texel=0;affine_matches=0;perspective_matches=0
for e in records(root/'world.bin'):
 if e['pc']!=0x030032f0:continue
 b=e['blocks'];desc=b[4][1];src=b[5][1];cam=struct.unpack('<12i',b[2][1]);mat=b[8][1];context=b[3][1]
 if u(desc,4) or not u(desc,8):continue
 width=1<<u(mat,36);height=u(mat,38)//2;affine=i(b[69][1],0)!=0
 start=u(b[1][1],242);count=u(b[1][1],244);scale=i(context,28);face=b[42][1] or bytes(20)
 projected=[struct.unpack_from('<6i',b[7][1],(start+j)*24) for j in range(count)]
 for j in range(u(desc,2)):
  s=src[j*68:(j+1)*68];o=b[10+j][1] or bytes(32)
  x=i(s,0)+h(o,0)+cam[9];z=i(s,4)+h(o,2)+cam[11]
  cx=half(si(x*cam[0]+z*cam[6])>>14);cz=half(si(x*cam[2]+z*cam[8])>>14)
  if cz<64 or cz>0x5fff:continue
  reciprocal=16777216//(cz+1);factor=si(scale*reciprocal)>>7
  cy=h(s,56)+h(o,6)+h(face,6)+cam[10]
  px=h(context,8)+(si((cx>>1)*factor)>>16);py=h(context,10)+(si((cy>>1)*factor)>>16)
  candidates=[v for v in projected if v[0]==px and v[1]==py and (affine or v[3]==reciprocal)]
  if not candidates:continue
  expected=(i(s,32)/16384+h(b[9][1],4)/(256*width),i(s,36)/16384+h(b[9][1],6)/(512*height))
  errors=[]
  for v in candidates:
   q=1 if affine else v[3]/65536
   actual=((v[4]/65536/q+h(b[9][1],4)/512)/(width*.5),(v[5]/65536/q+h(b[9][1],6)/512)/height)
   errors.append(tuple(abs(actual[k]-expected[k]-round(actual[k]-expected[k])) for k in (0,1)))
  pair=min(errors,key=max);error=max(pair);maximum=max(maximum,error);matched+=1
  # Original perspective UV generation floors once before reciprocal multiply
  # and once afterward. Bound both lost fractions in normalized texture units.
  for k,denom in enumerate((width*.5,height)):
   bound=1e-10 if affine else (1/256+1/reciprocal)/denom+1e-10
   assert pair[k]<=bound,(e['id'],j,k,pair[k],bound)
  max_texel=max(max_texel,pair[0]*width,pair[1]*height)
  affine_matches+=affine;perspective_matches+=not affine
assert matched>0 and affine_matches>0 and perspective_matches>0
report={'result':'PASS','unclipped_vertex_matches':matched,'affine_matches':affine_matches,'perspective_matches':perspective_matches,
        'maximum_wrapped_UV_error':maximum,'maximum_texel_error':max_texel,
        'within_original_integer_rounding_bound':True,'scope':'Observed +8 surfaces, original uncut corners only; clipped UVs and alternate surface coverage remain incomplete.'}
(root/'road-uv-tests.json').write_text(json.dumps(report,indent=2));print(report)
