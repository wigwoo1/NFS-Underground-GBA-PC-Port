import json,struct,hashlib,shutil
from pathlib import Path
rp=Path('work/camera/prototype-runs/owned-native-1791447468356352200.json');pp=Path('work/camera/prototype-runs/pool-cleanup-1791447468143140300.json')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/playable-sky-capture-live-20261008')
r=json.loads(rp.read_text());p=json.loads(pp.read_text());records=p['playable_sky_capture'];assert len(records)==96
samples={x['native_draw_boundary'][0]:x for x in r['presentation_samples'] if x.get('native_draw_boundary')}
checks=[];previous=None;changed=0
for i,record in enumerate(records):
 row=record['values'];x=samples[row[0]];assert row[1]==x['native_draw_boundary'][1]
 alpha=struct.unpack('<d',struct.pack('<Q',row[2]))[0];assert alpha==x['alpha']
 assert row[4]==600+i
 raw=Path(record['path']).read_bytes();assert len(raw)==3240*16*3
 if previous is not None:changed+=raw!=previous
 checks.append(dict(index=i,ordinal=row[4],epoch=x['epoch'],refresh=x['refresh'],alpha=alpha,sha256=hashlib.sha256(raw).hexdigest()))
 (cp/'pixels').mkdir(exist_ok=True);shutil.copy2(record['path'],cp/'pixels'/f'{i}.rgb');previous=raw
out=dict(result='PASS_EXACT_LIVE_CAPTURE_IDENTITY',captures=96,adjacent_changed_regions=changed,checks=checks,scope='Completed actual playable fullscene region pixels matched to exact draw start/end/alpha. Region contains world/HUD; changes alone do not prove sky provenance or display cadence.')
(cp/'capture-analysis.json').write_text(json.dumps(out,indent=2));print(out['result'],changed)
