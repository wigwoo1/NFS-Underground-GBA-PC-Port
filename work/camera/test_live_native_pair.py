"""Completed live snapshot native packet API; preserves original simulation output."""
from pathlib import Path
import ctypes as C,struct,json,hashlib,sys,os,time,statistics
p=Path('work/camera').resolve();root=p.parent;rom_path=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
Callback=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p)
@Callback
def noop(ctx,index,selector,objects,count,bits,matrix,head,maximum):return 1
frames=int(sys.argv[1]) if len(sys.argv)>1 else 240
pair_mode=len(sys.argv)>2 and sys.argv[2]=='pair'
owned_mode=len(sys.argv)>2 and sys.argv[2] in ('owned','pair')
replay_mode=len(sys.argv)>2 and sys.argv[2] in ('replay','owned','pair')
results=[]
def run(library,diagnostic):
 timings=[];delayed=[];delayed_verified=0;sample_digest=hashlib.sha256()
 d=C.CDLL(str(library));packets=[];pending=[];failures={};success=0;atomic=0;blocked_callbacks=0;palette_missing=0;palette_differences=[];original_by_identity={};source_orders=[];asset_matches={1:0,2:0,4:0};producer_failures={};callback_mismatches={};visit_divergences={};journal_records=journal_changed_bytes=journal_failures=replayed_changed_bytes=0;native_calls=0;previous=None;pair_success=0;pair_failed={};pair_changes=0
 d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
 @Sink
 def sink(user,epoch,ptr,n):
  raw=C.string_at(ptr,n);h=struct.unpack_from('<8I',raw);packets.append(hashlib.sha256(raw).hexdigest());pending.append((epoch,*h[4:7]));original_by_identity[(epoch,*h[4:7])]=raw;return 1
 assert d.nf_init(str(rom_path).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
 try:
  assert d.nf_native_scene_sink(sink,None)
  if diagnostic:
   rom=rom_path.read_bytes();d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t];assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1)
   d.nf_live_completed_visibility_pose.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p]
   api=d.nf_live_completed_native_packet;api.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p,C.c_double,C.c_void_p,C.c_uint,Callback,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p];d.nf_scene_packet_free.argtypes=[C.c_void_p]
   replay_api=d.nf_live_completed_native_packet_owned if owned_mode else d.nf_live_completed_native_packet_replay;replay_api.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p]*3
   d.nf_live_completed_object_visits.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p]
   d.nf_live_completed_callback_journal.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p]
   d.nf_live_completed_snapshot_read.argtypes=[C.c_uint64]+[C.c_uint32]*4+[C.c_void_p,C.c_size_t];d.nf_live_completed_model_inputs.argtypes=[C.c_uint64]+[C.c_uint32]*3+[C.c_void_p]
   if pair_mode:
    class Identity(C.Structure):_fields_=[('epoch',C.c_uint64)]+[(k,C.c_uint32) for k in ('serial','begin','end','query','builder')]
    pair_api=d.nf_live_completed_native_pair_packet;pair_api.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p,C.c_void_p]
  for frame in range(frames):
   d.nf_frame(1 | (32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
   if not diagnostic:pending.clear();continue
   effects=(C.c_uint32*7)();stats=(C.c_uint32*6)();d.nf_live_object_callback_effects(effects);d.nf_live_object_collector_stats(stats)
   for identity in pending:
    pose=C.create_string_buffer(104)
    if not d.nf_live_completed_visibility_pose(*identity,pose):continue
    out=C.c_void_p(123);size=C.c_size_t(456);stage=C.c_uint()
    assert not api(identity[0]+1,*identity[1:],pose,0.,None,256,Callback(),None,C.byref(out),C.byref(size),C.byref(stage)) and (out.value,size.value)==(123,456);atomic+=1
    if owned_mode:assert not replay_api(identity[0]+1,*identity[1:],C.byref(out),C.byref(size),C.byref(stage)) and (out.value,size.value)==(123,456)
    if not replay_mode and (any(effects[1:]) or stats[4] or stats[5]):blocked_callbacks+=1;continue
    # Only after original live callback state effects and collector parity audit.
    if replay_mode:
     journal=(C.c_uint32*3)();assert d.nf_live_completed_callback_journal(*identity,journal);journal_records+=journal[0];journal_failures+=journal[1];journal_changed_bytes+=journal[2]
     ok=replay_api(*identity,C.byref(out),C.byref(size),C.byref(stage))
    else:ok=api(*identity,pose,0.,None,256,noop,None,C.byref(out),C.byref(size),C.byref(stage))
    if ok:
     if owned_mode:
      native_detail=(C.c_uint32*6)();d.nf_visibility_snapshot_packet_detail(native_detail);native_calls+=native_detail[5]
     if replay_mode:
      detail=(C.c_uint32*4)();d.nf_live_completed_callback_replay_detail(detail);replayed_changed_bytes+=detail[3]
     try:
      raw=C.string_at(out,size.value);assert struct.unpack_from('<4I',raw,16)[:3]==identity[1:]
      def source_order(packet):
       sections={t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+j*12) for j in range(5))};count=struct.unpack_from('<I',sections[3],4)[0];ids=[struct.unpack_from('<5I',sections[5],8+j*20) for j in range(count)];order=struct.unpack_from('<'+'I'*count,sections[3],8)
       return [(ids[-1] if j==0xffffffff else ids[j])[::2][:2] for j in order]
      source_orders.append(source_order(raw)==source_order(original_by_identity[identity]))
      def payload_sections(packet):return {t:packet[o:o+n] for t,o,n in (struct.unpack_from('<3I',packet,32+j*12) for j in range(5))}
      generated=payload_sections(raw);original=payload_sections(original_by_identity[identity])
      for tag in asset_matches:asset_matches[tag]+=generated[tag]==original[tag]
      (p/f'live-native-packet-{success}.bin').write_bytes(raw);success+=1
     finally:d.nf_scene_packet_free(out)
    else:
     assert (out.value,size.value)==(123,456);failures[str(stage.value)]=failures.get(str(stage.value),0)+1
     if stage.value==8:
      native_visits=(C.c_uint32*(1+2048*3))();original_visits=(C.c_uint32*(1+2048*3))();d.nf_scene_command_plan_visits(native_visits);assert d.nf_live_completed_object_visits(*identity,original_visits)
      nv=[tuple(native_visits[1+i*3:4+i*3]) for i in range(native_visits[0])];ov=[tuple(original_visits[1+i*3:4+i*3]) for i in range(original_visits[0])];first=next((i for i in range(min(len(nv),len(ov))) if nv[i]!=ov[i]),min(len(nv),len(ov)));key=str(dict(at=first,native=nv[max(0,first-1):first+3],original=ov[max(0,first-1):first+3]));visit_divergences[key]=visit_divergences.get(key,0)+1
      detail=(C.c_uint32*4)();d.nf_live_completed_callback_replay_detail(detail);bits=C.create_string_buffer(64);d.nf_live_completed_callback_replay_bits(bits);extra=[i for i in range(256) if bits.raw[i//8]&(1<<(i%8)) and not bits.raw[32+i//8]&(1<<(i%8))];missing=[i for i in range(256) if bits.raw[32+i//8]&(1<<(i%8)) and not bits.raw[i//8]&(1<<(i%8))];key=','.join(map(str,detail))+f' extra={extra} missing={missing}';callback_mismatches[key]=callback_mismatches.get(key,0)+1
     if stage.value==4:
      road=(C.c_uint32*(12+128*6))();d.nf_scene_command_plan_road(road)
      if road[0]:(p/f'live-road-failure-{identity[1]}-{road[0]}.bin').write_bytes(bytes(road))
      detail=(C.c_uint32*6)();d.nf_visibility_snapshot_packet_detail(detail);plan=(C.c_uint32*18)();d.nf_scene_command_plan_detail(plan);key=','.join(map(str,list(detail)+list(plan)));producer_failures[key]=producer_failures.get(key,0)+1
     if stage.value==3:
      retained=C.create_string_buffer(512);model_inputs=C.create_string_buffer(560)
      if not d.nf_live_completed_snapshot_read(*identity,0x05000000,retained,512):palette_missing+=1
      else:
       assert d.nf_live_completed_model_inputs(*identity,model_inputs)
       palette_differences.append(sum(retained.raw[i:i+2]!=model_inputs.raw[48+i:50+i] for i in range(0,512,2)))
    if pair_mode:
     if previous:
      aid=Identity(*previous,0,0);bid=Identity(*identity,0,0);samples=[]
      bad_identity=Identity(previous[0]+1,*previous[1:],0,0)
      for left,right,value in ((bad_identity,bid,.5),(bid,aid,.5),(aid,bid,float('nan'))):
       rejected=C.c_void_p(123);rejected_size=C.c_size_t(456);rejected_stage=C.c_uint()
       assert not pair_api(C.byref(left),C.byref(right),value,C.byref(rejected),C.byref(rejected_size),C.byref(rejected_stage)) and (rejected.value,rejected_size.value)==(123,456)
      for alpha in (0.,.25,.5,.75,1.):
       pair_out=C.c_void_p(123);pair_size=C.c_size_t(456);pair_stage=C.c_uint()
       started=time.perf_counter_ns()
       pair_ok=pair_api(C.byref(aid),C.byref(bid),alpha,C.byref(pair_out),C.byref(pair_size),C.byref(pair_stage))
       elapsed_ms=(time.perf_counter_ns()-started)/1e6
       if 0<alpha<1:timings.append(elapsed_ms)
       if pair_ok:
        try:sample=C.string_at(pair_out,pair_size.value)
        finally:d.nf_scene_packet_free(pair_out)
        sample_digest.update(hashlib.sha256(sample).digest())
        if bid.serial==int(os.environ.get('NF_PAIR_CAPTURE_SERIAL','-1')):(p/f'paired-scene-{bid.serial}-{alpha}.bin').write_bytes(sample)
        if alpha==.5:delayed.append((previous,identity,hashlib.sha256(sample).hexdigest()))
        sections={t:sample[o:o+n] for t,o,n in (struct.unpack_from('<3I',sample,32+j*12) for j in range(5))};samples.append(hashlib.sha256(sections[1]+sections[2]).hexdigest());pair_success+=1
        surface_count=struct.unpack_from('<I',sections[2],4)[0];bounds_offset=8+(surface_count+1)*20
        assert struct.unpack_from('<d',sections[5],bounds_offset+8)[0]==(alpha if alpha<1 else 0)
        if alpha in (0.,1.):
         chosen=previous if alpha==0 else identity;endpoint=C.c_void_p();endpoint_size=C.c_size_t();assert replay_api(*chosen,C.byref(endpoint),C.byref(endpoint_size),C.byref(stage))
         try:assert sample==C.string_at(endpoint,endpoint_size.value)
         finally:d.nf_scene_packet_free(endpoint)
       else:
        assert (pair_out.value,pair_size.value)==(123,456);detail=(C.c_uint32*6)() if pair_stage.value==5 else (C.c_uint32*4)();d.nf_live_command_palette_missing(detail) if pair_stage.value==5 else d.nf_object_pool_sample_detail(detail);palette_reason=(C.c_uint32*4)();d.nf_scene_command_palette_detail(palette_reason);key=str(pair_stage.value)+':'+str(list(detail))+(' reason='+str(list(palette_reason)) if pair_stage.value==5 else '');pair_failed[key]=pair_failed.get(key,0)+1
      pair_changes+=len(set(samples))>2
      if len(delayed)>4:
       old_a,old_b,expected=delayed.pop(0);left=Identity(*old_a,0,0);right=Identity(*old_b,0,0);held=C.c_void_p();held_size=C.c_size_t();held_stage=C.c_uint()
       assert pair_api(C.byref(left),C.byref(right),.5,C.byref(held),C.byref(held_size),C.byref(held_stage)),('delayed pair',old_b,held_stage.value)
       try:assert hashlib.sha256(C.string_at(held,held_size.value)).hexdigest()==expected
       finally:d.nf_scene_packet_free(held)
       delayed_verified+=1
     previous=identity
   pending.clear()
  memory=[]
  for base,n in ((0x02000000,0x40000),(0x03000000,0x8000)):
   path=p/f'live-native-test-{int(diagnostic)}-{base:x}.bin';d.nf_dump(str(path).encode(),base,n);memory.append(hashlib.sha256(path.read_bytes()).hexdigest())
  if diagnostic:
   assert (replay_mode or frames!=240 or (success==len(packets) and not failures)) and all(source_orders) and all(n==success for n in asset_matches.values()),'successful live native packet fidelity'
   palette_stats=(C.c_uint32*4)();palette_detail=(C.c_uint32*6)();d.nf_live_visibility_palette_stats(palette_stats);d.nf_live_visibility_palette_detail(palette_detail)
   functions=(C.c_uint32*80)();function_count=d.nf_live_callback_functions(functions);assert function_count<=16;function_rows=[list(functions[i*5:i*5+5]) for i in range(function_count)]
   root_coherence=(C.c_uint32*5)();d.nf_live_snapshot_root_coherence(root_coherence)
   coherence=(C.c_uint32*5)();d.nf_live_snapshot_object_coherence(coherence)
   results.append(dict(pair_sample_success=pair_success,pair_sample_failures=pair_failed,pairs_with_changed_samples=pair_changes,native_callback_semantics=owned_mode,native_callback_calls=native_calls,callback_functions=function_rows,root_object_coherence=list(root_coherence),visit_divergences=visit_divergences,snapshot_object_coherence=list(coherence),palette_capture_stats=list(palette_stats),palette_capture_detail=list(palette_detail),live_native_packets=success,original_draw_source_order_matches=sum(source_orders),original_asset_section_matches=asset_matches,rejections_by_stage=failures,producer_failure_details=producer_failures,callback_replay_mismatches=callback_mismatches,identity_atomic_rejections=atomic,callback_audit_blocked=blocked_callbacks,callback_journal_records=journal_records,callback_journal_changed_bytes=journal_changed_bytes,successful_replayed_changed_bytes=replayed_changed_bytes,callback_journal_failures=journal_failures,missing_snapshot_palettes=palette_missing,palette_differing_indices_range=[min(palette_differences),max(palette_differences)] if palette_differences else None,original_callback_effects=list(effects),collector_stats=list(stats)))
  if diagnostic and timings:
   results[-1]['delayed_pair_exact_after_four_newer_scenes']=delayed_verified
   results[-1]['all_sample_packet_digest']=sample_digest.hexdigest()
   ordered=sorted(timings)
   results[-1]['intermediate_generation_ms']=dict(samples=len(timings),median=statistics.median(timings),p95=ordered[min(len(ordered)-1,int(.95*len(ordered)))],maximum=max(timings),over_60hz_budget=sum(t>1000/60 for t in timings),scope='Native paired API only; excludes simulation, GPU rendering, upload and presentation.')
  return packets,memory
 finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(p/'visibility-probe-wide.dll',True);assert baseline==captured
report=dict(result='INCOMPLETE' if pair_mode and results[0]['pair_sample_failures'] else 'PASS',paired_intermediate_requested=3*(len(baseline[0])-1) if pair_mode else 0,paired_intermediate_generated=results[0]['pair_sample_success']-2*(len(baseline[0])-1) if pair_mode else 0,native_generation_coverage='COMPLETE' if results[0]['live_native_packets']==len(baseline[0]) else 'INCOMPLETE',frames=frames,original_scene_packets=len(baseline[0]),original_packets_and_final_ram_identical=True,cases=results,scope='Paired native scene generation from immutable live endpoints; sampled camera/object/rotation, native callbacks and owned palettes. Endpoint scene assets exact; intermediate generation and changed payloads verified, independent original intermediate raster oracle still pending. Original simulation preserved. Unpaced diagnostic, no gameplay60fps claim.')
(p/(f'live-native-packet-pair-{frames}-tests.json' if pair_mode else f'live-native-packet-owned-{frames}-tests.json' if owned_mode else f'live-native-packet-replay-{frames}-tests.json' if replay_mode else 'live-native-packet-tests.json' if frames==240 else f'live-native-packet-{frames}-tests.json')).write_text(json.dumps(report,indent=2));print(report)





