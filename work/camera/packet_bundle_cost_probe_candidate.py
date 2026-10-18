"""Alternating transfers of the same live published captured packet."""
import ctypes as C,time,statistics
from owned_uncovered_window_candidate import OwnedD3DConsumer
original=OwnedD3DConsumer.render;results=[]
def render(self,s,readback=True):
 if not results:
  v=(C.c_uint*3)();t=(C.c_uint*2)();assert s.nf_source_packets_stats(v)==0 and s.nf_source_texture_stats(t)==0
  nv,nd,overflow=v;nt,nb=t;assert not overflow
  sizes=[nv*80,(nd+1)*4,nb,nt*16,nd*4,nd*72,20];arrays=[C.create_string_buffer(max(1,n)) for n in sizes]
  args=tuple(x for pair in zip(arrays,sizes) for x in pair)
  def bundled():assert s.nf_source_packet_bundle_copy(*args)==0
  def baseline():
   assert s.nf_source_packets_stats(v)==0 and s.nf_source_texture_stats(t)==0
   assert s.nf_source_packets_copy(arrays[0],sizes[0],arrays[1],sizes[1])==0
   assert s.nf_source_texture_copy(arrays[2],sizes[2],arrays[3],sizes[3],arrays[4],sizes[4])==0
   assert s.nf_source_state_copy(arrays[5],sizes[5])==0
  trials=[]
  for repetition in range(8):
   for name,fn in ([('baseline',baseline),('bundle',bundled)] if repetition%2==0 else [('bundle',bundled),('baseline',baseline)]):
    for _ in range(20):fn()
    begin=time.perf_counter_ns()
    for _ in range(500):fn()
    trials.append(dict(mode=name,ns_per_transfer=(time.perf_counter_ns()-begin)/500))
  medians={mode:statistics.median(x['ns_per_transfer'] for x in trials if x['mode']==mode) for mode in ('baseline','bundle')}
  baseline();before=[a.raw for a in arrays[:6]];bundled();assert [a.raw for a in arrays[:6]]==before
  results.append(dict(median_ns=medians,trials=trials,payload_bytes=sum(sizes[:6]),counts=[nv,nd,nt,nb],exact_same_packet_bytes=True,scope='Matched warm transfer-only cost on one actual published packet. Excludes source generation, numpy conversion, D3D/material upload, queue waits and visible cadence; not fullrenderer or live speed proof.'))
 return original(self,s,readback)
OwnedD3DConsumer.render=render
