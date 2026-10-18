from pathlib import Path
import threading,json
from concurrent.futures import CancelledError
from owned_progressive_pair_candidate import ProgressivePair
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns)
p=ProgressivePair(ns['alphas']);p.publish(ns['packets'][0]);assert p.first.result(1) is p and not p.complete
ready=threading.Event();result=[]
def consumer():
 ready.set();result.append(p.sample(ns['alphas'][1]))
t=threading.Thread(target=consumer);t.start();assert ready.wait(1)
for packet in ns['packets'][1:]:p.publish(packet)
p.finish();t.join(5);assert not t.is_alive() and result
for a,packet,expected in zip(ns['alphas'],ns['packets'],ns['expected']):
 f,c,m,b,d=p.sample(a);o,mask,total,diag=p.source_masks[a]
 reconstructed=(a,f,bytes(c),bytes(m),bytes(b),bytes(o),bytes(mask),total,json.dumps(d,sort_keys=True).encode(),json.dumps(diag,sort_keys=True).encode(),p.source_cameras)
 assert ns['fingerprint'](reconstructed)==expected
held=p.sample(ns['alphas'][0]);p.close();assert bytes(held[0])==bytes(ns['packets'][0][1])
try:p.sample(ns['alphas'][0])
except CancelledError:pass
else:raise AssertionError('Retired pair exposed')
empty=ProgressivePair(ns['alphas']);empty.close();assert empty.first.cancelled()
failed=ProgressivePair(ns['alphas']);failed.publish(ns['packets'][0]);failed.fail(RuntimeError('Injected later preparation failure'))
try:failed.sample(ns['alphas'][0])
except RuntimeError as e:assert str(e)=='Injected later preparation failure'
else:raise AssertionError('Ready sample exposed after failure')
failed.close()
# Decode errors cannot fulfill first-ready future with a partially constructed sample.
bad=ProgressivePair(ns['alphas']);packet=list(ns['packets'][0]);packet[2]=b'bad'
try:bad.publish(tuple(packet))
except ValueError:pass
else:raise AssertionError('Truncated camera accepted')
assert not bad.first.done() and not bad.samples;bad.close()
out=dict(result='PASS_PROGRESSIVE_PAIR_FIRST_FUTURE',samples=6,first_ready_before_complete=True,exact_arrays_masks=True,retirement_rejected=True,scope='Sample owner component; not live preparation service integration.')
Path('outputs/nfsug-native-renderer/camera-research/progressive-pair-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
