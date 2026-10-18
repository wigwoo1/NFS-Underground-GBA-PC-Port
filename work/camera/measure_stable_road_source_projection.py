from pathlib import Path
import json,math,hashlib
p=Path('work/camera');mapping=json.loads((p/'stable-road-emission-source-map.json').read_text());joins=json.loads((p/'stable-road-source-transform-comparison.json').read_text())['checks'];projection=json.loads((p/'stable-road-projected-inputs.json').read_text())['projection'];checks=[]
for road,join in zip(mapping['checks'],joins):
 assert road['source']==join['source'];rows=[];vertices=join['vertices']
 for m in road['mapping']:
  i=m['source_edge'];j=(i+1)%len(vertices)
  def point(kind):
   a=vertices[i][kind];b=vertices[j][kind]
   if not m['near_generated']:return vertices[m['source_vertex']][kind]
   t=(64-a[2])/(b[2]-a[2]);return [a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),64]
  original=m['six_words'][:2];native=point('native_camera');q14=point('original_camera');project=lambda v:[projection[k]+projection[2]*v[k]/v[2] for k in range(2)];np=project(native);qp=project(q14)
  rows.append(dict(emitted_ordinal=m['emitted_ordinal'],source_edge=i,near_generated=m['near_generated'],original_integer_xy=original,native_geometric_xy=np,q14_geometric_xy=qp,native_minus_original=[np[k]-original[k] for k in range(2)],q14_geometric_minus_original=[qp[k]-original[k] for k in range(2)],native_transform_only_delta=[np[k]-qp[k] for k in range(2)]))
 checks.append(dict(source=road['source'],rows=rows))
summary={}
for generated in [False,True]:
 rows=[r for c in checks for r in c['rows'] if r['near_generated']==generated];summary['near' if generated else 'retained']=dict(count=len(rows),max_native_original_delta=max(abs(x) for r in rows for x in r['native_minus_original']),max_q14_geometric_original_delta=max(abs(x) for r in rows for x in r['q14_geometric_minus_original']),max_transform_only_delta=max(abs(x) for r in rows for x in r['native_transform_only_delta']))
assert summary['near']['count']==4 and summary['retained']['count']==13
report=dict(result='MEASURED',summary=summary,checks=checks,projection=projection,source_map_sha256=hashlib.sha256((p/'stable-road-emission-source-map.json').read_bytes()).hexdigest(),scope='Comparisons joined by verified source edge and emitted ordinal, never projected polygon matching. Geometric near positions versus original fixed clipping/projection; no renderer substitution or pixel fidelity acceptance.');(p/'stable-road-source-projection-deltas.json').write_text(json.dumps(report,indent=2));print(json.dumps(summary,indent=2))
