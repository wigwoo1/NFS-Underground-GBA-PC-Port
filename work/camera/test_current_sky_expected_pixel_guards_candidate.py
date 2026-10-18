import copy,json,runpy,sys
from pathlib import Path
from unittest.mock import patch
folder=Path('work/camera/prototype-runs/current-backend-sky-readback-1791562369577319400');manifest=folder/'manifest.json';original=Path.read_text;base=json.loads(original(manifest));cases=[]
x=copy.deepcopy(base);x['pending']=1;cases.append(x)
x=copy.deepcopy(base);x['rows'][0]['backend']='other.dll';cases.append(x)
x=copy.deepcopy(base);x['rows'][0]['commit'][4]+=1;cases.append(x)
x=copy.deepcopy(base);x['rows'][0]['strip_sha256']='0'*64;cases.append(x)
for i,data in enumerate(cases):
 def read(path,*args,**kwargs):return json.dumps(data) if path==manifest else original(path,*args,**kwargs)
 with patch.object(Path,'read_text',read),patch.object(Path,'write_text',return_value=0) as written,patch.object(sys,'argv',['audit',str(folder)]):
  try:runpy.run_path('work/camera/analyze_current_sky_expected_pixels_candidate.py',run_name='__main__')
  except AssertionError:pass
  else:raise AssertionError(i)
  assert written.call_count==0,i
out=dict(result='PASS_CURRENT_SKY_PIXEL_REJECTION_GUARDS',rejected=len(cases),scope='Reject pending capture, wrong backend, mismatched commit and corrupt pixel hash; actual capture files untouched.')
Path('work/camera/prototype-runs/current-sky-expected-guards-20261009.json').write_text(json.dumps(out,indent=2));print(out)
