"""Fresh original replay: prepared camera view drives native visibility reconstruction."""
from pathlib import Path
import ctypes as C,csv,json
p=Path(__file__).resolve().parent
exec(compile((p/'test_live_owned_indexed_copy.py').read_text().split("\nassert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'test_live_owned_indexed_copy.py'),'exec'))
root=d.nf_live_completed_draw_root;root.argtypes=[C.c_uint64,U,U,P,P]
rebuild=d.nf_live_completed_draw_root_commands_view;rebuild.argtypes=[C.c_uint64,U,U,P,P,U,P]
road_view=d.nf_live_completed_draw_road_asset_view;road_view.argtypes=[C.c_uint64,U,U,U,P,U,U,P,P]
road_detail=d.nf_live_completed_draw_road_asset_view_detail;road_detail.argtypes=[P]
road_span_report=[]
focals_get=d.nf_live_completed_draw_sample_focals;focals_get.argtypes=[C.c_uint64,U,U,U,C.c_double,P]
rebuild_focal=d.nf_live_completed_draw_root_commands_focal;rebuild_focal.argtypes=[C.c_uint64,U,U,P,U,U,P,U,P]
sample=d.nf_visibility_view_sample;sample.argtypes=[P,P,C.c_double,P]
assert C.sizeof(Command)==3604
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
completion_owners=[];display_rows=[]
generation_copy=d.nf_page_write_audit_generation_copy;generation_copy.argtypes=[P]
d.nf_page_write_audit_enable(1);d.nf_page_write_audit_generation_reset()
display_generation=d.nf_layer_queue_page_generation;display_generation.argtypes=[C.c_uint64,U,U,P]
hud_read=d.nf_layer_queue_hud_row;hud_read.argtypes=[C.c_uint64,U,U,P,U]
text_read=d.nf_layer_queue_text_row;text_read.argtypes=[C.c_uint64,U,U,P,P,U]
base_sink=sink
@Sink
def motion_sink(ctx,e,data,size):
 raw=C.string_at(data,size);serial,begin,end,page=__import__('struct').unpack_from('<4I',raw,16);gen=(C.c_uint64*2)();assert generation_copy(gen)
 completion_owners.append(dict(epoch=e,serial=serial,completion_refresh=end,page=page,completion_generation=gen[page]))
 return base_sink(ctx,e,data,size)
report=[];tested=False;operation_ledger=[];owned_packets=[];packet_results=[];original_bundles=[]
transition=d.nf_live_completed_draw_scene_packet_transition;transition.argtypes=[C.c_uint64,U,U,C.c_double,P,P,P,U,P]
d.nf_live_completed_draw_sample_detail.argtypes=[P]
for flag in ['NF_TEST_FOCAL_SAMPLE','NF_TEST_INDEXED_ENTRANTS','NF_TEST_OWNED_ROOT_ENDPOINT']:assert crt._putenv_s(flag.encode(),b'1')==0
try:
 assert d.nf_native_scene_sink(motion_sink,None) and d.nf_native_scene_multimodel(1)
 assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_layer_queue_enable(1) and d.nf_bitmap_text_enable(1)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']))
  if latest.get('serial')!=19 or tested:continue
  tested=True;e=latest['epoch']
  import struct
  for refresh in range(3509,3515):
   hud=C.create_string_buffer(160*34944);text=C.create_string_buffer(76832);struct.pack_into('<8I',text,0,0x5854464e,1,e&0xffffffff,e>>32,refresh,240,160,38400)
   for y in range(160):assert hud_read(e,refresh,y,C.byref(hud,y*34944),34944) and text_read(e,refresh,y,C.byref(text,32+y*240),C.byref(text,38432+y*240),240)
   pages=[(struct.unpack_from('<H',hud.raw,y*34944+8)[0]>>4)&1 for y in range(160)]
   owners=[]
   for page in set(pages):
    candidates=[x for x in completion_owners if x['epoch']==e and x['page']==page and x['completion_refresh']<=refresh];assert candidates
    owner=max(candidates,key=lambda x:x['completion_refresh']);gen=C.c_uint64();ok=display_generation(e,refresh,page,C.byref(gen));owners.append(dict(**owner,display_refresh=refresh,display_generation=gen.value,generation_verified=bool(ok and gen.value==owner['completion_generation'])))
   transitions=[y for y in range(1,160) if pages[y]!=pages[y-1]]
   if transitions:
    assert len(transitions)==1 and len(owners)==2
    split=d.nf_layer_queue_split_generations;split.argtypes=[C.c_uint64,U,U,C.c_uint64,U,C.c_uint64,P]
    older,newer=sorted(owners,key=lambda x:x['completion_refresh']);cut=U()
    assert split(e,refresh,older['page'],older['completion_generation'],newer['page'],newer['completion_generation'],C.byref(cut)) and cut.value==transitions[0]
    for owner in owners:owner['generation_verified']=True;owner['proof_kind']='split_generation'
   else:assert all(x['generation_verified'] for x in owners),(refresh,owners)
   (p/f'motion-display-{refresh}.hud').write_bytes(hud.raw);(p/f'motion-display-{refresh}.text').write_bytes(text.raw)
   display_rows.append(dict(refresh=refresh,first_page=pages[0],transitions=transitions,owners=owners))
  for serial in [18,19]:
   events=(OrderedEvent*608)();amount=U();assert order_get(e,serial,events,608,C.byref(amount))
   operation_ledger.append(dict(serial=serial,events=[dict(cycles=v.cycles,type=v.type,pass_index=v.pass_index,ordinal=v.ordinal,kind=v.kind,source=v.source) for v in events[:amount.value]]))
  for serial in [18,19]:
   out=P();size=Z();assert road_bundle_get(e,serial,C.byref(out),C.byref(size))
   raw=C.string_at(out,size.value);assert road_bundle_validate(out,size.value)
   original_bundles.append(dict(serial=serial,bytes=size.value,sha256=hashlib.sha256(raw).hexdigest()))
   (p/f'motion-prepared-original-{serial}.nfrb').write_bytes(raw);d.nf_live_road_asset_free(out)
  for alpha in [0.,.25,.5,.75,1.]:
   out=P(123);size=Z(999);poses=C.create_string_buffer(b'T'*8064,8064);amount=U(888)
   ok=transition(e,18,19,alpha,C.byref(out),C.byref(size),poses,144,C.byref(amount))
   detail=(U*8)();d.nf_live_completed_draw_sample_detail(detail)
   if ok:
    raw=C.string_at(out,size.value)
    if alpha in [0.,1.]:
     exact=P();exact_size=Z();exact_poses=C.create_string_buffer(8064);exact_count=U()
     assert scene_get(e,19 if alpha==1 else 18,C.byref(exact),C.byref(exact_size),exact_poses,144,C.byref(exact_count))
     assert raw==C.string_at(exact,exact_size.value) and poses.raw[:amount.value*56]==exact_poses.raw[:exact_count.value*56]
     d.nf_scene_packet_free(exact)
    owned_packets.append((alpha,out,size.value,hashlib.sha256(raw).hexdigest()))
    (p/f'motion-prepared-{alpha:.2f}.packet').write_bytes(raw)
    (p/f'motion-prepared-{alpha:.2f}.cameras').write_bytes(poses.raw[:amount.value*56])
   else:assert out.value==123 and size.value==999 and amount.value==888 and poses.raw==b'T'*8064
   packet_results.append(dict(alpha=alpha,accepted=bool(ok),bytes=size.value if ok else 0,cameras=amount.value if ok else 0,failure_detail=list(detail) if not ok else None))
  for ordinal in range(16):
   views=[];original=[]
   for serial in [18,19]:
    v=(U*12)();state=C.create_string_buffer(65536)
    if not root(e,serial,ordinal,v,state):break
    commands=(Command*144)();n=U();assert commands_get(e,serial,ordinal,commands,144,C.byref(n))
    views.append(v);original.append(bytes(commands)[:n.value*3604])
   if len(views)!=2:break
   phases=[]
   for alpha in [0.,.25,.5,.75,1.]:
    v=(U*12)();assert sample(views[0],views[1],alpha,v)
    focals=(U*2)();assert focals_get(e,18,19,ordinal,alpha,focals)
    commands=(Command*144)();n=U();assert rebuild_focal(e,19 if alpha==1 else 18,ordinal,v,focals[0],focals[1],commands,144,C.byref(n))
    for index,command in enumerate(commands[:n.value]):
     if command.head[0]!=1:continue
     out=P(123);size=Z(999);serial=19 if alpha==1 else 18
     ok=road_view(e,serial,ordinal,index,v,focals[0],focals[1],C.byref(out),C.byref(size))
     detail=(U*4)();road_detail(detail)
     if not ok and not command.head[8]:assert list(detail)[0]==6 and list(detail)[3]==0, list(detail)
     assert not (ok and command.head[8]), (alpha,index,list(command.head))
     if ok:
      asset=C.string_at(out,size.value);assert d.nf_live_road_asset_validate(out,size.value)
      if alpha in [0.,1.]:
       original_asset=P();original_size=Z();assert road_asset(e,serial,ordinal,index,C.byref(original_asset),C.byref(original_size))
       assert asset==C.string_at(original_asset,original_size.value);d.nf_live_road_asset_free(original_asset)
      (p/f'motion-road-{alpha:.2f}-{ordinal}-{index}.nfre').write_bytes(asset)
      d.nf_live_road_asset_free(out)
     else:assert out.value==123 and size.value==999
     road_span_report.append(dict(alpha=alpha,pass_index=ordinal,command=index,source=command.head[5],detail=list(detail),secondary=bool(command.head[8]),focals=list(focals),accepted=bool(ok),bytes=size.value if ok else 0))
    raw=bytes(commands)[:n.value*3604]
    if alpha in [0.,1.]:assert raw==original[int(alpha)],(ordinal,alpha)
    phases.append(dict(alpha=alpha,commands=n.value,world=[dict(kind=c.head[0],source=c.head[5],identity=list(c.head[:13]),bounds=list(c.bounds)) for c in commands[:n.value] if c.head[0] in [1,2]]))
   old_keys={(x['kind'],x['source']) for x in phases[0]['world']};new_keys={(x['kind'],x['source']) for x in phases[-1]['world']}
   for phase in phases:
    keys=[(x['kind'],x['source']) for x in phase['world']];assert len(keys)==len(set(keys)), 'ambiguous source in pass'
    phase['older_only_absent']=[list(k) for k in sorted(old_keys-set(keys))]
    phase['newer_only_absent']=[list(k) for k in sorted(new_keys-set(keys))]
    phase['novel_sources']=[list(k) for k in sorted(set(keys)-old_keys-new_keys)]
   report.append(dict(pass_index=ordinal,phases=phases,endpoint_commands_exact=True))
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  f=p/('motion-visibility-check-'+name+'.bin');d.nf_dump(str(f).encode(),address,size);raw=f.read_bytes();f.unlink();assert raw==Path(str(prefix)+'-'+name+'.bin').read_bytes()
finally:d.nf_close()
for alpha,out,size,digest in owned_packets:
 assert hashlib.sha256(C.string_at(out,size)).hexdigest()==digest
 d.nf_scene_packet_free(out)
assert tested and report
# Establish ordering evidence for this pair before any transport replacement.
for ledger in operation_ledger:
 events=ledger['events'];first=next(i for i,x in enumerate(events) if x['type'] in [3,4])
 assert all(x['type'] in [1,2] for x in events[:first])
 assert all(x['type'] in [3,4] for x in events[first:]), 'interleaved operation needs separate handling'
 ledger['prefix_operation_count']=first
for entry in report:
 endpoints=[[ (x['kind'],x['source']) for x in phase['world']] for phase in [entry['phases'][0],entry['phases'][-1]]]
 shared=set(endpoints[0])&set(endpoints[1])
 expected=[k for k in endpoints[0] if k in shared]
 assert expected==[k for k in endpoints[1] if k in shared]
 for phase in entry['phases']:
  keys=[(x['kind'],x['source']) for x in phase['world']]
  assert [k for k in keys if k in shared]==expected, 'shared order changed'
  phase['shared_order_exact']=True
  phase['entrant_anchors']=[dict(source=list(k),previous=list(keys[i-1]) if i else None,next=list(keys[i+1]) if i+1<len(keys) else None) for i,k in enumerate(keys) if k not in set(endpoints[0])]
result=dict(result='PASS',pair=[18,19],passes=report,operation_ledger=operation_ledger,display_rows=display_rows,road_spans=road_span_report,packet_results=packet_results,original_bundles=original_bundles,owned_packets_after_bridge_close=True,full_original_ram_exact=True,scope='Prepared Q8 view reconstruction audit; focal interpolation and ordered effects not integrated')
(p/'motion-visibility-audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(dict(road_span_assets=sum(x['accepted'] for x in road_span_report),road_span_rejections=sum(not x['accepted'] for x in road_span_report),result='PASS',passes=len(report),packet_results=packet_results,phases=5,endpoint_commands_exact=True,full_original_ram_exact=True)))
