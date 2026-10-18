"""Acknowledge a fully private packet before publishing renderer ownership."""
import dis,textwrap

def transform(source):
    marker='publication_begin=time.perf_counter_ns();pair.publish(packet);published=time.perf_counter_ns();self.service.acknowledge(token)'
    if source.count(marker)!=1:raise RuntimeError('Unexpected progressive publication source')
    timing='ack_sent_ns=time.perf_counter_ns()'
    if source.count(timing)!=1:raise RuntimeError('Unexpected acknowledgement timing source')
    return source.replace(marker,'self.service.acknowledge(token);acknowledged=time.perf_counter_ns();publication_begin=time.perf_counter_ns();pair.publish(packet);published=time.perf_counter_ns()').replace(timing,'ack_sent_ns=acknowledged')

def signature(fn):
    return [(x.opname,x.argval) for x in dis.get_instructions(fn)]

def install():
    from owned_progressive_preparation_adapter_candidate import ProgressivePreparationAdapter as Adapter
    import owned_long_preparation_rows_install_candidate as selected
    if getattr(Adapter,'early_sample_ack_selected',False):return
    source=textwrap.dedent(selected.source)
    namespace=dict(Adapter._run.__globals__)
    exec(compile(source,'early-ack-baseline-qualification','exec'),namespace)
    if signature(namespace['_run'])!=signature(Adapter._run):
        raise RuntimeError('Active preparation method differs from qualified source')
    exec(compile(transform(source),'early-private-sample-ack','exec'),namespace)
    Adapter._run=namespace['_run'];Adapter.early_sample_ack_selected=True
