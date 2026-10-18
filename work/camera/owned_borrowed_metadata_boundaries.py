"""Guarded caller clocks around the existing metadata queries."""
import inspect, textwrap, time

def profile_call(records, name, fn, *args):
    begin=time.perf_counter_ns();result=fn(*args);end=time.perf_counter_ns()
    records.append(dict(call=name,begin_ns=begin,end_ns=end))
    return result

def transform(source):
    marker='result=original_prepare(self,*args,**kwargs);values='
    if source.count(marker)!=1 or source.count('return result')!=1:
        raise RuntimeError('Unexpected borrowed metadata wrapper')
    source=source.replace(marker,'result=original_prepare(self,*args,**kwargs);metadata_calls=[];values=')
    for old,name,new in (
        ('self.source.nf_source_setup_ticks(values)','source_setup','self.source.nf_source_setup_ticks,values'),
        ('self.source.nf_source_input_ticks(input_values)','source_input','self.source.nf_source_input_ticks,input_values'),
        ('fn(discard_stats,C.sizeof(discard_stats))','hud_discard','fn,discard_stats,C.sizeof(discard_stats)'),
        ('fn(phase_cycles,C.sizeof(phase_cycles))','hud_cycles','fn,phase_cycles,C.sizeof(phase_cycles)'),
        ('self.source.nf_hud_borrowed_input_count()','borrowed_count','self.source.nf_hud_borrowed_input_count'),
    ):
        if source.count(old)!=1:raise RuntimeError('Metadata query marker mismatch: '+name)
        source=source.replace(old,"_metadata_call(metadata_calls,'"+name+"',"+new+')')
    return source.replace('return result',"result['borrowed_metadata_calls']=metadata_calls\n return result")

def install():
    import owned_hud_borrowed_rows_install_candidate as borrowed
    if getattr(borrowed,'metadata_boundaries_installed',False):return
    method=borrowed.prepare
    if method.__code__.co_freevars or not method.__code__.co_filename.endswith('owned_hud_borrowed_rows_install_candidate.py'):
        raise RuntimeError('Unexpected borrowed metadata function identity')
    namespace=dict(method.__globals__,_metadata_call=profile_call)
    exec(compile(transform(textwrap.dedent(inspect.getsource(method))),'borrowed-metadata-boundaries','exec'),namespace)
    # Keep function identity: the prepared-HUD closure already retains it.
    method.__globals__['_metadata_call']=profile_call
    method.__code__=namespace['prepare'].__code__
    borrowed.metadata_boundaries_installed=True
