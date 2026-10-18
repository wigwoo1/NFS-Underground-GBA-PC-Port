"""Join actual original draw value changes to immutable native source identities."""
import json,struct,sys,hashlib
from pathlib import Path
report_path=Path(sys.argv[1]);report=json.loads(report_path.read_text())
sources=json.loads(Path(sys.argv[2]).read_text());packets={tuple(row['identity'][2:]):row for row in sources['original_endpoints']}
checks=[]
for scene in report['scenes']:
 key=(scene['begin_refresh'],scene['end_refresh'])
 if key not in packets:continue
 row=packets[key];data=Path(row['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256']
 sections={t:data[o:o+n] for t,o,n in (struct.unpack_from('<3I',data,32+i*12) for i in range(5))}
 world=struct.unpack_from('<I',sections[2],4)[0];models=struct.unpack_from('<I',sections[1],4)[0]
 ids=[struct.unpack_from('<5I',sections[5],8+20*i) for i in range(world+models)]
 joins=[]
 for draw in scene['draws']:
  if draw['model_object'] is not None:
   matches=[i for i,v in enumerate(ids) if v[0]==3 and v[2]==int(draw['model_object'],16)]
  else:
   kind=1 if draw['pc']=='0x30032f0' else 2
   matches=[i for i,v in enumerate(ids) if v[0]==kind and v[1]==int(draw['state'],16) and v[2]==int(draw['source'],16)]
  assert matches,(key,draw)
  joins.append(dict(draw_id=draw['draw_id'],source_identity_ordinals=matches,visible_changed_pixels=draw['visible_changed_pixels']))
 checks.append(dict(interval=key,packet_sha256=row['sha256'],native_models=models,original_model_draws=sum(d['model_object'] is not None for d in scene['draws']),all_observed_routines_captured=scene['all_observed_routines_captured'],original_routine_entries=scene['original_routine_entries'],captured_entries=scene['captured_entries'],joins=joins))
assert checks
out=report_path.with_name(report_path.stem+'-source-joins.json');out.write_text(json.dumps(dict(result='PASS',checks=checks,scope='Completed original scene intervals and actual traced original routine identities join to retained native source identities. Model object resolved from original invocation, not reused stack context. Membership only; not matching raster coverage or proving omitted native models should draw.'),indent=2));print(json.dumps(dict(result='PASS',joined_scenes=len(checks),joined_draws=sum(len(c['joins']) for c in checks),fully_captured_scenes=sum(c['all_observed_routines_captured'] for c in checks))))
