import json,sys,struct,hashlib
from pathlib import Path
report=json.loads(Path(sys.argv[1]).read_text());pool=json.loads(Path(sys.argv[2]).read_text());samples={r['sample_begin_ns']:r for r in report['presentation_samples'] if r.get('native_committed_sample')};rows=pool['sky_region_records'];assert len(rows)==96
checks=[];previous=None
for record in rows:
 v=record['values'];assert v[5]==0;sample=samples[v[0]];alpha=struct.unpack('<d',struct.pack('<Q',v[3]))[0];assert alpha==sample['alpha'];assert v[2]==sample['epoch']
 raw=Path(record['path']).read_bytes();assert len(raw)==3840*16*3
 check=dict(sample_begin_ns=v[0],frame_refresh=v[1],source_refresh=sample['refresh'],source_older=sample['source_older'],epoch=v[2],alpha=alpha,sky_fraction=sample['sky_fraction'],read_ns=v[4],sha256=hashlib.sha256(raw).hexdigest())
 if previous:check['changed_pixels_from_previous']=sum(raw[i:i+3]!=previous[i:i+3] for i in range(0,len(raw),3))
 previous=raw;checks.append(check)
out=dict(result='PASS_LIVE_TARGET_REGION_IDENTITIES',rows=checks,changed_transitions=sum(x.get('changed_pixels_from_previous',0)>0 for x in checks),scope='Actual completed fullscene target top16rows, before native presentation. Pixel changes may include HUD/world; no exclusive sky attribution, scanout or pacing certification. Readback overhead diagnostic.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print('PASS',len(checks),'records',out['changed_transitions'],'changed transitions')
