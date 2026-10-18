"""Isolated native GPU support for one changing wall portal, with owned camera overrides."""
import json,struct,sys,os,subprocess,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
m=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'));prefix=m['prefix'];p=Path(__file__).parent.resolve()
def view(i):
 base=prefix+f'-dense-{i:02d}';raw=Path(base+'-native-scene.bin').read_bytes();s={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+j*12) for j in range(5))};count=struct.unpack_from('<I',s[5],4)[0];world=struct.unpack_from('<I',s[2],4)[0];ids=[struct.unpack_from('<5I',s[5],8+j*20) for j in range(world)];at=8+count*20;assert s[5][at:at+4]==b'NFB2';bounds=[struct.unpack_from('<4H',s[5],at+16+j*8) for j in range(world)];return base,raw,ids,bounds
first=view(1);last=view(m['dense_frames']);candidates=[(j,k) for j,k in enumerate(first[2]) if k[0]==2 and k in last[2] and first[3][j]!=last[3][last[2].index(k)]];assert candidates
ordinal,key=max(candidates,key=lambda pair:(first[3][pair[0]][1]-first[3][pair[0]][0])*(first[3][pair[0]][3]-first[3][pair[0]][2]));checks=[]
for index in [1,m['dense_frames']]:
 base,raw,ids,bounds=view(index);j=ids.index(key);left,right,top,bottom=bounds[j];assert 0<=left<=right<=240 and 0<=top<=bottom<=160
 left=left//2*2;right=min(240,right//2*2+2);bottom=min(160,bottom+2)
 support=[int(np.ceil(300+left*13.5-.5)),int(np.ceil(300+right*13.5-.5)),int(np.ceil(top*13.5-.5)),int(np.ceil(bottom*13.5-.5))]
 poses=Path(base+'-owned-cameras.bin').read_bytes();assert struct.unpack_from('<4I',poses)==(0x5043464e,1,2,0);camera=Path(base+'-support-camera.bin');camera.write_bytes(poses[24:136])
 env={k:v for k,v in os.environ.items() if not k.startswith('NF_')};env.update(NF_ENDPOINT_CAMERA_PAIR=str(camera),NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
 images=[]
 for commands,label in [('4294967200','empty'),(str(j),'wall')]:
  target=base+'-support-'+label+'.ppm';subprocess.run([str(p/'endpoint-scene-road-order-preview.exe'),base+'-native-scene.bin',target],env=dict(env,NF_ENDPOINT_COMMANDS=commands),check=True,capture_output=True);images.append(np.asarray(Image.open(target+'-0.ppm')))
 mask=np.any(images[0]!=images[1],axis=2);inside=np.zeros(mask.shape,bool);x0,x1,y0,y1=support;inside[max(0,y0):min(2160,y1),max(0,x0):min(3840,x1)]=True;outside=int((mask&~inside).sum());assert outside==0
 checks.append(dict(frame=index,ordinal=j,identity=key,packet_sha256=hashlib.sha256(raw).hexdigest(),portal=bounds[j],support=support,changed_pixels=int(mask.sum()),outside_support=outside))
r=dict(result='PASS',checks=checks,scope='Two isolated native wall draws with actual retained camera endpoints confined to their owned changing portal support. Diagnostic command isolation only; no original rectangle fidelity, visibility completeness or fullscene60fps proof.');Path(prefix+'-selection-portal-support.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
