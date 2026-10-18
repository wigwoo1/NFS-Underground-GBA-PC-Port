"""Compare world-source projection with actual original prepared road edges."""
from pathlib import Path
import json,struct,math
p=Path('outputs/nfsug-native-renderer/camera-research');a=json.loads((p/'original-road5-scene10-audit.json').read_text())['road'];s=json.loads((p/'original-pose-scene10/native-world-audit.json').read_text())['surfaces'][5]
b=Path('work/camera/scene10-original-pose.packet').read_bytes();_,off,size=struct.unpack_from('<3I',b,32);m=b[off:off+size];assert struct.unpack_from('<I',m)[0]==0x324d464e
cx,cy,scale=struct.unpack_from('<3d',m,24);px,py,pz,x,y,z,w=struct.unpack_from('<7d',m,48);rows=((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),(2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),(2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)))
prepared=bytes.fromhex(a['prepared_hex']);results=[]
for i,v in enumerate(s['vertices']):
 delta=[a-b for a,b in zip(v,(px,py,pz))];camera=[sum(a*b for a,b in zip(row,delta)) for row in rows];projected=[cx+scale*camera[0]/camera[2],cy+scale*camera[1]/camera[2]]
 # Original road prepared list begins at source vertex1, then2,3,0.
 edge=struct.unpack_from('<6i',prepared,((i+3)%4)*24);original=list(edge[:2]);error=max(abs(a-b) for a,b in zip(projected,original));assert error<1,(i,error)
 results.append(dict(vertex=i,world=v,camera=camera,continuous_projected=projected,original_integer_projected=original,max_error=error))
area=abs(sum(results[i]['continuous_projected'][0]*results[(i+1)%4]['continuous_projected'][1]-results[(i+1)%4]['continuous_projected'][0]*results[i]['continuous_projected'][1] for i in range(4)))/2
report=dict(result='PASS',vertices=results,continuous_original_pixel_area=area,scope='Actual final prepared road polygon versus original-pose world projection within one original pixel. Does not verify final coverage/overdraw or motion timing.')
(p/'road5-original-projection-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

