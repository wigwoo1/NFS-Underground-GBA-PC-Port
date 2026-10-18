"""Component probe inside the real renderer's published packet lifetime."""
import ctypes as C,threading
from owned_uncovered_window_candidate import OwnedD3DConsumer
original=OwnedD3DConsumer.render;verified=[]
def render(self,s,readback=True):
 if not verified:
  v=(C.c_uint*3)();t=(C.c_uint*2)();assert s.nf_source_packets_stats(v)==0 and s.nf_source_texture_stats(t)==0
  nv,nd,overflow=v;nt,nb=t;assert not overflow
  sizes=[nv*80,(nd+1)*4,nb,nt*16,nd*4,nd*72,20];arrays=[C.create_string_buffer(max(1,n)) for n in sizes]
  def call(capacities,pointers=None):
   args=[]
   for array,n in zip(pointers or arrays,capacities):args.extend((array,n))
   return s.nf_source_packet_bundle_copy(*args)
  assert call(sizes)==0
  meta=(C.c_uint*5).from_buffer(arrays[-1]);assert list(meta)==[nv,nd,overflow,nt,nb]
  references=[C.create_string_buffer(max(1,n)) for n in sizes]
  assert s.nf_source_packets_copy(references[0],sizes[0],references[1],sizes[1])==0
  assert s.nf_source_texture_copy(references[2],sizes[2],references[3],sizes[3],references[4],sizes[4])==0
  assert s.nf_source_state_copy(references[5],sizes[5])==0
  assert all(a.raw[:n]==b.raw[:n] for a,b,n in zip(arrays[:6],references[:6],sizes[:6]))
  for a in arrays:C.memset(a,0xa5,C.sizeof(a))
  before=[a.raw for a in arrays]
  for i,n in enumerate(sizes):
   assert n>0
   caps=list(sizes);caps[i]=n-1;assert call(caps)==1;assert [a.raw for a in arrays]==before
   pointers=list(arrays);pointers[i]=None;assert call(sizes,pointers)==1;assert [a.raw for a in arrays]==before
  errors=[]
  def wrong_thread():
   try:assert call(sizes)==1 and [a.raw for a in arrays]==before
   except BaseException as error:errors.append(repr(error))
  thread=threading.Thread(target=wrong_thread);thread.start();thread.join(5);assert not thread.is_alive() and not errors
  verified.append(dict(capacity_rejections=7,null_rejections=7,wrong_thread_rejected=True,all_original_packet_bytes_exact=True,no_partial_writes=True))
 return original(self,s,readback)
OwnedD3DConsumer.render=render
