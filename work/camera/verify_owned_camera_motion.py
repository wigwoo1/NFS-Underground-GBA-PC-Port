"""Independent camera sampling from immutable submission endpoints, not rounded packet poses."""
import ctypes as C,json,math,struct,sys,hashlib
from pathlib import Path
m=Path(sys.argv[1]);s=json.loads(m.read_text(encoding='utf-8-sig'));prefix=s['prefix'];d=C.CDLL(str(Path(__file__).parent/'visibility-probe-wide.dll'));d.nf_pose_sample.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p];checks=[];previous=None
source_path=Path(prefix+'-dense-source-identity-verification.json');source=json.loads(source_path.read_text());endpoint_cameras={}
for row in source['original_endpoints']:
 packet=Path(row['path']).read_bytes();assert hashlib.sha256(packet).hexdigest()==row['sha256'];off=struct.unpack_from('<I',packet,36)[0];model=packet[off:];at=struct.unpack_from('<I',model,8)[0] if model[:4]==b'NML1' else 0;endpoint_cameras[row['identity'][3]]=struct.unpack_from('<7d',model,at+48)
for i in range(1,s['dense_frames']+1):
 base=prefix+f'-dense-{i:02d}';meta=json.loads(Path(base+'-native-source.json').read_text());raw=Path(base+'-owned-cameras.bin').read_bytes();magic,version,n,commands=struct.unpack_from('<4I',raw);assert magic==0x5043464e and version==1 and len(raw)==24+56*(n+commands);alpha=struct.unpack_from('<d',raw,16)[0];assert abs(alpha-meta['alpha'])<1e-10
 poses=[struct.unpack_from('<7d',raw,24+j*56) for j in range(n+commands)];assert n==2 and commands==0,'Per-command held cameras require separate audit'
 a,b=poses[:2];assert a==endpoint_cameras[meta['source_refreshes'][0]] and b==endpoint_cameras[meta['source_refreshes'][1]],'Owned camera does not match original replay endpoint'
 qa=list(a[3:]);qb=list(b[3:]);dot=sum(x*y for x,y in zip(qa,qb))
 if dot<0:qb=[-v for v in qb];dot=-dot
 dot=min(1,dot);u,v=1-alpha,alpha
 if dot<.9995:theta=math.acos(dot);u=math.sin((1-alpha)*theta)/math.sin(theta);v=math.sin(alpha*theta)/math.sin(theta)
 q=[u*x+v*y for x,y in zip(qa,qb)];norm=math.sqrt(sum(v*v for v in q));expected=[(1-alpha)*a[j]+alpha*b[j] for j in range(3)]+[v/norm for v in q]
 aa=(C.c_double*7)(*a);bb=(C.c_double*7)(*b);actual=(C.c_double*7)();assert d.nf_pose_sample(aa,bb,alpha,actual);error=max(abs(x-y) for x,y in zip(expected,actual));assert error<1e-12
 step=None if previous is None else math.dist(previous[:3],actual[:3]);checks.append(dict(index=i,target=meta['target'],alpha=alpha,camera_export_sha256=hashlib.sha256(raw).hexdigest(),effective_camera=list(actual),independent_sample_max_error=error,position_step=step));previous=list(actual)
r=dict(result='PASS',checks=checks,scope='Immutable renderer camera override endpoints independently sampled and cross-checked against actual nf_pose_sample. Hash-validated original replay endpoint cameras match owned exports exactly. Per-command held cameras, image/geometry fidelity and scanout/fullscene60fps require separate checks.')
Path(prefix+'-owned-camera-motion.json').write_text(json.dumps(r,indent=2));print(json.dumps(dict(result='PASS',frames=len(checks),max_error=max(c['independent_sample_max_error'] for c in checks),position_steps=[c['position_step'] for c in checks])))
