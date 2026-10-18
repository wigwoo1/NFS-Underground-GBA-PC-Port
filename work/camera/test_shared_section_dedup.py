import json
from multiprocessing.shared_memory import SharedMemory
import owned_shared_payload as transport
payload={'tails':[b'x'*1000000], 'samples':[(.25,(b'geometry'*100,0,b'camera',None,b'bounds',{})),(.75,(b'geometry'*100,0,b'camera',None,b'bounds',{}))]}
class UnhashableTail(bytes):
 def __hash__(self):raise AssertionError('Already unique tail hashed again')
transport.DEDUPLICATE_BYTES=True
_,sections=transport.parts({'tails':[UnhashableTail(b'large-tail')], 'samples':[b'prefix',b'prefix']})
assert len(sections)==2
m=SharedMemory(create=True,size=2000000)
try:
 transport.DEDUPLICATE_BYTES=False
 baseline=transport.write_payload(m,payload,7,1)
 a=transport.read_payload(baseline,7,m)
 transport.DEDUPLICATE_BYTES=True
 candidate=transport.write_payload(m,payload,7,2)
 b=transport.read_payload(candidate,7,m)
 assert a==b==payload
 assert candidate[3]<baseline[3]
 assert b['samples'][0][1][0] is b['samples'][1][1][0]
 try:transport.read_payload(baseline,7,m)
 except ValueError:pass
 else:raise AssertionError('Stale serial accepted')
 m.buf[:]=b'\0'*m.size
 assert b==payload
finally:m.close();m.unlink()
assert b==payload
print(json.dumps(dict(result='PASS',baseline_bytes=baseline[3],candidate_bytes=candidate[3],scope='Exact shared transport sections, stale serial rejection, private bytes survive overwrite and mapping close')))
