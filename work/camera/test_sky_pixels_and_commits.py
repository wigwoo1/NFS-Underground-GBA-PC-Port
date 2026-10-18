import copy,json,sys
from pathlib import Path
sys.path.insert(0,'work/camera')
from audit_sky_pixels_and_commits import analyze
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791421692644305400.json').read_text()); d=json.loads(Path('work/camera/prototype-runs/selected-sky-pixels-1791421692829884800.json').read_text())
analyze(r,d)
for mutation in ('identity','owner','pixel'):
 bad=copy.deepcopy(d)
 if mutation=='identity':bad['records'][0]['alpha']+=.01
 elif mutation=='owner':bad['records'][0]['thread']+=1
 else:bad['records'][0]['sky_reference_points'][0]['stage']=[999,999,999]
 try:analyze(r,bad)
 except AssertionError:pass
 else:raise AssertionError(mutation)
print('PASS reference plus three rejected attribution/pixel mutations')
