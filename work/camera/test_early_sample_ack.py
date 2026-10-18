import inspect,textwrap,queue,threading,pickle,json
from types import SimpleNamespace
from owned_early_sample_ack import transform
from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter as Adapter
from owned_progressive_shared_transport_candidate import SharedConnection

payload=(.25,b'private-frame',b'geometry')
wire=pickle.dumps(payload,protocol=5);memory=SimpleNamespace(buf=bytearray(wire),size=len(wire))
connection=SimpleNamespace(recv=lambda:('sample_shared',0,0,1,len(wire)))
private=SharedConnection(connection,memory).recv()[3]
memory.buf[:]=b'\x00'*len(wire)
assert private==payload

source=textwrap.dedent(inspect.getsource(Adapter._run))
namespace=dict(Adapter._run.__globals__)
exec(compile(transform(source),'test-early-ack-run','exec'),namespace)
candidate=namespace['_run']
results=[]
for failure in (None,'ack','publish'):
    calls=[]
    class Service:
        generation=0;active=False;last_sample_timing={};last_terminal=None;last_start_timing={}
        def start(self,*args):self.active=True;calls.append('start')
        def take(self,*args):calls.append('take');return (0,0),private
        def acknowledge(self,token):
            assert token==(0,0);calls.append('ack')
            if failure=='ack':raise ValueError('ack failure')
        def finish(self):calls.append('finish');self.active=False
        def invalidate(self):calls.append('invalidate');self.active=False
        def close(self):calls.append('close')
    class Pair:
        alphas=(.25,);closed=False;cv=threading.Condition();submission_begin_ns=0;enqueued_ns=0
        def publish(self,p):
            assert p==payload;calls.append('publish')
            if failure=='publish':raise ValueError('publish failure')
        def finish(self):calls.append('pair_finish')
        def fail(self,error):calls.append('fail')
        def close(self):calls.append('pair_close')
    a=Adapter.__new__(Adapter);a.service=Service();a.jobs=queue.Queue();a.jobs.put((0,(None,SimpleNamespace(graph=SimpleNamespace(refresh=1))),(None,SimpleNamespace(graph=SimpleNamespace(refresh=2))),Pair()));a.jobs.put(None)
    a.lock=threading.Lock();a.closed=False;a.generation=0;a.space=SimpleNamespace(release=lambda:calls.append('release'))
    a.completed=0;a.stage_samples=[];a.protocol='test';a.errors=[];a.diagnostic_dropped=0
    candidate(a)
    assert calls[-2:]==['release','close'] and calls.index('ack')>calls.index('take')
    if failure is None:assert calls.index('ack')<calls.index('publish') and a.completed==1 and not a.errors
    else:
        assert a.completed==0 and len(a.errors)==1 and 'invalidate' in calls
        if failure=='ack':assert 'publish' not in calls
    results.append(dict(failure=failure,calls=calls))
Path=__import__('pathlib').Path
Path('early_sample_ack_component.json').write_text(json.dumps(dict(result='PASS_PRIVATE_COPY_ORDER_AND_FAILURE_RELEASE',cases=results),indent=2))
print('PASS actual shared receive detachment; transformed adapter success/ack failure/publication failure cleanup')
