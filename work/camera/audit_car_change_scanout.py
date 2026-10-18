"""Original per-scanline page provenance around sequential car-selection draws."""
from pathlib import Path
import ctypes as C,csv,json,struct,hashlib
p=Path(__file__).resolve().parent
exec(compile((p/'diagnose_late_model_pairs.py').read_text().split("assert d.nf_init(session['rom'].encode(),b'')")[0],str(p/'diagnose_late_model_pairs.py'),'exec'))
prefix=p/'prototype-runs/threaded-prepared-4c0a478bbea14eedbc3a639513b0b9d6'
session=json.loads(Path(str(prefix)+'-session.json').read_text())
for name in ['rom','state']:
 assert hashlib.sha256(Path(session[name]).read_bytes()).hexdigest()==session[name+'_sha256'].lower()
publications=[]
@Sink
def observe(ctx,epoch,data,size):
 header=struct.unpack('<8I',C.string_at(data,32))
 publications.append(dict(epoch=epoch,serial=header[4],begin=header[5],end=header[6],page=header[7]))
 return 1
d.nf_native_scene_epoch.restype=C.c_uint64
d.nf_layer_queue_row.argtypes=[C.c_uint64,U,U,P,U]
records=[];previous=None
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(session['state'].encode(),0)
try:
 assert d.nf_native_scene_sink(observe,None) and d.nf_native_scene_multimodel(1)
 rom=Path(session['rom']).read_bytes();assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
 assert d.nf_layer_queue_enable(1)
 epoch=d.nf_native_scene_epoch();size=d.nf_layer_row_size();assert size==100480
 buffer=C.create_string_buffer(size)
 for row in csv.DictReader(Path(str(prefix)+'-input.csv').open()):
  d.nf_frame(int(row['keys']));refresh=d.nf_layer_queue_latest()
  if not (3519<=refresh<=3550 or 3610<=refresh<=3640):continue
  pages=[bytearray(),bytearray()];displayed=bytearray();selection=[]
  for y in range(160):
   assert d.nf_layer_queue_row(epoch,refresh,y,buffer,size)
   raw=buffer.raw;assert struct.unpack_from('<2I',raw)==(refresh,y)
   control=struct.unpack_from('<H',raw,8)[0];assert control&7==4
   page=(control>>4)&1;selection.append(page)
   for i in range(2):pages[i].extend(raw[128+i*0xa000+y*240:128+i*0xa000+(y+1)*240])
   displayed.extend(pages[page][-240:])
  changes=None
  if previous and previous[0]==refresh-1:
   changes=dict(page_pixels=[sum(a!=b for a,b in zip(pages[i],previous[1][i])) for i in range(2)],displayed_pixels=sum(a!=b for a,b in zip(displayed,previous[2])))
  spans=[]
  for y,page in enumerate(selection):
   if not spans or spans[-1]['page']!=page:spans.append(dict(first_row=y,last_row=y,page=page))
   else:spans[-1]['last_row']=y
  records.append(dict(refresh=refresh,page_spans=spans,page_sha256=[hashlib.sha256(x).hexdigest() for x in pages],displayed_sha256=hashlib.sha256(displayed).hexdigest(),changes=changes))
  previous=(refresh,pages,displayed)
finally:d.nf_close()
assert len(records)==63
hidden_intervals=[]
for first,last,switch,split in [(3525,3543,3544,6),(3616,3633,3634,99)]:
 interval=[x for x in records if first<=x['refresh']<=last]
 assert len(interval)==last-first+1
 assert all(x['page_spans']==[dict(first_row=0,last_row=159,page=1)] for x in interval)
 assert len({x['displayed_sha256'] for x in interval})==1
 assert len({x['page_sha256'][0] for x in interval})>1
 event=next(x for x in records if x['refresh']==switch)
 assert event['page_spans']==[dict(first_row=0,last_row=split-1,page=1),dict(first_row=split,last_row=159,page=0)]
 hidden_intervals.append(dict(first=first,last=last,displayed_page=1,hidden_written_page=0,displayed_indices_unchanged=True,page_switch_refresh=switch,page_switch_row=split))
report=dict(result='AUDITED',records=records,hidden_intervals=hidden_intervals,publications=[x for x in publications if 20<=x['serial']<=24 or 36<=x['serial']<=40],scope='All160 original scanline rows perrefresh, both Mode4 page bytes and selected displayed indices. Palette/OBJ not included; index change is not native geometry correspondence, final row snapshot is not CPU write chronology.')
(p/'car-change-scanout-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(refreshes=len(records),publications=report['publications'],page_switches=[dict(refresh=x['refresh'],spans=x['page_spans']) for x in records if len(x['page_spans'])>1]),indent=2))
