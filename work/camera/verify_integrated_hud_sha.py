import hashlib,json,struct
from pathlib import Path
checks=[]
for i in (1,2):
 p=Path('work/camera/hud-sha-integrated-'+str(i));m=Path(str(p)+'-message.bin').read_bytes();d=Path(str(p)+'-digest.bin').read_bytes()
 assert len(d)==32 and hashlib.sha256(m).digest()==d
 assert struct.unpack_from('<Q',m)[0]==7 and struct.unpack_from('<I',m,16)[0]==258
 checks.append({'fixture':i,'bytes':len(m),'sha256':d.hex(),'layout':258,'independent_match':True})
print(json.dumps({'result':'INTEGRATED_POOL_SHA256_MATCHES_HASHLIB','checks':checks},indent=2))
