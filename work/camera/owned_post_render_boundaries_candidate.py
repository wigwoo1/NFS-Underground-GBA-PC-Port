"""Opt-in timestamps for the current outer HUD profile wrapper."""
import inspect
import time


def transform(source):
    markers = (
        ' result=original(self,*args,**kwargs)',
        ' ticks=Ticks();assert self.d.nf_d3d_hud_phase_ticks(ticks,C.sizeof(ticks))==0',
        " rows[0]['native_hud_ticks']=list(ticks)",
    )
    if any(source.count(marker) != 1 for marker in markers):
        raise RuntimeError('Unexpected outer HUD profile wrapper')
    source = source.replace(markers[0], markers[0] + '\n wrapper_begin=time.perf_counter_ns()')
    source = source.replace(markers[1],
        ' ticks=Ticks();ticks_ready=time.perf_counter_ns()\n'
        ' assert self.d.nf_d3d_hud_phase_ticks(ticks,C.sizeof(ticks))==0\n'
        ' ticks_returned=time.perf_counter_ns()')
    source = source.replace(markers[2], markers[2] +
        "\n rows[0]['post_render_profile']=dict(wrapper_begin_ns=wrapper_begin,ticks_ready_ns=ticks_ready,ticks_returned_ns=ticks_returned,profile_finished_ns=time.perf_counter_ns())")
    return source


def install():
    import owned_present_batch_trace_install_candidate as present
    if getattr(present, 'post_render_boundaries_installed', False):
        return
    if present.OwnedD3DConsumer.render is not present.render:
        raise RuntimeError('Outer render wrapper was replaced')
    namespace = dict(present.render.__globals__, time=time)
    exec(compile(transform(inspect.getsource(present.render)), 'post-render-boundaries', 'exec'), namespace)
    present.render = namespace['render']
    present.OwnedD3DConsumer.render = present.render
    present.post_render_boundaries_installed = True
