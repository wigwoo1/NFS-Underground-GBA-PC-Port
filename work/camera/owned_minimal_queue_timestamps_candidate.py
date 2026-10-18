"""Diagnostic submission/dispatch timestamps only; no queue or history policy change."""
import inspect,textwrap
import owned_long_preparation_rows_install_candidate as long_rows
from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter as Adapter
source=inspect.getsource(Adapter.submit);needle='self.jobs.put((self.generation,older,newer,pair));return future';assert source.count(needle)==1;source=source.replace(needle,'pair._diagnostic_submitted_ns=time.perf_counter_ns();'+needle)
ns=dict(Adapter.submit.__globals__);exec(compile(textwrap.dedent(source),'diagnostic-queue-submit','exec'),ns);Adapter.submit=ns['submit']
source=long_rows.source;needle='row=dict(protocol=self.protocol,';assert source.count(needle)==1;source=source.replace(needle,'row=dict(queue_submitted_ns=pair._diagnostic_submitted_ns,queue_dispatch_ns=started,queue_wait_ns=started-pair._diagnostic_submitted_ns,protocol=self.protocol,')
ns=dict(Adapter._run.__globals__);exec(compile(textwrap.dedent(source),'diagnostic-queue-dispatch','exec'),ns);Adapter._run=ns['_run']
