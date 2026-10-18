import ctypes as C,threading,json
from owned_async_crop_ledger import CropLedger
class Fn:
 def __init__(self,f):self.f=f
 def __call__(self,*args):return self.f(*args)
class GPU:
 def __init__(self):
  self.ids=[];self.ready=False
  self.nf_crop_enqueue=Fn(self.enqueue);self.nf_crop_poll=Fn(self.poll)
 def enqueue(self,i,x,y):
  if len(self.ids)==3:return 2
  self.ids.append(i);return 0
 def poll(self,i,b,n):
  if not self.ids:return 2
  if not self.ready:return 0
  ident=self.ids.pop(0);C.cast(i,C.POINTER(C.c_uint64))[0]=ident;C.memset(b,ident,n);return 1
row=dict(epoch=2,generation=3,display_index=180,source_older=10,refresh=14,alpha=.5)
g=GPU();l=CropLedger(g,5)
for n in range(4):assert l.enqueue(dict(row,display_index=180+n),n+1,2)==(n<3)
row['alpha']=.9;assert all(x['alpha']==.5 for x in l.pending.values())
g.ready=True;l.poll();assert [x['capture_id'] for x in l.completed]==[1,2,3]
g.ready=False;assert l.enqueue(row,5,2);assert not l.enqueue(row,6,2)
wrong=[]
def other():
 try:l.poll()
 except RuntimeError:wrong.append(True)
t=threading.Thread(target=other);t.start();t.join();assert wrong==[True]
l.retire();r=l.report();assert r['attempts']==5 and len(r['completed'])==3 and len(r['omitted'])==1 and len(r['retired'])==1 and not r['pending']
g=GPU();l=CropLedger(g);g.ids=[999];g.ready=True
try:l.poll()
except RuntimeError:pass
else:raise AssertionError('Unknown identity accepted')
print('PASS stubbed delayed identity, copied metadata, capacity omissions, bounded limit, wrong owner, close retirement, unknown identity rejection')
