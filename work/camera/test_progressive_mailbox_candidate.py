from pathlib import Path
import json,threading
from owned_progressive_mailbox_candidate import ProgressiveMailbox,RetiredGeneration,immutable_size
# Uses real six complete source packets from the prior exact batch/publication regression.
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns)
packets=ns['packets'];fingerprint=ns['fingerprint'];expected=ns['expected']
m=ProgressiveMailbox();errors=[]
def produce():
 try:
  for i,p in enumerate(packets):m.publish(0,i,p)
 except BaseException as e:errors.append(repr(e))
t=threading.Thread(target=produce);t.start();received=[]
for i in range(6):
 token,p=m.take(0);assert token[:2]==(0,i);received.append(fingerprint(p));m.acknowledge(token)
t.join(10);assert not t.is_alive() and not errors and received==expected and m.stats()['retained_bytes']==0
# Reset drops pending owners but keeps outstanding lease until its explicit acknowledgement.
m=ProgressiveMailbox(capacity=1);token=m.publish(0,0,packets[0]);lease,p=m.take(0);entered=threading.Event();retired=[]
def blocked():
 entered.set()
 try:m.publish(0,1,packets[1])
 except RetiredGeneration:retired.append(True)
t=threading.Thread(target=blocked);t.start();assert entered.wait(5);new=m.retire();t.join(5)
assert not t.is_alive() and retired==[True] and fingerprint(p)==expected[0] and m.stats()['leased']==1
try:m.publish(new,0,packets[1],timeout=0)
except TimeoutError:pass
else:raise AssertionError('Unacknowledged lease ignored')
m.acknowledge(lease);assert m.stats()['retained_bytes']==0
m.publish(new,0,packets[1]);m.close();assert m.stats()['pending']==0 and m.stats()['retained_bytes']==0
for action in (lambda:m.take(new,0),lambda:m.publish(new,1,packets[2],0)):
 try:action()
 except RetiredGeneration:pass
 else:raise AssertionError('Closed mailbox accepted work')
for payload in (bytearray(1),[1],{'mutable':1}):
 try:ProgressiveMailbox().publish(0,0,payload)
 except ValueError:pass
 else:raise AssertionError('Mutable payload accepted')
small=ProgressiveMailbox(budget=1)
try:small.publish(0,0,packets[0])
except ValueError:pass
else:raise AssertionError('Budget ignored')
out=dict(result='PASS_PROGRESSIVE_MAILBOX_REAL_SAMPLES',samples=6,exact_batch_hashes=True,reset_unblocks_stale_producer=True,unacknowledged_owner_preserved=True,closed_generation_rejected=True,mutable_payloads_rejected=True,budget_enforced=True,scope='Threaded immutable ownership component only; no spawned process stream or native render integration.')
Path('outputs/nfsug-native-renderer/camera-research/progressive-mailbox-20261009.json').write_text(json.dumps(out,indent=2));print(out)
