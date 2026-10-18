import ctypes as C,json,threading
from pathlib import Path
from owned_hud_shared_library_binding_candidate import configure_hud_library,HudFrameSnapshot
from owned_hud_preparation_timed_service_candidate import HudPreparationService
p=Path('work/camera');d=configure_hud_library(C.CDLL(str((p/'owned-hud-creation-profile-candidate.dll').resolve())))
r=json.loads((p/'prototype-runs/owned-native-1791434872973979000.json').read_text());folder=Path(r['live_preparation_profiles'][0]['capture']);frames=[(folder/name).read_bytes() for name in ('older.frame.bin','newer.frame.bin')]
def stats():
 a=(C.c_uint64*3)();assert d.nf_hud_owner_stats(a);return list(a)
assert stats()==[0,0,0]
service=HudPreparationService(d);a=service.submit(frames[0]);b=service.submit(frames[1]);a.result(5);b.result(5)
try:service.submit(frames[0])
except RuntimeError:pass
else:raise AssertionError('Unbounded pending owners')
first=service.take(a,5);assert first._base is frames[0] and first.token!=b.result().token
try:service.take(a)
except RuntimeError:pass
else:raise AssertionError('Duplicate creator transfer')
service.close();assert not service.thread.is_alive() and stats()==[1,5591040,1];first.close();assert stats()==[0,0,0];service.close()
# Close must wait for in-flight creation, then release its unclaimed creator.
entered=threading.Event();release=threading.Event();done=threading.Event()
def blocked(base,**kwargs):entered.set();assert release.wait(5);return HudFrameSnapshot(base,**kwargs)
service=HudPreparationService(d,factory=blocked);future=service.submit(frames[0]);assert entered.wait(5)
t=threading.Thread(target=lambda:(service.close(),done.set()));t.start();assert not done.wait(.05);release.set();t.join(5);assert done.is_set() and not service.thread.is_alive() and stats()==[0,0,0]
try:service.take(future)
except RuntimeError:pass
else:raise AssertionError('Closed transfer accepted')
# Validation failures remain bounded and shutdown releases all successful work.
service=HudPreparationService(d);bad=service.submit(b'bad');good=service.submit(frames[1]);good.result(5)
try:service.take(bad,5)
except ValueError:pass
else:raise AssertionError('Invalid frame accepted')
recovery=service.submit(frames[0]);recovery.result(5)
service.close();assert not service.thread.is_alive() and stats()==[0,0,0]
out=dict(result='PASS_BOUNDED_HUD_BACKGROUND_TRANSFER_CLOSE',capacity=2,actual_captured_frames=2,creator_transfer_once=True,claimed_owner_survives_service_close=True,inflight_close_barrier=True,failed_creation_cleanup=True,failed_submission_capacity_recovered=True,final_stats=stats(),scope='Native immutable HUD ownership service component only. No renderer/pause/live timing integration or gameplay claim.')
(p/'prototype-runs/hud-preparation-timed-service-20261009.json').write_text(json.dumps(out,indent=2));print(out)
