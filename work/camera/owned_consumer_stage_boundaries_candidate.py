"""Opt-in scalar stage boundaries, preserving the active tail wrapper."""
def install():
    import owned_present_batch_trace_install_candidate as present
    import owned_ordered_tail_profile_install_candidate as tail
    if getattr(present,'consumer_boundaries_installed',False):return
    original=present.original
    if original.__code__.co_filename!='ordered-tail-profile-render':
        raise RuntimeError('Unexpected active consumer render chain')
    source=tail.render_source
    marker='dict(stage=name,elapsed_ns=now-ticks[-1])'
    if source.count(marker)!=1:raise RuntimeError('Consumer stage marker mismatch')
    source=source.replace(marker,'dict(stage=name,elapsed_ns=now-ticks[-1],started_ns=ticks[-1],completed_ns=now)')
    namespace=dict(original.__globals__)
    import os
    if os.environ.get('NFSUG_NATIVE_BACKDROP_PROFILE')=='1':
        if os.environ.get('NFSUG_BACKDROP_BATCH')=='1':raise RuntimeError('Conflicting backdrop diagnostic selections')
        from owned_backdrop_call_profile_candidate import transform
        source=transform(source,namespace)
    elif os.environ.get('NFSUG_BACKDROP_BATCH')=='1':
        from owned_backdrop_batch_candidate import transform
        source=transform(source,namespace)
    exec(compile(source,'consumer-stage-boundaries','exec'),namespace)
    present.original=namespace['render'];present.consumer_boundaries_installed=True
