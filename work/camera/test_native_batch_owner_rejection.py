import sys,struct,json,ctypes as C
from pathlib import Path
from owned_native_presentation_batch import OwnedPresentationBatch
from owned_sky_sampler import SkySamples
sys.argv=['setup','work/camera/prototype-runs/owned-native-1791352541751468500.json','0','unused'];ns={}
exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'setup','exec'),ns)
checks=[]
try:
 value=ns['prepared'].sample(.5);epoch=ns['scenes'][0].identity[0];older,newer=[s.identity[1] for s in ns['scenes']];sky=SkySamples(bytes(15136),bytes(15136),.5,0x06002940)
 row=(older,newer,0,0,.5,value,sky);OwnedPresentationBatch(epoch,[row]);original=value[0]
 cases=[]
 bad=bytearray(original);struct.pack_into('<Q',bad,24,epoch+1);cases.append(('epoch',(*value[:0],bytes(bad),*value[1:]),sky))
 bad=bytearray(original);struct.pack_into('<I',bad,4,newer+1);cases.append(('refresh', (bytes(bad),*value[1:]),sky))
 bad=bytearray(original);struct.pack_into('<I',bad,8,1);cases.append(('layout',(bytes(bad),*value[1:]),sky))
 camera=(C.c_double*12)(*value[1]);camera[0]=float('nan');cases.append(('pose_nan',(value[0],camera,*value[2:]),sky))
 bounds=(C.c_double*len(value[3]))(*value[3]);bounds[0]=float('inf');cases.append(('bounds_inf',(*value[:3],bounds,value[4]),sky))
 cases.append(('sky_nan',value,SkySamples(sky.lower,sky.upper,float('nan'),sky.destination)))
 cases.append(('sky_destination',value,SkySamples(sky.lower,sky.upper,.5,0)))
 cases.append(('short_frame',(b'bad',*value[1:]),sky))
 for name,v,k in cases:
  try:OwnedPresentationBatch(epoch,[(older,newer,0,0,.5,v,k)])
  except ValueError:checks.append(name)
  else:raise AssertionError(name)
 assert value[0]==original
finally:ns['prepared'].close();ns['history'].close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-batch-owner-validation-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',rejected=checks,scope='Actual captured moving scene; Python owner rejection before native/GPU dispatch, valid batch accepted; full-motion GPU parity checked separately.'),indent=2));print('PASS malformed batch owners',checks)
