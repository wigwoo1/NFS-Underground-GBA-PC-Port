"""Guarded instrumentation of a supplied active session prepare source."""
def transform(source):
    render = 'assert self.consumer.render(s,readback=False) is None'
    result = 'return dict('
    close = 'finally:assert s.nf_source_packets_close()==0'
    if any(source.count(marker) != 1 for marker in (render, result, close)):
        raise RuntimeError('Unexpected session prepare structure')
    source = source.replace(render, render + '\n  post_consumer_profile=dict(render_return_ns=time.perf_counter_ns())')
    source = source.replace(result, 'return dict(session_post_consumer=post_consumer_profile,')
    source = source.replace(close,
        'finally:\n'
        '  close_begin=time.perf_counter_ns()\n'
        '  assert s.nf_source_packets_close()==0\n'
        '  close_end=time.perf_counter_ns()\n'
        '  if "post_consumer_profile" in locals():\n'
        '   post_consumer_profile.update(close_begin_ns=close_begin,close_end_ns=close_end)')
    return source
