import copy,json
from pathlib import Path
from verify_live_sky_motion_evidence import verify
names=['owned-native-1791342021305508000.json','owned-native-1791502761374205500.json']
results=[]
for name in names:
 r=json.loads((Path('work/camera/prototype-runs')/name).read_text());audit=verify(r);rejected=[]
 for mutation in ('phase','source','commit_time','present_time'):
  bad=copy.deepcopy(r);x=next(x for x in bad['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented'))
  if mutation=='phase':x['sky_fraction']=(x['sky_fraction']+.25)%1
  elif mutation=='source':bad['sky_capture_records']=[s for s in bad['sky_capture_records'] if (s['epoch'],s['publication'])!=(x['epoch'],x['source_older'])]
  elif mutation=='commit_time':x['native_committed_sample'][6]=0
  elif x.get('native_deadline_path'):x['callback_timing']['present_end_ns']=0
  else:x['present_end_ns']=0
  try:verify(bad)
  except (AssertionError,KeyError):rejected.append(mutation)
  else:raise AssertionError('Accepted corruption: '+mutation)
 results.append(dict(report=name,samples=audit['committed_fullscene_sky_samples'],rejected=rejected))
out=dict(result='PASS_SKY_AUDIT_SCHEMAS',checks=results,scope='Legacy and native deadline captured telemetry; not physical pixel motion.')
Path('work/camera/prototype-runs/native-sky-audit-schema-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
