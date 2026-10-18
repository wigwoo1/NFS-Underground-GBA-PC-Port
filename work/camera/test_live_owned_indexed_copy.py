"""Fresh original replay retains ordered image copies, with lifetime guards."""
from pathlib import Path
from project_paths import load_session
import ctypes as C,csv,json,hashlib
p=Path(__file__).resolve().parent
exec(compile((p/'diagnose_late_model_pairs.py').read_text().split("assert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'diagnose_late_model_pairs.py'),'exec'))
prefix=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6'
session=load_session(Path(str(prefix)+'-session.json'));rom=Path(session['rom']).read_bytes()
assert crt._putenv_s(b'NF_CAPTURE_RETAINED_STRIP',b'1')==0
assert crt._putenv_s(b'NF_CAPTURE_INDEXED_COPY',b'1')==0
assert crt._putenv_s(b'NF_CAPTURE_WALL_OUTPUT_INDICES',b'1')==0
get=d.nf_live_completed_indexed_copy;get.argtypes=[C.c_uint64,U,U,P,P,P,P]
d.nf_indexed_copy_free.argtypes=[P];copies=[];seen=set()
operation=d.nf_live_completed_indexed_operation;operation.argtypes=[C.c_uint64,U,U,P,P,P,P];operations=[];pass_cycles=[];world_events=[]
world_cycles=d.nf_live_completed_world_cycles;world_cycles.argtypes=[C.c_uint64,U,U,P,U,P]
class WorldPalette(C.Structure):
 _fields_=[("kind",U),("source",U),("palette",C.c_uint8*512),("refresh",U),("vcount",U)]
palette_timeline=d.nf_live_completed_draw_palette_timeline;palette_timeline.argtypes=[C.c_uint64,U,U,P,P,U,P]
draw_cycles=d.nf_live_completed_draw_cycles;draw_cycles.argtypes=[C.c_uint64,U,U,P]
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
commands_get=d.nf_live_completed_draw_root_commands;commands_get.argtypes=[C.c_uint64,U,U,P,U,P]
class OrderedEvent(C.Structure):
 _fields_=[('cycles',C.c_uint64)]+[(k,U) for k in ['type','pass_index','ordinal','kind','source','page']]
order_get=d.nf_live_completed_operation_order;order_get.argtypes=[C.c_uint64,U,P,U,P];merged_events=[]
bundle_validate=d.nf_live_ordered_bundle_validate;bundle_validate.argtypes=[P,Z];malformed_cases=0
road_bundle_get=d.nf_live_completed_road_bundle;road_bundle_get.argtypes=[C.c_uint64,U,P,P];road_bundles=[]
road_bundle_validate=d.nf_live_road_bundle_validate;road_bundle_validate.argtypes=[P,Z];road_bundle_rejections=0;strip_mutation_checks=0
bundle_get=d.nf_live_completed_ordered_bundle;bundle_get.argtypes=[C.c_uint64,U,P,P];bundles=[]
d.nf_live_ordered_bundle_free.argtypes=[P]
scene_get=d.nf_live_completed_draw_scene_packet;scene_get.argtypes=[C.c_uint64,U,P,P,P,U,P]
road_contexts=d.nf_live_completed_draw_road_contexts;road_contexts.argtypes=[C.c_uint64,U,U,U,P,U,P]
road_spans=d.nf_live_completed_draw_road_spans;road_spans.argtypes=[C.c_uint64,U,U,U,P,U,P];edge_span_owners=[]
road_asset=d.nf_live_completed_draw_road_asset;road_asset.argtypes=[C.c_uint64,U,U,U,P,P];road_assets=[]
d.nf_live_road_asset_free.argtypes=[P]
road_sample=d.nf_live_road_asset_span_pixels;road_sample.argtypes=[P,Z,U,P,P,U]
road_validate=d.nf_live_road_asset_validate;road_validate.argtypes=[P,Z]
d.nf_layer_queue_text_row.argtypes=[C.c_uint64,U,U,P,P,U]
d.nf_layer_queue_hud_row.argtypes=[C.c_uint64,U,U,P,U]
d.nf_dump.argtypes=[C.c_char_p,U,U]
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
 assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_bitmap_text_enable(1);assert d.nf_layer_queue_enable(1)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']));e,s=latest.get('epoch'),latest.get('serial')
  if not e or s in seen:continue
  seen.add(s)
  if s not in [22,38]:continue
  amount=None;ordinal=0
  while amount is None or ordinal<amount:
   out=P();size=Z();meta=(U*4)();cycles=C.c_uint64()
   assert operation(e,s,ordinal,C.byref(out),C.byref(size),meta,C.byref(cycles))
   try:data=C.string_at(out,size.value)
   finally:d.nf_indexed_copy_free(out)
   h=struct.unpack_from('<10I',data);amount=meta[2]
   assert len(data)==40+h[9] and meta[3] in [1,2]
   if meta[3]==2:assert data[40:]==struct.pack('<I',h[2])*(h[9]//4)
   else:assert data[40:]==rom[h[2]-0x08000000:h[2]-0x08000000+h[9]]
   (p/f'live-indexed-operation-{s}-{ordinal}.bin').write_bytes(data)
   operations.append(dict(serial=s,ordinal=ordinal,refresh=meta[0],cycles=cycles.value,kind=meta[3],offset=h[4],bytes=h[9]))
   ordinal+=1
  palette_refresh=d.nf_layer_queue_latest();hud_size=d.nf_layer_hud_row_size();hud_row=(C.c_uint8*hud_size)();palette_rows=[];hud_rows=[];text_rows=[];coverage_rows=[]
  for y in range(160):
   assert d.nf_layer_queue_hud_row(e,palette_refresh,y,hud_row,hud_size)
   assert struct.unpack_from('<2I',bytes(hud_row))==(palette_refresh,y)
   text_row=(C.c_uint8*240)();coverage_row=(C.c_uint8*240)()
   if d.nf_layer_queue_text_row(e,palette_refresh,y,text_row,coverage_row,240):text_rows.append(bytes(text_row));coverage_rows.append(bytes(coverage_row))
   hud_rows.append(bytes(hud_row));palette_rows.append(bytes(hud_row)[32896:33408])
  text_meta=dict(epoch=e,serial=s,refresh=palette_refresh,rows_available=len(text_rows),complete=len(text_rows)==160)
  if len(text_rows)==160:
   text_raw=struct.pack('<8I',0x5854464e,1,e&0xffffffff,e>>32,palette_refresh,240,160,38400)+b''.join(text_rows)+b''.join(coverage_rows)
   (p/f'road-bundle-{s}-owned-text.bin').write_bytes(text_raw);text_meta.update(covered_pixels=sum(x!=0 for row in coverage_rows for x in row),sha256=hashlib.sha256(text_raw).hexdigest())
  (p/f'road-bundle-{s}-owned-text.json').write_text(json.dumps(text_meta,indent=2))
  (p/f'road-bundle-{s}-owned-hud.bin').write_bytes(b''.join(hud_rows))
  palette_raw=b''.join(palette_rows);assert len(palette_raw)==81920
  (p/f'road-bundle-{s}-display-palette.bin').write_bytes(palette_raw)
  (p/f'road-bundle-{s}-display-palette.json').write_text(json.dumps(dict(epoch=e,serial=s,refresh=palette_refresh,sha256=hashlib.sha256(palette_raw).hexdigest(),scope='Latest owned original scanline palette at publication observation; partial display switch synchronization not proven'),indent=2))
  road_out=P();road_size=Z();assert road_bundle_get(e,s,C.byref(road_out),C.byref(road_size))
  road_raw=C.string_at(road_out,road_size.value);rh=struct.unpack_from('<8I',road_raw)
  assert road_bundle_validate(road_raw,len(road_raw))
  assert rh[:3]==(0x4252464e,2,s) and rh[7]==len(road_raw)
  assert bundle_validate(road_raw[rh[5]:rh[5]+rh[6]],rh[6])
  for word,value in [(0,0),(1,3),(2,s+1),(3,145),(4,36),(5,rh[5]+4),(6,rh[6]-1),(7,rh[7]+1),(8,4),(9,143),(10,0),(11,1)]:
   corrupt=bytearray(road_raw);struct.pack_into('<I',corrupt,word*4,value);assert not road_bundle_validate(bytes(corrupt),len(corrupt));road_bundle_rejections+=1
  assert not road_bundle_validate(road_raw,len(road_raw)-1);road_bundle_rejections+=1
  if rh[3]>1:
   corrupt=bytearray(road_raw);corrupt[48:56]=corrupt[32:40];assert not road_bundle_validate(bytes(corrupt),len(corrupt));road_bundle_rejections+=1
  baseline_offset=32+rh[3]*16
  for word,value in [(0,0),(2,1),(3,1),(4,3844),(9,1888)]:
   corrupt=bytearray(road_raw);struct.pack_into('<I',corrupt,baseline_offset+word*4,value);assert not road_bundle_validate(bytes(corrupt),len(corrupt));road_bundle_rejections+=1
  corrupt=bytearray(road_raw);corrupt[baseline_offset+40]=1;assert not road_bundle_validate(bytes(corrupt),len(corrupt));road_bundle_rejections+=1
  # Reversible private fixture perturbation outside the original frame calls.
  d.nf_write.argtypes=[U,U,C.c_int];d.nf_write(0x06000000+3840,0x0101,2)
  changed=P();changed_size=Z();assert road_bundle_get(e,s,C.byref(changed),C.byref(changed_size))
  changed_raw=C.string_at(changed,changed_size.value);assert struct.unpack_from('<I',changed_raw,4)[0]==1 and road_bundle_validate(changed_raw,len(changed_raw))
  d.nf_live_ordered_bundle_free(changed);d.nf_write(0x06000000+3840,0,2)
  assert C.string_at(road_out,len(road_raw))==road_raw;strip_mutation_checks+=1
  for ri in range(rh[3]):
   rp,rc,ro,rs=struct.unpack_from('<4I',road_raw,32+ri*16)
   assert road_validate(road_raw[ro:ro+rs],rs) and struct.unpack_from('<2I',road_raw,ro+12)==(rp,rc)
  (p/f'road-bundle-{s}.bin').write_bytes(road_raw)
  road_bundles.append((road_out,road_raw,rh[3]))
  for pass_index in range(2):
   ticks=(C.c_uint64*2)();assert draw_cycles(e,s,pass_index,ticks)
   assert ticks[0]<ticks[1]
   world=(C.c_uint64*128)();n=U();assert world_cycles(e,s,pass_index,world,128,C.byref(n))
   root_palette=(C.c_uint8*512)();records=(WorldPalette*128)();palette_count=U()
   assert palette_timeline(e,s,pass_index,root_palette,records,128,C.byref(palette_count)) and n.value==palette_count.value
   commands=(Command*144)();command_count=U();assert commands_get(e,s,pass_index,commands,144,C.byref(command_count))
   world_commands=[commands[i] for i in range(command_count.value) if commands[i].head[0] in [1,2]]
   assert len(world_commands)==n.value
   assert [(x.head[0],x.head[5]) for x in world_commands]==[(records[i].kind,records[i].source) for i in range(n.value)]
   assert [commands[i].head[0] for i in range(command_count.value)].count(5)==1 and commands[command_count.value-1].head[0]==5
   for command_index in range(command_count.value):
    cmd=commands[command_index]
    if cmd.head[0]!=1:continue
    spans=(U*(512*4))();span_count=U();assert road_spans(e,s,pass_index,command_index,spans,512,C.byref(span_count))
    contexts=None
    if not cmd.head[8]:
     contexts=(U*(512*20))();context_count=U();assert road_contexts(e,s,pass_index,command_index,contexts,512,C.byref(context_count)) and context_count.value==span_count.value
     assert all(list(contexts[j*20:j*20+4])==list(spans[j*4:j*4+4]) for j in range(span_count.value))
     if context_count.value:
      asset=P();length=Z();assert road_asset(e,s,pass_index,command_index,C.byref(asset),C.byref(length))
      raw=C.string_at(asset,length.value);h=struct.unpack_from('<10I',raw)
      assert h[:6]==(0x4552464e,1,s,pass_index,command_index,context_count.value)
      assert raw[40:h[9]]==bytes(contexts)[:context_count.value*80]
      assert raw[h[9]:]==rom[h[7]-0x08000000:h[7]-0x08000000+h[8]] and len(raw)==h[9]+h[8]
      assert road_validate(raw,len(raw))
      assert h[8]==2*((contexts[5]>>16)+((contexts[6]>>16)<<contexts[4])+1)
      for word,value in [(0,0),(1,2),(3,4),(5,513),(6,16),(8,h[8]-2),(9,h[9]+4),(14,16),(19,0)]:
       corrupt=bytearray(raw);struct.pack_into('<I',corrupt,word*4,value);assert not road_validate(bytes(corrupt),len(corrupt))
      assert not road_validate(raw,len(raw)-1)
      road_assets.append((asset,raw))
     atomic=(U*(512*20))(*([99]*(512*20)));bad_count=U(77)
     if context_count.value:assert not road_contexts(e,s,pass_index,command_index,atomic,context_count.value-1,C.byref(bad_count)) and bad_count.value==77 and all(x==99 for x in atomic)
    for j in range(span_count.value):
     destination,width,writer,doubled=spans[j*4:j*4+4]
     offset=destination-0x06000000
     for row_offset in range(1+doubled):
      if offset+row_offset*240<=143*240+238<offset+row_offset*240+width*2:
       edge_span_owners.append(dict(serial=s,pass_index=pass_index,command=command_index,source=hex(cmd.head[5]),span=j,destination=hex(destination),halfwords=width,writer=hex(writer),doubled=doubled,bounds=list(cmd.bounds),context=list(contexts[j*20+4:j*20+20]) if contexts is not None else None))
   assert n.value>0 and all(ticks[0]<world[i]<ticks[1] for i in range(n.value))
   assert all(world[i]<world[i+1] for i in range(n.value-1))
   for i in range(n.value):world_events.append(dict(serial=s,pass_index=pass_index,ordinal=i,cycles=world[i],kind=records[i].kind,source=hex(records[i].source),refresh=records[i].refresh))
   untouched=(C.c_uint64*128)(*([99]*128));bad_count=U(77)
   assert not world_cycles(e,s,pass_index,untouched,n.value-1,C.byref(bad_count)) and bad_count.value==77 and list(untouched)==[99]*128
   pass_cycles.append(dict(serial=s,pass_index=pass_index,root=ticks[0],model=ticks[1]))
  merged=(OrderedEvent*608)();merged_count=U();assert order_get(e,s,merged,608,C.byref(merged_count))
  expected=[(x['cycles'],x['kind']) for x in operations if x['serial']==s]+[(x['cycles'],3) for x in world_events if x['serial']==s]+[(x['model'],4) for x in pass_cycles if x['serial']==s]
  assert [(merged[i].cycles,merged[i].type) for i in range(merged_count.value)]==sorted(expected)
  assert all(merged[i].page==0 for i in range(merged_count.value))
  for i in range(merged_count.value):merged_events.append(dict(serial=s,cycles=merged[i].cycles,type=merged[i].type,pass_index=merged[i].pass_index,ordinal=merged[i].ordinal,source=hex(merged[i].source)))
  atomic=(OrderedEvent*608)();C.memset(atomic,0x5a,C.sizeof(atomic));before=bytes(atomic);bad_count=U(77)
  assert not order_get(e,s,atomic,merged_count.value-1,C.byref(bad_count)) and bytes(atomic)==before and bad_count.value==77
  assert not order_get(e+1,s,atomic,608,C.byref(bad_count)) and bytes(atomic)==before and bad_count.value==77
  bundle=P();bundle_size=Z();assert bundle_get(e,s,C.byref(bundle),C.byref(bundle_size))
  raw_bundle=C.string_at(bundle,bundle_size.value);
  (p/f'ordered-bundle-{s}.bin').write_bytes(raw_bundle)
  h=struct.unpack_from('<16I',raw_bundle)
  assert bundle_validate(raw_bundle,len(raw_bundle))
  mutations=[]
  for word,value in [(0,0),(1,2),(5,2),(6,609),(7,33),(8,145),(9,65),(10,h[10]+8),(11,h[11]+8),(12,h[12]+8),(13,h[13]-1)]:
   bad=bytearray(raw_bundle);struct.pack_into('<I',bad,word*4,value);mutations.append(bytes(bad))
  for offset,value in [(h[9],0),(h[9]+8,99),(h[9]+20,99),(h[10],h[12]),(h[10]+4,1),(h[12]+16,s+1)]:
   bad=bytearray(raw_bundle);struct.pack_into('<I',bad,offset,value);mutations.append(bytes(bad))
  bad=bytearray(raw_bundle);struct.pack_into('<d',bad,h[11],float('nan'));mutations.append(bytes(bad))
  for bad in mutations:assert not bundle_validate(bad,len(bad));malformed_cases+=1
  assert not bundle_validate(raw_bundle,len(raw_bundle)-1);malformed_cases+=1
  assert h[:3]==(0x424f464e,1,s) and h[5]==0 and h[6]==merged_count.value and h[7]==7 and (h[14]|h[15]<<32)==e
  assert raw_bundle[h[9]:h[9]+h[6]*32]==bytes(merged)[:h[6]*32]
  packet=P();packet_size=Z();cameras=(C.c_uint8*(144*56))();camera_count=U()
  assert scene_get(e,s,C.byref(packet),C.byref(packet_size),cameras,144,C.byref(camera_count))
  assert raw_bundle[h[12]:h[12]+h[13]]==C.string_at(packet,packet_size.value)
  d.nf_indexed_copy_free(packet)
  assert h[8]==camera_count.value and raw_bundle[h[11]:h[11]+h[8]*56]==bytes(cameras)[:h[8]*56]
  for i in range(h[7]):
   offset,length=struct.unpack_from('<2I',raw_bundle,h[10]+i*8)
   assert raw_bundle[offset:offset+length]==(p/f'live-indexed-operation-{s}-{i}.bin').read_bytes()
  bundles.append(dict(serial=s,pointer=bundle,raw=raw_bundle,size=bundle_size.value,sha256=hashlib.sha256(raw_bundle).hexdigest()))
  bad=P(123);bad_size=Z(456);assert not bundle_get(e+1,s,C.byref(bad),C.byref(bad_size)) and (bad.value,bad_size.value)==(123,456)
  sequence=[x for x in operations if x['serial']==s]
  passes=[x for x in pass_cycles if x['serial']==s]
  image_copies=[x for x in sequence if x['kind']==1]
  assert image_copies[0]['cycles']<passes[0]['root']<passes[0]['model']<image_copies[1]['cycles']<passes[1]['root']<passes[1]['model']
  sentinel=(C.c_uint64*2)(123,456)
  assert not draw_cycles(e+1,s,0,sentinel) and list(sentinel)==[123,456]
  for ordinal in range(2):
   out=P();size=Z();meta=(U*3)();cycles=C.c_uint64()
   assert get(e,s,ordinal,C.byref(out),C.byref(size),meta,C.byref(cycles)),(s,ordinal)
   raw=C.string_at(out,size.value);header=struct.unpack_from('<10I',raw)
   (p/f'live-indexed-copy-{s}-{ordinal}.bin').write_bytes(raw)
   assert header[9]==15136 and raw[40:]==rom[header[2]-0x08000000:header[2]-0x08000000+15136]
   assert meta[2]==2
   copies.append(dict(serial=s,ordinal=ordinal,refresh=meta[0],caller=hex(meta[1]),cycles=cycles.value,source=hex(header[2]),asset_sha256=hashlib.sha256(raw).hexdigest(),pointer=out,raw=raw))
  bad=P(123);length=Z(456);meta=(U*3)(7,8,9);ticks=C.c_uint64(99)
  assert not get(e+1,s,0,C.byref(bad),C.byref(length),meta,C.byref(ticks))
  assert (bad.value,length.value,list(meta),ticks.value)==(123,456,[7,8,9],99)
 for name,address,amount in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/('live-copy-check-'+name+'.bin');d.nf_dump(str(path).encode(),address,amount)
  data=path.read_bytes();assert len(data)==amount and data==Path(str(prefix)+'-'+name+'.bin').read_bytes();path.unlink()
finally:d.nf_close()
for asset,raw,count in road_bundles:assert C.string_at(asset,len(raw))==raw;d.nf_live_ordered_bundle_free(asset)
reciprocal=(U*32768).from_buffer_copy((p/'road-correction-reciprocal.bin').read_bytes())
edge_reference={(x['serial'],x['pass']):[x['x237'],x['x238'],x['x239']] for x in json.loads((p/'owned-road-edge-samples.json').read_text())['checks']}
owned_edge_checks=0
owned_sampled_spans=0;owned_sampled_writers=set()
for asset,raw in road_assets:
 h=struct.unpack_from('<10I',raw)
 for span_index in range(h[5]):
  span=struct.unpack_from('<20I',raw,40+span_index*80)
  pixels=(C.c_uint16*512)();assert road_sample(asset,len(raw),span_index,reciprocal,pixels,512)
  owned_sampled_spans+=1;owned_sampled_writers.add(span[2])
 for owner in edge_span_owners:
  if (owner['serial'],owner['pass_index'],owner['command'])!=h[2:5]:continue
  pixels=(C.c_uint16*512)();assert road_sample(asset,len(raw),owner['span'],reciprocal,pixels,512)
  span=struct.unpack_from('<20I',raw,40+owner['span']*80)
  packed=bytes(pixels)[:span[1]*2];base=span[0]-0x06000000
  start=143*240+237-base
  if start<0:start-=240
  # The original duplicate-row store adds240bytes to the same packed span.
  if start>=len(packed):start-=240
  assert list(packed[start:start+3])==edge_reference[h[2],h[3]]
  sentinel=(C.c_uint16*512)(*([999]*512));assert not road_sample(asset,len(raw),owner['span'],reciprocal,sentinel,span[1]-1) and all(x==999 for x in sentinel)
  owned_edge_checks+=3
assert owned_edge_checks==12
for asset,raw in road_assets:assert C.string_at(asset,len(raw))==raw;d.nf_live_road_asset_free(asset)
for b in bundles:assert C.string_at(b["pointer"],b["size"])==b["raw"];d.nf_live_ordered_bundle_free(b["pointer"])
assert len(copies)==4
for x in copies:assert C.string_at(x['pointer'],len(x['raw']))==x['raw'];d.nf_indexed_copy_free(x['pointer'])
assert [x['refresh'] for x in copies if x['serial']==38]==[3616,3619]
for serial in [22,38]:
 sequence=[x for x in operations if x['serial']==serial]
 assert sum(x['kind']==1 for x in sequence)==2 and sum(x['kind']==2 for x in sequence)>=4
 assert all(a['cycles']<b['cycles'] for a,b in zip(sequence,sequence[1:]))
report=dict(strip_mutation_checks=strip_mutation_checks,road_bundle_rejections=road_bundle_rejections,road_bundle_assets=[x[2] for x in road_bundles],owned_sampled_spans=owned_sampled_spans,owned_sampled_writers=[hex(x) for x in sorted(owned_sampled_writers)],owned_edge_indices=owned_edge_checks,owned_road_assets=len(road_assets),edge_span_owners=edge_span_owners,malformed_bundle_rejections=malformed_cases,result='PASS',copies=[{k:v for k,v in x.items() if k not in ['pointer','raw']} for x in copies],operations=operations,pass_cycles=pass_cycles,world_events=world_events,merged_events=merged_events,bundles=[{k:v for k,v in b.items() if k not in ["pointer","raw"]} for b in bundles],history_eviction_close_lifetime=True,wrong_epoch_atomic=True,complete_original_ram_exact=True,scope='Original immutable ordered ROM-copy/fill capture/publication component only; no scene assembler/GPU integration.')
(p/'live-owned-indexed-copy-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
