"""Isolated 1024-record diagnostic; ordinary 128-record trace unchanged."""
import inspect

def install():
    import owned_fine_deadline_trace as trace
    import owned_native_transaction_interval_totals_candidate as module
    if getattr(module, 'expanded_deadline_trace_installed', False):
        return
    if module.LongIntervalTotals is not trace.DeadlineTrace:
        raise RuntimeError('Unexpected selected deadline observer')
    source = inspect.getsource(trace.DeadlineTrace)
    for old in ('len(self.deadline_events)>128', 'capacity=128', 'Worst128'):
        if source.count(old) != 1:
            raise RuntimeError('Deadline capacity source guard mismatch')
    source = source.replace('len(self.deadline_events)>128','len(self.deadline_events)>1024').replace('capacity=128','capacity=1024').replace('Worst128','Worst1024')
    namespace = dict(trace.__dict__)
    # Preserve the original aggregate base, avoiding double observation.
    assert namespace['Base'] is trace.Base
    exec(compile(source, 'isolated-expanded-deadline-trace', 'exec'), namespace)
    module.LongIntervalTotals = namespace['DeadlineTrace']
    module.expanded_deadline_trace_installed = True
    print('EXPANDED_DEADLINE_TRACE_SELECTED 1024', flush=True)
