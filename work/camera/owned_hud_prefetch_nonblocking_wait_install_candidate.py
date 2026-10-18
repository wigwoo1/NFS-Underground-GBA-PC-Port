"""Install an isolated nonblocking HUD-future handoff candidate."""
import inspect
import textwrap
import time

def _patch(method, source, assign):
    source=textwrap.dedent(source)
    old_enqueue="    hud_prefetch_future=self.native_worker.prefetch_hud((previous[0],current),epoch,generation)"
    if source.count(old_enqueue)!=1:
        old_enqueue="    hud_prefetch_future=self.native_worker.prefetch_hud((previous[0],),epoch,generation)"
    assert source.count(old_enqueue)==1
    observer=old_enqueue+"""\n    hud_prefetch_observation={\"completed_ns\":None,\"result\":None,\"error\":None}
    def observe_hud_prefetch(done):
     hud_prefetch_observation[\"completed_ns\"]=time.perf_counter_ns()
     try:hud_prefetch_observation[\"result\"]=done.result()
     except BaseException as error:hud_prefetch_observation[\"error\"]=error
    hud_prefetch_future.add_done_callback(observe_hud_prefetch)"""
    source=source.replace(old_enqueue,observer)
    old_wait="    hud_prefetch_wait_begin_ns=time.perf_counter_ns();hud_prefetch_result=hud_prefetch_future.result(20);hud_prefetch_wait_end_ns=time.perf_counter_ns()"
    new_wait="    hud_prefetch_wait_begin_ns=time.perf_counter_ns();hud_prefetch_wait_end_ns=hud_prefetch_wait_begin_ns;hud_prefetch_result=None"
    assert source.count(old_wait)==1
    source=source.replace(old_wait,new_wait)
    commit="   row=self.native_commit.run(owned,epoch,generation,previous[2],refresh,slot['index'],alpha,slot['deadline_ns'])"
    fence=commit+"""\n   if row['native_result']==1:
    if hud_prefetch_observation[\"completed_ns\"] is None:raise RuntimeError('HUD prefetch did not complete before successful queued prepare')
    if hud_prefetch_observation[\"error\"] is not None:raise hud_prefetch_observation[\"error\"]
    hud_prefetch_result=hud_prefetch_observation[\"result\"]
    if type(hud_prefetch_result) is not dict:raise RuntimeError('HUD prefetch returned no result')
   elif hud_prefetch_observation[\"completed_ns\"] is not None:
    hud_prefetch_result=hud_prefetch_observation[\"result\"]"""
    assert source.count(commit)==1
    source=source.replace(commit,fence)
    dispatch="   row['caller_stages']['hud_prefetch_dispatch']=hud_prefetch_result.get('renderer_dispatch')"
    dispatch_new="   row['caller_stages']['hud_prefetch_dispatch']=hud_prefetch_result.get('renderer_dispatch') if type(hud_prefetch_result) is dict else None\n   row['caller_stages']['hud_prefetch_wait_elided']=True\n   row['caller_stages']['hud_prefetch_completed_ns']=hud_prefetch_observation['completed_ns']"
    assert source.count(dispatch)==1
    source=source.replace(dispatch,dispatch_new)
    namespace=dict(method.__globals__);namespace['time']=time
    exec(compile(source,'nonblocking_hud_draw_intervals','exec'),namespace)
    patched=namespace['_draw_intervals']
    assign(patched)
    return dict(installed=True,queue_fence='successful render-prepare Future completes after FIFO HUD-prefetch callback',source_guard='single enqueue/wait/commit replacement; candidate compiled')

def install_live():
    import live_native_hud_prefetch_generation_candidate as live
    return _patch(live.NativeLiveWorker._draw_intervals,inspect.getsource(live.NativeLiveWorker._draw_intervals),lambda method:setattr(live.NativeLiveWorker,'_draw_intervals',method))

def install_retirement():
    import owned_progressive_retirement_install_candidate as retirement
    import owned_hud_pair_lookahead_install_candidate as lookahead
    return _patch(retirement.owned_draw,lookahead.source,lambda method:setattr(retirement,'owned_draw',method))

if __name__=='__main__':
    print(install_live())
