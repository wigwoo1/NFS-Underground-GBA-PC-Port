from pathlib import Path
import json
p=Path('work/camera');packets=json.loads((p/'visibility-transition-packet-tests.json').read_text());frames=[]
for i in range(12):
 r=json.loads((p/f'road-visibility-alignment-{i:03}-tests.json').read_text());record=packets['records'][i]
 assert r['result']=='PASS' and r['target_refresh']==record['target'] and abs(r['alpha']-record['alpha'])<1e-10
 assert r['rendered_4K_cases']==12 and len(r['cases'])==4
 combined=r['cases'][0];assert combined['ring']==-1
 frames.append(dict(index=i,target=r['target_refresh'],source_pair=record['source_pair'],removed_pixels=combined['removed_pixels'],removed_bbox=combined['removed_pixel_bbox_gl'],added_pixels=combined['added_pixels'],camera_changed_rgb=combined['camera_change_rgb_pixels'],camera_changed_coverage=combined['camera_change_coverage_pixels'],camera_position_difference=r['continuous_to_native_camera_position_difference'],bounds=[c['native_bounds'] for c in r['cases'][1:]],depth_difference_max=combined['depth_absolute_difference_max']))
summary=dict(result='PASS',measurement_only=True,frames=12,source_pairs=packets['distinct_source_pairs'],rendered_4K_cases=144,removed_pixels_range=[min(f['removed_pixels'] for f in frames),max(f['removed_pixels'] for f in frames)],camera_changed_rgb_range=[min(f['camera_changed_rgb'] for f in frames),max(f['camera_changed_rgb'] for f in frames)],camera_changed_coverage_max=max(f['camera_changed_coverage'] for f in frames),depth_difference_max=max(f['depth_difference_max'] for f in frames),records=frames,scope='Twelve measured native bounds/camera states across four source pairs; roads only. Captured complete packets include eight walls and one model but those visibility paths are not tested here. No original raster parity, continuous visibility between targets, full-scene motion or 60fps proof.')
(p/'visibility-transition-gpu-tests.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
