"""Isolated measurement of the active prepared-HUD result wrapper."""
import inspect
import textwrap
import time

def transform(source):
    markers = ('result=original(self,*args,**kwargs)',
               "result['native_prepared_hud_rows_used']=self.source.nf_hud_prepared_rows_used()",
               "result['native_prepared_hud_bytes']=self.source.nf_hud_owner_prepared_bytes()")
    if any(source.count(marker) != 1 for marker in markers):
        raise RuntimeError('Unexpected prepared HUD return wrapper')
    source = source.replace(markers[0], markers[0]+'\n wrapper_begin=time.perf_counter_ns()')
    source = source.replace(markers[1], markers[1]+'\n rows_returned=time.perf_counter_ns()')
    source = source.replace(markers[2], markers[2]+"\n result['prepared_hud_return_profile']=dict(wrapper_begin_ns=wrapper_begin,rows_returned_ns=rows_returned,bytes_returned_ns=time.perf_counter_ns())")
    return source

def install():
    import owned_hud_borrowed_rows_install_candidate as selected
    if getattr(selected, 'prepared_hud_return_boundaries_installed', False):
        return
    method = selected.PrefetchSession.prepare
    if not method.__code__.co_filename.endswith('owned_prepared_hud_live_install.py'):
        raise RuntimeError('Current prepared HUD wrapper is not selected')
    source = textwrap.dedent(inspect.getsource(method))
    namespace = dict(method.__globals__, **inspect.getclosurevars(method).nonlocals, time=time)
    exec(compile(transform(source), 'prepared-hud-return-boundaries', 'exec'), namespace)
    selected.PrefetchSession.prepare = namespace['prepare']
    selected.prepared_hud_return_boundaries_installed = True
