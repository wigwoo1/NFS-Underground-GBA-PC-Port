import sys,json,ctypes as C,struct
from pathlib import Path
sys.argv=['test','work/camera/prototype-runs/owned-native-1791434872973979000.json']
exec(compile(Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text().split('session=None;results=[]')[0],'captured_setup','exec'))
d=C.CDLL(str(Path('work/camera/owned-handoff-copy-profile-candidate.dll').resolve()));P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t
for name,args,result in [('create_capacity',[U,C.c_uint],P),('push_stages',[P,P,Z,P],C.c_int),('pop_token',[P,P,P],P),('pause',[P,C.c_uint],C.c_int),('epoch',[P,U],C.c_int),('pool_stats',[P,P],C.c_int),('close',[P],None),('destroy',[P],None)]:
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
d.nf_owned_frame_free.argtypes=[P]
epoch=struct.unpack_from('<Q',frames[0],24)[0];q=d.nf_owned_handoff_create_capacity(epoch,2);assert q;held=None
samples=[]
try:
 for i in range(20):
  frame=frames[i%2];timing=(U*8)();assert d.nf_owned_handoff_push_stages(q,frame,len(frame),timing)
  size=Z();generation=U();p=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(generation));assert p and C.string_at(p,size.value)==frame
  profile=(U*3)();assert d.nf_owned_handoff_copy_profile(profile);assert profile[2]>0;samples.append(dict(allocation_ms=profile[0]*1000/profile[2],copy_ms=profile[1]*1000/profile[2]));d.nf_owned_frame_free(p)
 # A popped frame must survive pause and later reuse of other buffers.
 frame=frames[0];assert d.nf_owned_handoff_push_stages(q,frame,len(frame),(U*8)());size=Z();gen=U();held=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(gen));assert held
 assert d.nf_owned_handoff_push_stages(q,frames[1],len(frames[1]),(U*8)())
 assert d.nf_owned_handoff_pause(q,1);assert not d.nf_owned_handoff_push_stages(q,frame,len(frame),(U*8)())
 cleared=(U*3)();assert d.nf_owned_handoff_copy_profile(cleared);assert list(cleared)==[0,0,0];assert C.string_at(held,size.value)==frame
 assert d.nf_owned_handoff_pause(q,0);assert d.nf_owned_handoff_epoch(q,epoch+1);assert not d.nf_owned_handoff_push_stages(q,frame,len(frame),(U*8)())
 cleared=(U*3)();assert d.nf_owned_handoff_copy_profile(cleared);assert list(cleared)==[0,0,0];assert C.string_at(held,size.value)==frame
 d.nf_owned_frame_free(held);held=None
 stats=(U*4)();assert d.nf_owned_handoff_pool_stats(q,stats);assert stats[1]>=18 and stats[2]<=8 and stats[3]<=8*0x1000000
 result=list(stats)
 # Close may drain queued packets, but cannot invalidate a consumer-owned packet.
 assert d.nf_owned_handoff_epoch(q,epoch+2)
 packet=bytearray(frame);struct.pack_into('<Q',packet,24,epoch+2);frame=bytes(packet)
 queued=bytearray(frames[1]);struct.pack_into('<Q',queued,24,epoch+2);queued=bytes(queued)
 assert d.nf_owned_handoff_push_stages(q,frame,len(frame),(U*8)())
 held=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(gen));assert held
 assert d.nf_owned_handoff_push_stages(q,queued,len(queued),(U*8)())
 d.nf_owned_handoff_close(q)
 assert C.string_at(held,size.value)==frame
 assert not d.nf_owned_handoff_push_stages(q,frame,len(frame),(U*8)())
 cleared=(U*3)();assert d.nf_owned_handoff_copy_profile(cleared);assert list(cleared)==[0,0,0]
 d.nf_owned_frame_free(held);held=None
finally:
 if held:d.nf_owned_frame_free(held)
 d.nf_owned_handoff_destroy(q)
out=dict(copy_profiles=samples,result='PASS_ACTUAL_FRAME_NATIVE_POOL_LIFETIME',allocations=result[0],reuses=result[1],cached_buffers=result[2],cached_bytes=result[3],scope='Actual captured full-frame queue parity and popped lifetime across pause/epoch/drain/close; consumer releases before queue destruction; isolated component, no live performance or 4K/cadence proof.')
Path('work/camera/prototype-runs/handoff-copy-profile-component-20261009.json').write_text(json.dumps(out,indent=2));print(out)


