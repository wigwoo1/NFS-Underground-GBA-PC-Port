"""Actual saved fullscene pixels with unchanged and resource-reuse transaction backends."""
import sys,json,ctypes as C,hashlib
from pathlib import Path
import numpy as np
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json']
setup=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0]
exec(compile(setup,'actual_saved_scene_setup','exec'))
from owned_native_source_hud_cache_lease_session_candidate import NativeSourceSession
original_cdll=C.CDLL
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True)
boundaries=[]
for scene in scenes:
 record=next(x for x in report['sky_capture_records'] if (x['epoch'],x['publication'])==scene.identity)
 origin=record['asset_origin'];offset=record['source']-0x08000000
 boundaries.append(SkyBoundary(record['epoch'],record['publication'],record['angle'],240,64,0,record['source'],origin,0x06002940,rom[offset:offset+15136]))
origin=boundaries[0].asset_origin;asset=SkyAsset(origin,rom[origin-0x08000000:origin-0x08000000+15376])
def run(library):
 loads=[]
 def load(path,*args,**kwargs):
  if Path(path).name.startswith('owned-d3d-'):
   path=str(Path(path).with_name(library));loads.append(path)
  return original_cdll(path,*args,**kwargs)
 C.CDLL=load;session=None;hashes=[]
 try:
  session=NativeSourceSession();assert len(loads)==1
  if hasattr(session.consumer.d,'nf_d3d_measured_stages'):
   initial=(C.c_uint64*12)();assert session.consumer.d.nf_d3d_measured_stages(initial,C.sizeof(initial))==0 and not any(initial)
  if hasattr(session.consumer.d,'nf_d3d_return_execution'):
   profile=(C.c_uint64*4)();getter=session.consumer.d.nf_d3d_return_execution;getter.argtypes=[C.c_void_p,C.c_size_t]
   assert getter(profile,C.sizeof(profile))==0 and not any(profile)
   assert getter(None,C.sizeof(profile))==37 and getter(profile,C.sizeof(profile)-1)==37
  for index,item in enumerate(expected*2):
   alpha=item['alpha'];frame,camera,models,bounds,detail=cached.sample(alpha);offsets,mask,total,_=cached.source_masks[alpha]
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*cached.source_cameras,alpha,offsets,mask,total).attach_sky(asset.sample_continuous(*boundaries,alpha))
   session.draw(owned,1,1,index)
   rgba=C.create_string_buffer(3840*2160*4);assert session.consumer.d.nf_d3d_read(rgba,len(rgba))==0
   if hasattr(session.consumer.d,'nf_d3d_full_async_capture'):
    import time,threading
    d=session.consumer.d;capture=d.nf_d3d_full_async_capture;capture.argtypes=[C.c_uint,C.c_uint64];capture.restype=C.c_int
    poll=d.nf_d3d_full_async_poll;poll.argtypes=[C.c_uint,C.c_uint64,C.c_void_p,C.c_size_t];poll.restype=C.c_int
    stats=d.nf_d3d_full_async_stats;stats.argtypes=[C.c_void_p,C.c_size_t];stats.restype=C.c_int
    slot=index%3;capture_id=index+1
    assert capture(3,capture_id)==1 and capture(slot,0)==1
    rejected=[];thread=threading.Thread(target=lambda:rejected.append(capture(slot,capture_id)));thread.start();thread.join(5);assert not thread.is_alive() and rejected==[1]
    assert capture(slot,capture_id)==0 and capture(slot,capture_id+100)==1
    async_rgba=C.create_string_buffer(len(rgba))
    assert poll(slot,capture_id+100,async_rgba,len(async_rgba))==1
    assert poll(slot,capture_id,None,len(async_rgba))==1 and poll(slot,capture_id,async_rgba,len(async_rgba)-1)==1
    deadline=time.monotonic()+5
    while True:
     rc=poll(slot,capture_id,async_rgba,len(async_rgba));assert rc in (0,3)
     if rc==0:break
     assert time.monotonic()<deadline;time.sleep(.001)
    assert async_rgba.raw==rgba.raw
    profile=(C.c_uint64*4)();getter=d.nf_d3d_full_async_poll_profile;getter.argtypes=[C.c_void_p,C.c_size_t];assert getter(profile,C.sizeof(profile))==0
    assert 0<profile[0]<=profile[1]<=profile[2]<=profile[3]
    assert getter(None,C.sizeof(profile))==1 and getter(profile,C.sizeof(profile)-1)==1
    assert poll(slot,capture_id,async_rgba,len(async_rgba))==1
    counts=(C.c_uint64*3)();assert stats(counts,C.sizeof(counts))==0 and counts[1]==0 and counts[0]<=3 and counts[2]==counts[0]*len(rgba)
    assert stats(None,C.sizeof(counts))==1 and stats(counts,C.sizeof(counts)-1)==1
   hashes.append(hashlib.sha256(rgba.raw).hexdigest())
  world_stats=(C.c_uint64*2)();assert session.consumer.d.nf_d3d_world_upload_stats(world_stats)==0
  assert world_stats[1]==0
  if library=='owned-d3d-world-stream-linear-transaction-candidate.dll':assert 0<world_stats[0]<len(hashes)
  reused=None
  if hasattr(session.consumer.d,'nf_d3d_resource_reuse_count'):
   session.consumer.d.nf_d3d_resource_reuse_count.restype=C.c_uint64;reused=session.consumer.d.nf_d3d_resource_reuse_count();assert reused>0
  measured=None
  if hasattr(session.consumer.d,'nf_d3d_measured_stages'):
   user=C.WinDLL('user32');user.PostMessageW.argtypes=[C.c_void_p,C.c_uint,C.c_size_t,C.c_ssize_t];user.PostMessageW.restype=C.c_int
   assert user.PostMessageW(session.consumer.window,0x8009,0,0)
   pump=session.consumer.d.nf_d3d_window_pump;pump.argtypes=[C.c_void_p,C.c_void_p];pump.restype=C.c_int
   window_stats=(C.c_uint64*7)();assert pump(session.consumer.window,window_stats)==0 and window_stats[0]>=1
   assert pump(None,window_stats)==1
   values=(C.c_uint64*12)();assert session.consumer.d.nf_d3d_measured_stages(values,C.sizeof(values))==0
   assert values[11]>0 and values[6]<=values[7] and values[8]<=values[9]
   assert values[5]>0 and values[0]<=values[1] and values[2]<=values[3] and values[4]>=1
   assert session.consumer.d.nf_d3d_measured_stages(None,C.sizeof(values))==37
   assert session.consumer.d.nf_d3d_measured_stages(values,C.sizeof(values)-1)==37
   measured=list(values)
  return dict(measured=measured,hashes=hashes,resource_reuses=reused,world_buffer_creates=world_stats[0],library=loads[0])
 finally:
  if session is not None:
   d=session.consumer.d
   if hasattr(d,'nf_d3d_full_async_capture'):
    for slot in range(3):assert d.nf_d3d_full_async_capture(slot,1000+slot)==0
    counts=(C.c_uint64*3)();assert d.nf_d3d_full_async_stats(counts,C.sizeof(counts))==0 and list(counts)==[3,3,3*3840*2160*4]
   session.close();assert session.source.nf_owned_gpu_contexts()==0
   if hasattr(d,'nf_d3d_full_async_stats'):assert d.nf_d3d_full_async_stats(counts,C.sizeof(counts))==0 and list(counts)==[0,0,0]

  C.CDLL=original_cdll
try:
 baseline=run('owned-d3d-sky-linear-transaction-candidate.dll')
 candidate=run('owned-d3d-full-async-return-candidate.dll')
 assert baseline['hashes']==candidate['hashes']
 out=dict(result='PASS_ACTUAL_SCENE_FULL_4K_ASYNC_PARITY_GUARDS',frames=len(candidate['hashes']),baseline=baseline,candidate=candidate,scope='Complete 4K RGBA saved fullscene pixels, five original/fractional phases repeated, actual source/HUD/sky/world draw order; Async entire-frame bytes equal synchronous entire-frame bytes at all phases; slot/id/size/null/owner/reuse guards and pending-close cleanup. Limited to one saved scene pair; not live async scheduling or sustained gameplay/cadence proof.')
 Path('work/camera/prototype-runs/full-async-return-4k-parity-20261010.json').write_text(json.dumps(out,indent=2));print(out['result']);print('frames',out['frames'],'resource_reuses',candidate['resource_reuses'])
finally:cached.close();prepared.close();history.close()
