import hashlib,json
from pathlib import Path
checks=[]
for label in ('large','small'):
 p=Path('work/camera/hud-sha256-'+label);message=Path(str(p)+'-message.bin').read_bytes();actual=Path(str(p)+'-digest.bin').read_bytes()
 assert len(actual)==32 and hashlib.sha256(message).digest()==actual
 assert int.from_bytes(message[:8],'little')==7
 checks.append({'fixture':label,'message_bytes':len(message),'epoch':7,'sha256':actual.hex(),'independent_match':True})
print(json.dumps({'result':'WINDOWS_SHA256_MATCHES_PYTHON_HASHLIB','checks':checks,'scope':'Full epoch-plus-stored-metadata-and-payload message, independent digest implementation; component proof only'},indent=2))
