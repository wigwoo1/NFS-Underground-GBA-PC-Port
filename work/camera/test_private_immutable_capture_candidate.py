import sys,json,ctypes as C,struct,hashlib
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'captured_setup','exec'))
from _owned_frame_capture_candidate import capture
Callback=C.CFUNCTYPE(C.c_int,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t))
state={'frame':frames[0],'fail':False,'oversize':False,'bad_written':False};calls=[]
def reader(epoch,refresh,out,capacity,written):
 frame=state['frame'];h=struct.unpack_from('<6I2Q',frame);calls.append((epoch,refresh,bool(out)))
 if (epoch,refresh)!=(h[6],h[1]):return 0
 written[0]=0x1000001 if state['oversize'] else len(frame)
 if not out:return 1
 if state['fail'] or capacity<len(frame):return 0
 C.memmove(out,frame,len(frame))
 if state['bad_written']:written[0]-=1
 return 1
callback=Callback(reader);address=C.cast(callback,C.c_void_p).value;results=[];held=[]
for frame in frames:
 state['frame']=frame;h=struct.unpack_from('<6I2Q',frame);owned=capture(address,h[6],h[1]);assert type(owned) is bytes and owned==frame;held.append(owned);results.append(hashlib.sha256(owned).hexdigest())
 for mode in ('fail','oversize','bad_written'):
  state[mode]=True
  try:capture(address,h[6],h[1])
  except ValueError:pass
  else:raise AssertionError(mode)
  state[mode]=False
 try:capture(address,h[6]+1,h[1])
 except ValueError:pass
 else:raise AssertionError('stale epoch')
 assert capture(address,h[6],h[1])==frame
assert held==frames
bad=bytearray(frames[-1]);bad[0]^=1;state['frame']=bytes(bad)
last=struct.unpack_from('<6I2Q',frames[-1])
try:capture(address,last[6],last[1])
except ValueError:pass
else:raise AssertionError('malformed header published')
state['frame']=bytes(40)+frames[-1][40:];h=struct.unpack_from('<6I2Q',state['frame'])
# Invalid identity rejected before calling even a valid callback.
try:capture(address,0,0)
except ValueError:pass
else:raise AssertionError('zero epoch')
out=dict(result='PASS_PRIVATE_IMMUTABLE_CAPTURE_COMPONENT',actual_captured_hashes=results,calls=len(calls),scope='Actual captured bytes through controlled native-call ABI callback; failure/recovery/lifetime tested, not actual live producer integration or performance proof.')
Path('work/camera/prototype-runs/private-immutable-capture-20261008.json').write_text(json.dumps(out,indent=2));print(out)

