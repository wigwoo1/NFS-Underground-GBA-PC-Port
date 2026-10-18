"""Retain existing HUD prefetch dispatch result; no command/order change."""
import owned_progressive_retirement_install_candidate as retirement
import owned_parent_publication_tail_install_candidate as publication_tail
source=publication_tail.source
needle='hud_prefetch_future.result(20)';assert source.count(needle)==1
source=source.replace(needle,'hud_prefetch_result=hud_prefetch_future.result(20)')
needle="slot_begin_ns=time.perf_counter_ns();alpha=slot['alpha']"
# Capture belongs to the new-pair branch; initialized for reused pairs as well.
first=source.index('\n')
source=source[:first+1]+' hud_prefetch_result=None\n'+source[first+1:]
needle="row['caller_stages']=dict("
pos=source.index(needle);end=source.index('\n',pos)
source=source[:end]+"\n   row['caller_stages']['hud_prefetch_dispatch']=None if hud_prefetch_result is None else hud_prefetch_result['renderer_dispatch']"+source[end:]
namespace=dict(retirement.owned_draw.__globals__);exec(compile(source,'progressive-hud-dispatch-trace','exec'),namespace)
retirement.owned_draw=namespace['_draw_intervals']
