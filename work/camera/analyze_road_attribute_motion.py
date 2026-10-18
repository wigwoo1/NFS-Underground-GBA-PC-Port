from pathlib import Path
import json,csv,hashlib,sys,math
from PIL import Image,ImageDraw
import numpy as np
p=Path('work/camera');prefix=sys.argv[1] if len(sys.argv)>1 else 'road-attribute-motion';files=sorted(p.glob(prefix+'-*.ppm'));assert len(files)==12
rows=[r for r in csv.DictReader((p/'road-attribute-live-parity.csv').open()) if int(r['ready'])][180:192];assert len(rows)==12
sources=list(csv.DictReader((p/(prefix+'-sources.csv')).open()));assert len(sources)==12
for i,(source,row) in enumerate(zip(sources,rows)):
 assert int(source['index'])==i and int(source['epoch'])>0
 for key in ('older','newer'):assert int(source[key])==int(row[key])
 for key in ('alpha','target'):assert abs(float(source[key])-float(row[key]))<1e-9
 assert int(source['older_refresh'])==int(row['source_older_refresh'])
 assert int(source['newer_refresh'])==int(row['source_newer_refresh'])
 assert int(source['hud_refresh'])==math.floor(float(source['target']))
 assert int(source['older_refresh'])<=float(source['target'])<=int(source['newer_refresh'])
 assert int(source['rings'])>0 and int(source['near_crossings'])>0
 assert int(row['render_start_ns'])<=int(source['capture_ns'])<=int(row['render_end_ns'])
 assert i==0 or int(source['capture_ns'])>int(sources[i-1]['capture_ns'])
frames=[np.asarray(Image.open(f)) for f in files];assert all(a.shape==(2160,3840,3) for a in frames)
changes=[]
for i,(a,b) in enumerate(zip(frames,frames[1:])):
 mask=np.any(a!=b,axis=2);assert mask.any();changes.append(dict(pair=i,changed_pixels=int(mask.sum()),road_lower_changed=int(mask[1080:2050,300:3540].sum()),world_upper_changed=int(mask[300:1080,300:3540].sum()),display_gap=int(rows[i+1]['display_index'])-int(rows[i]['display_index']),target_gap=float(rows[i+1]['target'])-float(rows[i]['target'])))
assert all(c['road_lower_changed']>0 and c['world_upper_changed']>0 for c in changes)
canvas=Image.new('RGB',(1280,750),(30,30,30));draw=ImageDraw.Draw(canvas)
for i,f in enumerate(files):
 im=Image.open(f);im.thumbnail((320,180));x=i%4*320;y=i//4*250;canvas.paste(im,(x,y));draw.text((x+5,y+183),f'{i}: display {rows[i]["display_index"]}',fill='white')
canvas.save(p/(prefix+'-contact.png'))
if '--consecutive' in sys.argv:assert all(c['display_gap']==1 for c in changes)
report=dict(result='PASS',frames=12,dimensions=[3840,2160],unique_frames=len({hashlib.sha256(a.tobytes()).hexdigest() for a in frames}),transitions=changes,scope='12 captured complete native images change across sampled scene regions; GPU readback/disk writes disturb cadence, so not smooth60fps or original visual parity evidence.')
report['sample_duration_seconds']=(int(rows[-1]['display_index'])-int(rows[0]['display_index']))/60
report['verified_capture_sources']=sources
report['scene_pair_changes']=sum((a['older'],a['newer'])!=(b['older'],b['newer']) for a,b in zip(sources,sources[1:]))
report['source_manifest_scope']='Per-image source pairs, target/alpha, HUD floor selection, render-time capture bounds and corrected near-edge crossings verified. Crossing counts do not identify individual edges or prove clipping pixel continuity.'
if '--consecutive' in sys.argv:report['scope']='12 consecutive corrected complete native4K frames sampled at60Hz display targets; upper/lower scene regions change, deferred disk writes, GPU readback present. Only183ms sampled, not fullroute smooth motion, near-transition isolation, physical scanout or original whole-scene fidelity proof.'
(p/(prefix+'-image-tests.json')).write_text(json.dumps(report,indent=2));print(report)
