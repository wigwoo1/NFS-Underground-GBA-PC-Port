from pathlib import Path
import json,hashlib
import numpy as np
folder=Path('work/camera/prototype-runs/owned-sky-world-packets-1791590492879412500');m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and m['pending']==0
rows=[]
for r in m['rows']:
 p=r['world_packets'];raw=(folder/p['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256'];a=np.load(folder/p['file']);v=a['vertices'];o=a['offsets'];ids=a['texture_ids'];states=a['states'];assert v.shape==(p['vertices'],10) and len(ids)==p['draws'] and states.shape==(len(ids),72);assert o[0]==0 and o[-1]==len(v) and np.all(o[1:]>o[:-1]) and np.all((o[1:]-o[:-1])%3==0) and np.isfinite(v).all()
 draws=[]
 for i in range(len(ids)):
  q=v[o[i]:o[i+1]];config=np.frombuffer(states[i,:32].tobytes(),dtype='<f4');rect=np.frombuffer(states[i,32:64].tobytes(),dtype='<i4');modes=np.frombuffer(states[i,64:].tobytes(),dtype='<u4');assert ids[i]<4096 and modes[0]<=3 and modes[1]<=1
  draws.append(dict(draw=i,texture_id=int(ids[i]),vertices=len(q),bounds_min=q[:,:2].min(0).tolist(),bounds_max=q[:,:2].max(0).tolist(),textured=bool(config[4]),config=config.tolist(),scissor_viewport=rect.tolist(),modes=modes.tolist()))
 rows.append(dict(index=r['index'],source_pair=[r['source_older'],r['source_newer']],y=r['y'],vertices=len(v),draws=draws))
out=dict(result='PASS_COMPLETE_CAPTURED_WORLD_DRAW_BUFFERS',frames=len(rows),draw_count_min=min(len(x['draws']) for x in rows),draw_count_max=max(len(x['draws']) for x in rows),untextured_draws=sum(not d['textured'] for x in rows for d in x['draws']),rows=rows,scope='Immutable actual consumer buffers captured before source close. Bounds are not rastercoverage, occlusion correctness or sourceprimitive classification proof. No screenpolygon fitting or geometry changes.')
(folder/'world-packet-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='rows'})
