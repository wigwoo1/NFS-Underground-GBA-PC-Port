"""Audit actual per-refresh display page runs against completion history."""
from pathlib import Path
import ctypes as C,csv,json,struct
p=Path(__file__).resolve().parent
exec(compile((p/'test_live_owned_indexed_copy.py').read_text().split("\nassert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'test_live_owned_indexed_copy.py'),'exec'))
helper=C.CDLL(str(p/"ordered-capture-test.dll"));capture=helper.nf_ordered_capture_test;capture.argtypes=[P,C.c_uint64,U,U,U,U,P];helper.nf_ordered_capture_test_free.argtypes=[P]
d.nf_page_write_audit_enable.argtypes=[U];d.nf_page_write_audit_counts_copy.argtypes=[P];d.nf_page_write_audit_origins_copy.argtypes=[P]
d.nf_page_write_audit_generation_copy.argtypes=[P];d.nf_layer_queue_page_generation.argtypes=[C.c_uint64,U,U,P]
class Proof(C.Structure):
 _fields_=[('epoch',C.c_uint64),('completion_generation',C.c_uint64),('display_generation',C.c_uint64)]+[(x,U) for x in ['serial','completion_refresh','display_refresh','page']]
stable=helper.nf_stable_scene_create_test;stable.argtypes=[P,Z,P,Z,P,Z,C.POINTER(Proof),P];helper.nf_stable_scene_free_test.argtypes=[P]
d.nf_layer_queue_split_generations.argtypes=[C.c_uint64,U,U,C.c_uint64,U,C.c_uint64,P]
d.nf_layer_queue_selection_split.argtypes=[C.c_uint64,U,U,U,U,U,P]
completed=[];capture_checks=[];stable_checks=[];stable_exported=set()
@Sink
def display_sink(ctx,e,data,size):
 h=struct.unpack('<8I',C.string_at(data,32));generation=(C.c_uint64*2)();assert d.nf_page_write_audit_generation_copy(generation);completed.append(dict(epoch=e,serial=h[4],begin=h[5],end=h[6],page=h[7],generation=list(generation)));return 1
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
checks=[]
d.nf_page_write_audit_generation_reset();d.nf_page_write_audit_enable(1)
try:
 assert d.nf_native_scene_sink(display_sink,None) and d.nf_native_scene_multimodel(1)
 assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024);d.nf_live_surface_audit_enable(1);assert d.nf_bitmap_text_enable(1) and d.nf_layer_queue_enable(1)
 for step,row in enumerate(csv.DictReader(Path(str(prefix)+'-input.csv').open())):
  d.nf_page_write_audit_enable(1);d.nf_frame(int(row['keys']));refresh=d.nf_layer_queue_latest();counts=(C.c_uint64*2)();assert d.nf_page_write_audit_counts_copy(counts);origins=(C.c_uint64*4)();assert d.nf_page_write_audit_origins_copy(origins);assert all(counts[i]==origins[i]+origins[i+2] for i in range(2))
  generation=(C.c_uint64*2)();assert d.nf_page_write_audit_generation_copy(generation)
  if not completed:continue
  epoch=completed[-1]['epoch'];runs=[];missing=0;raw=C.create_string_buffer(34944);hud_parts=[]
  for y in range(160):
   if not d.nf_layer_queue_hud_row(epoch,refresh,y,raw,34944):missing+=1;continue
   hud_parts.append(raw.raw);r,n,display=struct.unpack_from('<IIH',raw.raw);assert (r,n)==(refresh,y);state=(display&7,(display>>4)&1,bool(display&128))
   if not runs or runs[-1]['state']!=state:runs.append(dict(begin=y,end=y+1,state=state))
   else:runs[-1]['end']=y+1
  for run in runs:
   owners=[c for c in completed if c['epoch']==epoch and c['page']==run['state'][1] and c['end']<=refresh]
   run['latest_completed_owner']=owners[-1] if owners else None
   if owners:run['store_bytes_since_completion']=generation[run['state'][1]]-owners[-1]['generation'][run['state'][1]]
   historical=C.c_uint64(123);available=d.nf_layer_queue_page_generation(epoch,refresh,run['state'][1],C.byref(historical));run['scanline_generation_available']=bool(available);run['scanline_generation']=historical.value if available else None
   if len(runs)==1:assert available and owners and historical.value==owners[-1]['generation'][run['state'][1]]
  if len(runs)==1 and not missing and runs[0]['latest_completed_owner']:
   o=runs[0]['latest_completed_owner'];proof=Proof(epoch,o['generation'][o['page']],generation[o['page']],o['serial'],o['end'],refresh,o['page']);bp=P();bn=Z();available=road_bundle_get(epoch,o['serial'],C.byref(bp),C.byref(bn));valid=False;rejected=0
   if available:
    try:
     texts=[];covers=[]
     for y in range(160):
      ti=C.create_string_buffer(240);co=C.create_string_buffer(240);assert d.nf_layer_queue_text_row(epoch,refresh,y,ti,co,240);texts.append(ti.raw);covers.append(co.raw)
     text=struct.pack('<8I',0x5854464e,1,epoch&0xffffffff,epoch>>32,refresh,240,160,38400)+b''.join(texts)+b''.join(covers);hud=b''.join(hud_parts);owner=P(123)
     proof.display_generation+=1;assert not stable(bp,bn.value,hud,len(hud),text,len(text),C.byref(proof),C.byref(owner)) and owner.value==123;rejected+=1;proof.display_generation-=1
     for field in ['epoch','serial','completion_refresh','display_refresh','page']:
      saved=getattr(proof,field);setattr(proof,field,saved+1);assert not stable(bp,bn.value,hud,len(hud),text,len(text),C.byref(proof),C.byref(owner)) and owner.value==123;rejected+=1;setattr(proof,field,saved)
     valid=bool(stable(bp,bn.value,hud,len(hud),text,len(text),C.byref(proof),C.byref(owner)));assert valid;
     if o['serial'] in [22,38] and refresh>o['end'] and o['serial'] not in stable_exported:
      stem=p/f"stable-page-{o['serial']}";(Path(str(stem)+'-bundle.bin')).write_bytes(C.string_at(bp,bn.value));Path(str(stem)+'-hud.bin').write_bytes(hud);Path(str(stem)+'-text.bin').write_bytes(text);Path(str(stem)+'-proof.bin').write_bytes(bytes(proof));stable_exported.add(o['serial'])
     helper.nf_stable_scene_free_test(owner)
    finally:d.nf_live_ordered_bundle_free(bp)
   stable_checks.append(dict(refresh=refresh,serial=o['serial'],bundle_available=bool(available),complete_owned_stable=valid,negative_proof_rejections=rejected))
  if len(runs)==2 and all(x['latest_completed_owner'] for x in runs):
   older,newer=[x['latest_completed_owner'] for x in runs];cut=U(123);assert d.nf_layer_queue_split_generations(epoch,refresh,older['page'],older['generation'][older['page']],newer['page'],newer['generation'][newer['page']],C.byref(cut)) and cut.value==runs[0]['end'];bad=U(123);assert not d.nf_layer_queue_split_generations(epoch,refresh,older['page'],older['generation'][older['page']],newer['page'],newer['generation'][newer['page']]+1,C.byref(bad)) and bad.value==123;legacy=U(123);legacy_ok=d.nf_layer_queue_selection_split(epoch,older['end'],older['page'],newer['end'],newer['page'],refresh,C.byref(legacy));owner=P();ok=capture(d._handle,epoch,older['serial'],newer['serial'],refresh,runs[0]['end'],C.byref(owner));capture_checks.append(dict(refresh=refresh,older=older['serial'],newer=newer['serial'],cut=runs[0]['end'],complete_owned_capture=bool(ok),generation_partition_exact=True,wrong_generation_atomic=True,legacy_split_guard=bool(legacy_ok)))
   if ok:helper.nf_ordered_capture_test_free(owner)
  checks.append(dict(step=step,refresh=refresh,epoch=epoch,missing_rows=missing,store_bytes=list(counts),cpu_store_bytes=list(origins[:2]),dma_store_bytes=list(origins[2:]),runs=runs))
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  path=p/('display-ownership-check-'+name+'.bin');d.nf_dump(str(path).encode(),address,size);raw=path.read_bytes();path.unlink();assert raw==Path(str(prefix)+'-'+name+'.bin').read_bytes()
 last=checks[-1];page=last['runs'][0]['state'][1];sentinel=C.c_uint64(123)
 d.nf_page_write_audit_generation_reset();assert not d.nf_layer_queue_page_generation(last['epoch'],last['refresh'],page,C.byref(sentinel)) and sentinel.value==123
finally:d.nf_close()
summary=dict(audited_refreshes=len(checks),complete_rows=sum(c['missing_rows']==0 for c in checks),single_page=sum(len(c['runs'])==1 for c in checks),split_page=sum(len(c['runs'])==2 for c in checks),other_run_counts=sorted(set(len(c['runs']) for c in checks)-{1,2}),completed_scenes=len(completed),full_original_ram_exact=True)
summary['single_page_cpu_written_refreshes']=sum(len(c['runs'])==1 and c['cpu_store_bytes'][c['runs'][0]['state'][1]]>0 for c in checks)
summary['single_page_dma_written_refreshes']=sum(len(c['runs'])==1 and c['dma_store_bytes'][c['runs'][0]['state'][1]]>0 for c in checks)
summary['dma_store_bytes_per_page']=[sum(c['dma_store_bytes'][i] for c in checks) for i in range(2)]
summary['cpu_store_bytes_per_page']=[sum(c['cpu_store_bytes'][i] for c in checks) for i in range(2)]
summary['single_page_changed_since_completion']=sum(len(c['runs'])==1 and c['runs'][0].get('store_bytes_since_completion',-1)!=0 for c in checks)
summary['stable_captures_available']=sum(x['complete_owned_stable'] for x in stable_checks)
summary['stable_proof_negative_rejections']=sum(x['negative_proof_rejections'] for x in stable_checks)
summary['single_page_scanline_generation_exact']=sum(len(c['runs'])==1 and c['runs'][0]['scanline_generation_available'] for c in checks)
summary['reset_invalidates_history_atomic']=True
summary['generation_split_partitions']=sum(x['generation_partition_exact'] for x in capture_checks)
summary['legacy_split_guard_rejections']=[x['refresh'] for x in capture_checks if not x['legacy_split_guard']]
summary['split_captures_available']=sum(x['complete_owned_capture'] for x in capture_checks)
report=dict(result='AUDITED',summary=summary,stable_capture_checks=stable_checks,split_capture_checks=capture_checks,checks=checks,scope='Actual display register page ownership and completed scene availability only. Same-page partial writes, persistent bytes and geometry motion are not established by page equality.')
(p/'display-ownership-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
