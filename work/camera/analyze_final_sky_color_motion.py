import json,sys,struct
from pathlib import Path
import numpy as np
pool=json.loads(Path(sys.argv[1]).read_text());report=json.loads(Path(sys.argv[2]).read_text());samples={s['sample_begin_ns']:s for s in report['presentation_samples'] if s.get('native_committed_sample')};previous=None;transitions=[]
y=np.floor((648+np.arange(16)+.5)/13.5).astype(int)-48;x=np.floor((np.arange(3240)+.5)/13.5).astype(int)
for record in pool['sky_region_records']:
 p=Path(record['path']);final=np.frombuffer(p.read_bytes(),np.uint8).reshape(16,3240,3);sky=np.frombuffer(p.with_suffix('.sky.rgb').read_bytes(),np.uint8).reshape(16,3240,3);mask=np.frombuffer(p.with_suffix('.hudmask').read_bytes(),np.uint8).reshape(2,240)[y[:,None],x[None,:]].astype(bool);s=samples[record['values'][0]]
 agrees=np.all(final==sky,axis=2)&mask
 if previous:
  old_s,old_sky,old_agrees=previous;moving=np.any(sky!=old_sky,axis=2);surviving=moving&agrees&old_agrees;same=(old_s['source_older'],old_s['refresh'])==(s['source_older'],s['refresh'])
  transitions.append(dict(sample_begin_ns=record['values'][0],same_pair=same,sky_stage_changed=int(moving.sum()),sky_matching_final_changed=int(surviving.sum()),matching_both_frames=int((agrees&old_agrees).sum())))
 previous=s,sky.copy(),agrees.copy()
assert len(transitions)==95
out=dict(result='MEASURED_FINAL_SKY_COLOR_MOTION',transitions=transitions,moving_sky_transitions=sum(t['sky_stage_changed']>0 for t in transitions),final_sky_color_motion_transitions=sum(t['sky_matching_final_changed']>0 for t in transitions),pair_boundaries=sum(not t['same_pair'] for t in transitions),scope='Same-coordinate final RGB equals sky-stage RGB in both frames and HUD gate passes. Does not establish exclusive world provenance, all-sky coverage, scanout or60fps cadence. No geometry matching or redraw.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='transitions'})
