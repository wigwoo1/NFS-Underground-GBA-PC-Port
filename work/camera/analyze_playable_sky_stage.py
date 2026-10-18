import json,struct,hashlib,shutil,sys
from pathlib import Path
rp,pp,cp=map(Path,sys.argv[1:4]);cp.mkdir(exist_ok=True)
r=json.loads(rp.read_text());p=json.loads(pp.read_text());records=p['playable_sky_capture'];assert len(records)==96
samples={x['native_draw_boundary'][0]:x for x in r['presentation_samples'] if x.get('native_draw_boundary')}
checks=[];previous=None;moving=0;boundaries=0
for i,record in enumerate(records):
 row=record['values'];x=samples[row[0]];assert row[1]==x['native_draw_boundary'][1]
 alpha=struct.unpack('<d',struct.pack('<Q',row[2]))[0];assert alpha==x['alpha'];assert row[4]==600+i
 path=Path(record['path']);sky=path.with_suffix('.sky.rgb').read_bytes();final=path.read_bytes();assert len(sky)==len(final)==3240*16*3
 changed=0 if previous is None else sum(sky[n:n+3]!=previous[0][n:n+3] for n in range(0,len(sky),3))
 boundary=previous is not None and (x['epoch'],x['refresh'])!=previous[1]
 moving+=changed>0;boundaries+=boundary and changed>0
 checks.append(dict(index=i,epoch=x['epoch'],refresh=x['refresh'],alpha=alpha,sky_weight=struct.unpack('<d',struct.pack('<Q',row[3]))[0],sky_changed_pixels=changed,pair_boundary=boundary,sky_sha256=hashlib.sha256(sky).hexdigest(),final_sha256=hashlib.sha256(final).hexdigest()))
 (cp/'pixels').mkdir(exist_ok=True);shutil.copy2(path,cp/'pixels'/f'{i}.rgb');shutil.copy2(path.with_suffix('.sky.rgb'),cp/'pixels'/f'{i}.sky.rgb');previous=(sky,(x['epoch'],x['refresh']))
result=dict(result='PASS_EXACT_LIVE_SKY_STAGE_IDENTITY',captures=96,moving_sky_stage_transitions=moving,moving_boundary_transitions=boundaries,checks=checks,scope='Actual playable sky-beforeworld pixels; exact draw identities. Does not prove unoccluded final sky, physical presentation or60fps cadence.')
(cp/'sky-stage-analysis.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='checks'})
