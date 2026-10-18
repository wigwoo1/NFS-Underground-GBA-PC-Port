"""Bounded exact-endpoint lookahead inside existing retirement wrapper."""
import owned_progressive_retirement_install_candidate as retirement
method=retirement.owned_draw
source=retirement.source
old='self.native_worker.prefetch_hud((previous[0],),epoch,generation)'
assert source.count(old)==1
source=source.replace(old,'self.native_worker.prefetch_hud((previous[0],current),epoch,generation)')
namespace=dict(method.__globals__)
exec(compile(source,'bounded-hud-pair-lookahead','exec'),namespace)
retirement.owned_draw=namespace['_draw_intervals']
assert retirement.base.NativeLiveWorker._draw_intervals is retirement.draw
print('HUD_PAIR_LOOKAHEAD_SELECTED',flush=True)
