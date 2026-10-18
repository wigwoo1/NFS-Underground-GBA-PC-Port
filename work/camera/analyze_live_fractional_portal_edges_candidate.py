"""Independent integer-cell oracle for captured fractional portal edge arithmetic."""
import json,sys,struct,math,itertools
from pathlib import Path
from owned_portal_continuous import edge
ns={};exec(compile(Path('work/camera/analyze_live_portal_operands_candidate.py').read_text().split('path=Path(sys.argv[1])',1)[0],'graph-adapter','exec'),ns)
Graph=ns['PortalGraph'];path=Path(sys.argv[1]);data=json.loads(path.read_text());graphs={k:Graph(v) for k,v in data['graphs'].items()};table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes())
def signed(v):return (int(v)+2147483648)%4294967296-2147483648
def fixed(x,z,m):return signed(signed(x+m[9])*m[0]+signed(z+m[11])*m[6])>>14,signed(signed(x+m[9])*m[2]+signed(z+m[11])*m[8])>>14
def ideal(x,z,m):return (x+m[9])*m[0]+(z+m[11])*m[6],(x+m[9])*m[2]+(z+m[11])*m[8]
def oracle_cells(values,operation):
 floors=[math.floor(v) for v in values];fractions=[v-f for v,f in zip(values,floors)];terms=[];corners=[]
 for bits in itertools.product((0,1),repeat=len(values)):
  weight=math.prod(f if bit else 1-f for bit,f in zip(bits,fractions))
  if weight:
   value=operation(*(f+bit for f,bit in zip(floors,bits)));corners.append(value);terms.append(weight*value)
 # Constant cells are exactly constant; summation roundoff must not open a closed portal.
 if len(set(corners))==1:return corners[0]
 return math.fsum(terms)
def oracle(a,b,near,scale,center):
 x,z=a;nx,nz=b;flags=0
 if z<near and nz<near:return None
 def delta(t,d,x):return oracle_cells((t,d,x),lambda ti,di,xi:signed((signed(ti*xi)*signed(table[di]))>>24))
 if z<near:x+=delta(near-z,nz-z,nx-x);z=near;flags=8
 elif nz<near:nx-=delta(near-nz,z-nz,nx-x);nz=near;flags=16
 def project(x,z):return oracle_cells((x,z),lambda xi,zi:center+(signed((signed(table[zi]*scale)>>7)*(xi>>1))>>16))
 return project(x,z),project(nx,nz),flags,z,nz
checked=crossings=rejected=0;max_error=0.;samples=[]
for sample in data['samples']:
 alpha=sample['alpha']
 if alpha in (0,1):continue
 g,h=[graphs[k] for k in sample['graph_ids']];ma=struct.unpack_from('<12i',g.context,256);mb=struct.unpack_from('<12i',h.context,256);ea,eb=sample['endpoint_cameras'];cam=sample['sampled_camera'];fb=g.context[304:368];near=struct.unpack_from('<i',fb,16)[0];scale=struct.unpack_from('<I',fb,28)[0];center=struct.unpack_from('<h',fb,8)[0];count=0
 def camera(point):
  x,z=struct.unpack_from('<2i',point);v=ideal(x,z,cam);a,b=fixed(x,z,ma),fixed(x,z,mb);ia,ib=ideal(x,z,ea),ideal(x,z,eb)
  return tuple(v[k]+(1-alpha)*(a[k]-ia[k])+alpha*(b[k]-ib[k]) for k in range(2))
 for ordinal,region in enumerate(sample['portal_regions']):
  if region[6]>4:continue
  ring=g.graph()[0][region[0]][0];n=len(ring)//68
  for i in range(n):
   point=ring[i*68:(i+1)*68]
   if struct.unpack_from('<H',point,48)[0]==65535:continue
   a,b=camera(point),camera(ring[((i+1)%n)*68:((i+1)%n+1)*68])
   if max(a[1],b[1])>0x6000:break
   expected=oracle(a,b,near,scale,center);actual=edge(a,b,near,scale,center,table,ordinal==0)
   if expected is None:assert actual is None;rejected+=1;continue
   if ordinal==0 and expected[0]>expected[1]:expected=(expected[1],expected[0],*expected[2:])
   assert actual is not None and actual[2]==expected[2]
   error=max(abs(actual[k]-expected[k]) for k in (0,1,3,4));assert error<1e-9,(sample['sample_id'],region[0],i,error)
   checked+=1;count+=1;crossings+=bool(expected[2]);max_error=max(max_error,error)
 samples.append(dict(sample_id=sample['sample_id'],edges=count))
assert checked>0
original=Path('work/camera/owned-projected-portals.bin').read_bytes();integer_edges=0
for offset in range(0,len(original),368):
 m=struct.unpack_from('<12i',original,offset+168);fb=original[offset+216:offset+280];expected=struct.unpack_from('<6i',original,offset+344)
 a=fixed(*struct.unpack_from('<2i',original,offset+32),m);b=fixed(*struct.unpack_from('<2i',original,offset+100),m)
 result=oracle(a,b,struct.unpack_from('<i',fb,16)[0],struct.unpack_from('<I',fb,28)[0],struct.unpack_from('<h',fb,8)[0])
 if expected[5] and result[0]>result[1]:result=(result[1],result[0],*result[2:])
 assert result==expected[:5],(offset,result,expected);integer_edges+=1
out=dict(result='PASS_CAPTURED_FRACTIONAL_PORTAL_EDGE_CELL_ORACLE',original_integer_edges=integer_edges,samples=len(samples),edges=checked,near_crossings=crossings,fully_near_rejected=rejected,max_error=max_error,checks=samples,scope='Independent explicit multilinear corner sum and signed32 arithmetic match recovered edge extension on captured fractional camera inputs. Does not independently prove complete sampled traversal topology, root transitions, scene pixel fidelity or sustained60fps.')
path.with_name(path.stem+'-fractional-edges-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
