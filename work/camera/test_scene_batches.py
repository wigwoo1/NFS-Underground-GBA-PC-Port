from pathlib import Path
import collections,json
from scene_batches import batches
root=Path('work/camera');reports=[]
for name in ('world','stationary'):
    scenes=list(batches(root/f'{name}.bin'));assert scenes
    camera_values=[];spans=collections.Counter();page_mismatches=[];camera_mismatches=[];empty=0;geometry_counts=[]
    for scene in scenes:
        cameras=set();pages=set();counts=collections.Counter()
        for e in scene['events']:
            b=e['blocks'];pc=e['pc'];counts[hex(pc)]+=1
            if pc in (0x03000d48,0x03001800,0x03002964,0x030032f0,0x03000304):
                cameras.add(b[2][1]);pages.add(int.from_bytes(b[3][1][:4],'little'))
            elif pc==0x03002628:cameras.add(b[63][1])
            elif pc in (0x030045e0,0x03004770):pages.add(int.from_bytes(b[56][1][:4],'little'))
        if len(cameras)>1:camera_mismatches.append(scene['serial'])
        expected=0x0600a000 if scene['display_page'] else 0x06000000
        if pages and pages!={expected}:page_mismatches.append(scene['serial'])
        if not cameras:empty+=1
        camera_values.append(next(iter(cameras)) if cameras else None)
        spans[scene['end_refresh']-scene['begin_refresh']]+=1
        geometry_counts.append(counts['0x3001800'])
    assert not camera_mismatches,(name,'mixed cameras',camera_mismatches)
    assert not page_mismatches,(name,'wrong display page',page_mismatches)
    assert not empty,(name,'unexpected empty gameplay scene')
    report={'sample':name,'complete_scenes':len(scenes),'refresh_spans':dict(spans),
            'distinct_cameras':len(set(camera_values)),'successive_scenes_with_identical_camera':sum(a==b for a,b in zip(camera_values,camera_values[1:])),
            'mixed_camera_batches':len(camera_mismatches),'wrong_page_batches':len(page_mismatches),
            'world_descriptor_counts':[min(geometry_counts),max(geometry_counts)]}
    reports.append(report)
result={'result':'PASS','samples':reports,'scope':'Offline gameplay capture grouping; menus, dropped captures, and live buffer handoff remain untested.'}
(root/'scene-batch-tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
