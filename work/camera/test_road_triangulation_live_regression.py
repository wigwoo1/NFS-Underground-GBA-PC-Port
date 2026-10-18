"""Whole-image regression after factoring the existing triangulation helper.
Requires the immediately preceding continuous-camera reference capture.
"""
from pathlib import Path
import csv,hashlib,json,os,subprocess,sys
p=Path('work/camera').resolve();prefix='road-attribute-motion'
files=sorted(p.glob(prefix+'-*.ppm'));assert len(files)==12
before=[hashlib.sha256(f.read_bytes()).hexdigest() for f in files]
camera_before=list(csv.DictReader((p/(prefix+'-cameras.csv')).open()))
source_before=list(csv.DictReader((p/(prefix+'-sources.csv')).open()))
env=os.environ.copy()
for key in ('NF_LIVE_HUD','NF_LIVE_WORLD_CLASSIFIED','NF_LIVE_ROAD_ATTRIBUTES','NF_CONTINUOUS_CAMERA','NF_CAPTURE_DEFERRED'):env[key]='1'
env['NF_ROAD_RECIPROCAL']=str(p/'road-correction-reciprocal.bin');env['NF_CAPTURE_SEQUENCE']=str(p/prefix)
env['NF_CAPTURE_SOURCE_MANIFEST']=str(p/(prefix+'-sources.csv'));env['NF_CAPTURE_ROAD_EDGES']=str(p/(prefix+'-edges.csv'));env['NF_CAPTURE_CAMERA_PAIRS']=str(p/(prefix+'-cameras.csv'))
run=subprocess.run([sys.executable,str(p/'test_live_road_attributes.py'),'5','--window-buffer'],env=env,capture_output=True,text=True)
(p/'road-triangulation-live-regression.log').write_text(run.stdout+run.stderr);assert run.returncode==0,run.stderr
camera_after=list(csv.DictReader((p/(prefix+'-cameras.csv')).open()));source_after=list(csv.DictReader((p/(prefix+'-sources.csv')).open()))
assert camera_before==camera_after
for a,b in zip(source_before,source_after):
 for key in ('index','epoch','older','newer','alpha','target','older_refresh','newer_refresh','hud_refresh'):assert a[key]==b[key]
after=[hashlib.sha256(f.read_bytes()).hexdigest() for f in files];assert before==after
report=dict(result='PASS',byte_exact_complete_4K_frames=len(files),image_sha256=after,source_camera_records_exact=len(camera_after),scope='Before/after full-image regression for verbatim triangulation factoring at same captured camera/source timings, continuous camera and road UV correction. Exact diagnostic images do not prove original game pixel fidelity or smooth60fps.')
(p/'road-triangulation-live-regression-tests.json').write_text(json.dumps(report,indent=2));print(report)
