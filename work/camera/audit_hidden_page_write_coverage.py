"""Bounded original CPU write coverage; compare complete RAM with observer off."""
from pathlib import Path
from project_paths import load_session
import ctypes as C,csv,json,hashlib,collections
p=Path(__file__).resolve().parent
exec(compile((p/'diagnose_late_model_pairs.py').read_text().split("assert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'diagnose_late_model_pairs.py'),'exec'))
prefix=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6'
session=load_session(Path(str(prefix)+'-session.json'))
ledger=list(csv.DictReader(Path(str(prefix)+'-input.csv').open()))
for name in ['rom','state']:assert hashlib.sha256(Path(session[name]).read_bytes()).hexdigest()==session[name+'_sha256'].lower()
d.nf_page_write_audit_enable.argtypes=[U]
d.nf_page_write_audit_copy.argtypes=[P,U]
d.nf_page_write_audit_sources.argtypes=[P,U]
d.nf_dump.argtypes=[C.c_char_p,U,U]
d.nf_read.argtypes=[U,C.c_int];d.nf_read.restype=U
d.nf_bitmap_dma_trace.argtypes=[C.c_char_p]
d.nf_bitmap_dma_state.argtypes=[P]
edge_pixel_trace=[];coverage=[];ram_hashes=[];uncovered_checks=[];dma_windows=[];baseline=None;prior_writers=None;prior_sources=None
for observed in [False,True]:
 assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
 try:
  assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
  rom=Path(session['rom']).read_bytes();assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
  assert d.nf_layer_queue_enable(1);d.nf_page_write_audit_enable(0)
  for row in ledger:
   current=d.nf_layer_queue_latest()
   if observed and current==3615:d.nf_page_write_audit_enable(1)
   if observed and current in [3528,3618]:
    d.nf_page_write_audit_enable(1)
    out=p/'page-write-audit-baseline.bin';d.nf_dump(str(out).encode(),0x06000000,38400)
    baseline=out.read_bytes();assert len(baseline)==38400;out.unlink()
    dma_trace=p/f'hidden-page-dma-{current}.csv';assert d.nf_bitmap_dma_trace(str(dma_trace).encode())
    channels=(U*28)();assert d.nf_bitmap_dma_state(channels)
    dma_windows.append(dict(begin_after_refresh=current,path=str(dma_trace),initial_channels=[dict(zip(['source','destination','count_control','next_source','next_destination','next_count','when'],channels[i*7:(i+1)*7])) for i in range(4)]))
   d.nf_frame(int(row['keys']));current=d.nf_layer_queue_latest()
   if observed and current==3618:
    prior_writers=(U*(240*160))();assert d.nf_page_write_audit_copy(prior_writers,C.sizeof(prior_writers))
    prior_sources=(U*(240*160))();assert d.nf_page_write_audit_sources(prior_sources,C.sizeof(prior_sources))
   if observed and (3529<=current<=3534 or 3619<=current<=3625):
    values=(U*(240*160))();assert d.nf_page_write_audit_copy(values,C.sizeof(values))
    for x,y in [(0,23),(1,23),(239,22),(0,24),(238,143),(239,143),(237,143),(238,144),(239,144),(0,159),(238,159)]:
     at=y*240+x
     edge_pixel_trace.append(dict(refresh=current,x=x,y=y,baseline=baseline[at],index=d.nf_read(0x06000000+at,1)&255,writer=hex(values[at])))
    rows=[]
    for y in range(160):
     counts=collections.Counter(values[y*240:(y+1)*240])
     rows.append(dict(row=y,covered=240-counts.get(0,0),uncovered_columns=[x for x in range(240) if not values[y*240+x]],writers={hex(k):v for k,v in counts.items() if k}))
    coverage.append(dict(refresh=current,rows=rows,world_covered=sum(x['covered'] for x in rows[24:144]),world_total=120*240))
    if current in [3534,3625]:
     out=p/'page-write-audit-final.bin';d.nf_dump(str(out).encode(),0x06000000,38400)
     final=out.read_bytes();assert len(final)==38400;out.unlink()
     pixels=[dict(x=x,y=y,before=baseline[y*240+x],after=final[y*240+x],prior_cpu_writer=hex(prior_writers[y*240+x]) if current==3625 else None,prior_copy_source=hex(prior_sources[y*240+x]) if current==3625 else None) for y in range(24,144) for x in rows[y]['uncovered_columns']]
     uncovered_checks.append(dict(refresh=current,pixels=pixels,unchanged=sum(x['before']==x['after'] for x in pixels),changed=sum(x['before']!=x['after'] for x in pixels)))
   if observed and current in [3534,3625]:d.nf_page_write_audit_enable(0);assert d.nf_bitmap_dma_trace(None)
  hashes={}
  for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   out=p/('page-write-audit-'+name+'.bin');d.nf_dump(str(out).encode(),address,size)
   data=out.read_bytes();assert len(data)==size;hashes[name]=hashlib.sha256(data).hexdigest();out.unlink()
  ram_hashes.append(hashes)
 finally:d.nf_page_write_audit_enable(0);d.nf_close()
assert ram_hashes[0]==ram_hashes[1] and len(coverage)==13
assert next(x for x in coverage if x['refresh']==3532)['world_covered']==28800
assert next(x for x in coverage if x['refresh']==3623)['world_covered']==28800
retained=uncovered_checks[1]['pixels']
if retained:
 assert all(0x08000000<=int(x['prior_copy_source'],16)<0x08000000+len(rom) for x in retained)
 assert all(rom[int(x['prior_copy_source'],16)-0x08000000]==x['before']==x['after'] for x in retained)
 image_bases={int(x['prior_copy_source'],16)-x['y']*240-x['x'] for x in retained}
 assert len(image_bases)==1
 uncovered_checks[1]['rom_copy_provenance']=dict(exact_pixels=len(retained),stride=240,image_base=hex(next(iter(image_bases))))
for window in dma_windows:
 trace=Path(window['path']);window['trace_sha256']=hashlib.sha256(trace.read_bytes()).hexdigest()
 window['events']=list(csv.DictReader(trace.open()))
report=dict(result='AUDITED',original_updates_per_run=len(ledger),full_original_ram_equal=ram_hashes[0]==ram_hashes[1],ram_sha256=ram_hashes[0],edge_pixel_trace=edge_pixel_trace,coverage=coverage,uncovered_checks=uncovered_checks,dma_windows=dma_windows,scope='Cumulative CPU stores to page0 independently from original refresh3529 and3619 onward, beginning before second ROM-copy call in the latter interval. DMA register trace and initial controls are observational, not DMA execution coverage. CPU coverage does not prove native command ownership or permit dropping earlier passes.')
(p/'hidden-page-write-coverage-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(result=report['result'],full_original_ram_equal=True,uncovered_checks=[{k:v for k,v in x.items() if k!='pixels'} for x in uncovered_checks],dma_event_counts=[len(x['events']) for x in dma_windows],world_coverage=[dict(refresh=x['refresh'],covered=x['world_covered'],total=x['world_total']) for x in coverage]),indent=2))
