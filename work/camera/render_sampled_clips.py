"""Fixture-specific sampled wall clips, retaining packet command order."""
from pathlib import Path
import json,struct,os,subprocess,hashlib
from clip_metadata import packet_layout
p=Path('work/camera').resolve();packet=p/'candidate-140.bin';new=p/'order-boundary-141.bin';raw=packet.read_bytes();h,order,ids=packet_layout(raw)
samples=json.loads((p/'texture-provenance-tests.json').read_text())['portal_samples'];rows=[]
for sample in samples:
 alpha=sample['alpha']
 if alpha==1:continue # Exact newer endpoint uses its captured sidecar.
 plans=sample['all_wall_plans'];sources=[x['source'] for x in plans];assert len(sources)==len(set(sources))
 by_source={x['source']:x for x in plans};assert set(sources)<={x[2] for x in ids if x[0]==2}
 data=struct.pack('<5Id',0x3150434e,h[4],h[5],h[6],len(ids),alpha)
 for ident in ids:
  bounds=by_source[ident[2]]['viewport'] if ident[0]==2 and ident[2] in by_source else [0,0,0,0]
  data+=struct.pack('<5I4H',*ident,*bounds)
 label=f'sampled-all-{alpha}';clip=p/(label+'.clips');clip.write_bytes(data)
 env=os.environ.copy();env['NF_CAPTURE_CLIPS']=str(clip);env['NF_PREVIEW_FRACTION']=str(alpha);env['NF_PREVIEW_PHASE']='2'
 result=subprocess.run([str(p/'sampled-clip-preview.exe'),str(packet),str(new),str(p/label)],env=env,check=True,capture_output=True,text=True)
 rows.append(dict(alpha=alpha,wall_plans=len(plans),output=label+'-2.ppm',log=result.stdout.strip()))
(p/'sampled-clip-tests.json').write_text(json.dumps(dict(result='PASS',packet_sha256=hashlib.sha256(raw).hexdigest(),samples=rows,scope='Fixture replay; original packet order retained, appended candidate order unchanged. Object eligibility retained; no live or motion correctness claim.'),indent=2));print('Rendered',len(rows),'samples')
