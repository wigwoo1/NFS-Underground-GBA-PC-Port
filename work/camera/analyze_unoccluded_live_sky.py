import json,sys
from pathlib import Path
import numpy as np
pool=json.loads(Path(sys.argv[1]).read_text());report=json.loads(Path(sys.argv[2]).read_text());assert pool['sky_coverage_reads']==96 and pool['sky_coverage_resources']==0
samples={s['sample_begin_ns']:s for s in report['presentation_samples'] if s.get('native_committed_sample')};rows=[];transitions=[];previous=None;y=np.floor((648+np.arange(16)+.5)/13.5).astype(int)-48;x=np.floor((np.arange(3240)+.5)/13.5).astype(int)
for record in pool['sky_region_records']:
 p=Path(record['path']);final=np.frombuffer(p.read_bytes(),np.uint8).reshape(16,3240,3);sky=np.frombuffer(p.with_suffix('.sky.rgb').read_bytes(),np.uint8).reshape(16,3240,3);world=np.frombuffer(p.with_suffix('.worldmask').read_bytes(),np.uint8).reshape(16,3240);assert set(np.unique(world))<=set((0,1));hud=np.frombuffer(p.with_suffix('.hudmask').read_bytes(),np.uint8).reshape(2,240)[y[:,None],x[None,:]].astype(bool);eligible=(world==0)&hud;s=samples[record['values'][0]];assert record['values'][2]==s['epoch']
 mismatch=eligible&np.any(final!=sky,axis=2);assert not mismatch.any(),(len(rows),int(mismatch.sum()))
 rows.append(dict(sample_begin_ns=s['sample_begin_ns'],visible_sky_pixels=int(eligible.sum()),world_covered=int(world.sum())))
 if previous:
  old_s,old_sky,old_eligible=previous;changed=np.any(sky!=old_sky,axis=2)&eligible&old_eligible;same=(s['source_older'],s['refresh'])==(old_s['source_older'],old_s['refresh']);transitions.append(dict(same_pair=same,visible_sky_changed=int(changed.sum()),common_visible=int((eligible&old_eligible).sum())))
 previous=s,sky.copy(),eligible.copy()
assert len(rows)==96 and sum(r['visible_sky_pixels'] for r in rows)>0
out=dict(result='PASS_LIVE_UNOCCLUDED_SKY_PIXELS',visible_sky_pixels=sum(r['visible_sky_pixels'] for r in rows),rows=rows,transitions=transitions,moving_visible_transitions=sum(t['visible_sky_changed']>0 for t in transitions),moving_visible_pair_boundaries=sum(not t['same_pair'] and t['visible_sky_changed']>0 for t in transitions),scope='Stencil marks surviving actual world fragments. Conservative HUDgate + worldmask0: finalRGB equals sky-stageRGB. Same-coordinate movement only where both frames visible. Limited96capture strip, not allscene or physicalscanout/cadence.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('rows','transitions')})
