"""Isolate visible sky-stage changes with unchanged backdrop and commit binding."""
import hashlib,json,sys,subprocess
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1])
subprocess.run([sys.executable,'work/camera/verify_live_4k_sky_readback_candidate.py',str(folder)],check=True,stdout=subprocess.DEVNULL)
m=json.loads((folder/'manifest.json').read_text());transitions=[];previous=None
for r in m['rows']:
 def pixels(name,key):
  raw=(folder/r[name]).read_bytes();assert len(raw)==3840*64*4 and hashlib.sha256(raw).hexdigest()==r[key]
  return np.frombuffer(raw,np.uint8).reshape(64,3840,4)[:,:,:3]
 sky=pixels('sky_stage_strip_file','sky_stage_strip_sha256');final=pixels('strip_file','strip_sha256')
 visible=np.all(sky==final,axis=2)
 if previous is not None:
  a,oldsky,oldfinal,oldvisible=previous
  same_backdrop=r['backdrop_sha256']==a['backdrop_sha256']
  changed=np.any(sky!=oldsky,axis=2)
  exclusive=changed & visible & oldvisible
  transitions.append(dict(index=r['index'],same_backdrop=same_backdrop,sky_stage_changed_pixels=int(changed.sum()),visible_sky_changed_pixels=int(exclusive.sum()),both_frames_visible_sky_pixels=int((visible & oldvisible).sum()),commit_gap_ms=(r['commit'][6]-a['commit'][6])/1e6))
 previous=(r,sky.copy(),final.copy(),visible.copy())
assert len(transitions)==31
qualified=[r for r in transitions if r['same_backdrop'] and r['visible_sky_changed_pixels']>0]
assert qualified,'No visible sky motion isolated'
out=dict(result='PASS_LIVE_VISIBLE_SKY_STAGE_MOTION',samples=32,isolated_visible_sky_transitions=len(qualified),transitions=transitions,scope='Sky-stage change with identical backdrop, same coordinates surviving unchanged through world/HUD draw in both matching committed frames. Only captured sky band and bounded window; equal final colors cannot independently prove absence of a coincident overdraw. No cadence, physical scanout or fullscene fidelity proof; readback perturbs timing.')
(folder/'sky-stage-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='transitions'}))
