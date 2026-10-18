"""Opt-in bounded scalar submission-to-dispatch evidence; scheduling unchanged."""
import inspect,textwrap
from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter as Adapter
source=inspect.getsource(Adapter.submit)
needle='self.jobs.put((self.generation,older,newer,pair));return future'
assert source.count(needle)==1
source=source.replace(needle,'pair._queue_submitted_ns=time.perf_counter_ns();'+needle)
ns=dict(Adapter.submit.__globals__);exec(compile(textwrap.dedent(source),'queue-lead-submit','exec'),ns);Adapter.submit=ns['submit']
from owned_long_preparation_rows_install_candidate import source as long_source
source=long_source
needle='row=dict(protocol=self.protocol,';assert source.count(needle)==1
source=source.replace(needle,'row=dict(queue_submitted_ns=pair._queue_submitted_ns,queue_dispatch_ns=started,protocol=self.protocol,')
source=source.replace('started=time.perf_counter_ns();sample_rows=[]','started=time.perf_counter_ns();sample_rows=[];tail=None')
source=source.replace('row=dict(queue_submitted_ns=',"row=dict(previous_request_tail=getattr(self,'_queue_previous_tail',None),queue_submitted_ns=")
needle='    if len(self.stage_samples)<2048:';assert source.count(needle)==1
source=source.replace(needle,"    tail=dict(completed_ns=row['completed_ns'],report_append_begin_ns=time.perf_counter_ns())\n"+needle)
needle='    else:self.diagnostic_dropped+=1';assert source.count(needle)==1
source=source.replace(needle,needle+"\n    tail['report_append_end_ns']=time.perf_counter_ns()")
needle='    self.space.release();job=pair=older=newer=None';assert source.count(needle)==1
source=source.replace(needle,"    self.space.release()\n    if tail is not None:\n     tail['release_end_ns']=time.perf_counter_ns();self._queue_previous_tail=tail\n    job=pair=older=newer=None")
ns=dict(Adapter._run.__globals__);exec(compile(textwrap.dedent(source),'queue-lead-dispatch','exec'),ns);Adapter._run=ns['_run']
