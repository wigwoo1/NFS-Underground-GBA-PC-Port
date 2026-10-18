"""Audit raw camera/object factorization before presentation interpolation."""
from pathlib import Path
import struct,json,math
p=Path('work/camera');frames=[]
def matrix(block):return struct.unpack('<12i',block)
def rotation(m):return [[m[c*3+r]/16384 for c in range(3)] for r in range(3)]
def inverse(a):
 det=a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])-a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])+a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]);assert abs(det)>1e-8
 return [[(a[(c+1)%3][(r+1)%3]*a[(c+2)%3][(r+2)%3]-a[(c+1)%3][(r+2)%3]*a[(c+2)%3][(r+1)%3])/det for c in range(3)] for r in range(3)],det
def mul(a,b):return [[sum(a[r][k]*b[k][c] for k in range(3)) for c in range(3)] for r in range(3)]
def point(a,v):return [sum(a[r][k]*v[k] for k in range(3)) for r in range(3)]
for refresh in [8758,8762,8766,8769,8773,8776,8780]:
 raw=(p/'motion-actual-scanline-assets'/f'{refresh}-native-complete-frame.bin').read_bytes();gn=struct.unpack_from('<I',raw,8)[0];geometry=raw[40:40+gn];offset=0;records=[]
 while offset<len(geometry):
  magic,kind,context,count=struct.unpack_from('<4I',geometry,offset);offset+=16;assert magic==0x3147534e and count==12;blocks=[]
  for i in range(count):
   n=struct.unpack_from('<I',geometry,offset)[0];offset+=4;blocks.append(geometry[offset:offset+n]);offset+=n
  records.append((kind,context,blocks))
 cameras=[matrix(b[4] if k==1 else b[3]) for k,c,b in records if k in (1,2)];assert cameras
 assert all(m==cameras[0] for m in cameras),'Different raw camera poses within scene'
 cm=cameras[0];cr=rotation(cm);ci,det=inverse(cr);models=[]
 for kind,context,b in records:
  if kind!=3:continue
  mm=matrix(b[2]);mr=rotation(mm);wr=mul(ci,mr);world_translation=point(ci,mm[9:12]);wp=[world_translation[k]-cm[9+k] for k in range(3)]
  # Recover world transform algebraically, without screen-space samples.
  reconstructed_rotation=mul(cr,wr);reconstructed_translation=point(cr,[wp[k]+cm[9+k] for k in range(3)])
  error=max([abs(reconstructed_rotation[r][c]-mr[r][c]) for r in range(3) for c in range(3)]+[abs(reconstructed_translation[k]-mm[9+k]) for k in range(3)])
  assert error<1e-7
  norms=[math.sqrt(sum(wr[r][c]**2 for r in range(3))) for c in range(3)]
  models.append(dict(model_matrix=list(mm),context=context,world_position=wp,world_rotation=wr,column_norms=norms,reconstruction_error=error))
 frames.append(dict(camera_matrix=list(cm),refresh=refresh,camera_source_count=len(cameras),camera_position=[-x for x in cm[9:12]],camera_rotation=cr,camera_determinant=det,models=models))
r=dict(result='PASS_RAW_CAMERA_OBJECT_FACTORIZATION',frames=frames,scope='Algebraic raw matrix reconstruction and shared camera audit; not rigid-pose interpolation, source clipping correctness or smooth60fps gameplay proof.')
(p/'owned-motion-source-audit.json').write_text(json.dumps(r,indent=2));print(dict(result=r['result'],frames=len(frames),models=sum(len(f['models']) for f in frames),camera_determinants=[f['camera_determinant'] for f in frames],model_norms=[m['column_norms'] for f in frames for m in f['models']]))
