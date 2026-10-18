"""Classify GPU coverage failures by original writer ownership; never repair by measured holes."""
from pathlib import Path
import collections,json,struct
base=Path('C:/NFSUG-Workspace');folder=base/'NFSUG-restored-composition-fixtures';out=base/'NFSUG-android-local/app-restored-composition-gpu-tests';capture=json.loads((folder/'source-fixture-capture-report.json').read_text());gpu=json.loads((out/'restored-composition-gpu-failure-report.json').read_text());owners={r['owner']['serial']:r for r in capture['road_records']};points=[];groups=[]
for check in gpu['coverage_details']:
 if not check['holes']:continue
 entry=capture['fixtures'][str(check['refresh'])];raw=(folder/entry['filename']).read_bytes();h=struct.unpack_from('<16Q',raw);kinds=collections.Counter();xs=[];ys=[]
 for x,y in check['coordinates']:
  i=int(h[5]==2 and y>=h[6]);owner=entry['owners'][i];record=owners[owner['serial']];proof=(folder/record['provenance']['filename']).read_bytes();page=(folder/record['full_replay']['filename']).read_bytes();cell=y*240+x;kind=proof[cell];refresh=struct.unpack_from('<I',proof,38400+cell*4)[0];at=h[10+i*2];kinds[kind]+=1;xs.append(x);ys.append(y)
  points.append(dict(display_refresh=check['refresh'],owner_serial=owner['serial'],owner_begin=owner['begin'],owner_end=owner['end'],x=x,y=y,original_last_writer_kind=kind,original_last_writer_refresh=refresh,earlier_interval=refresh<owner['begin'],source_index=page[cell],initial_background_covered=raw[at+38480+cell]))
 groups.append(dict(display_refresh=check['refresh'],holes=check['holes'],x_range=[min(xs),max(xs)],y_range=[min(ys),max(ys)],last_writer_kinds=dict(kinds)))
assert len(points)==88 and len({(p['display_refresh'],p['x'],p['y']) for p in points})==70
assert all(p['original_last_writer_kind']==2 and p['original_last_writer_refresh']==12101 and p['y']>=158 for p in points)
report=dict(result='RESTORED_GPU_COVERAGE_SOURCE_DIAGNOSTIC',observations=len(points),unique_display_cells=70,groups=groups,source_points=points,rendering_modified=False)
(out/'restored-coverage-source-diagnostic.json').write_text(json.dumps(report,indent=2));print('CONFIRMED: 88 observations / 70 unique cells; original wall writer refresh12101, rows158-159; no renderer change')
