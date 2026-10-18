from pathlib import Path
import sys,json,copy
from verify_live_sky_motion_evidence import verify
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-phase-runtime-audit-20261006')
reports=['owned-native-1791341920392317300.json','owned-native-1791342021305508000.json','owned-native-1791341452666464800.json']
passed=[]
for name in reports:
 r=json.loads((Path('work/camera/prototype-runs')/name).read_text());a=verify(r);passed.append(dict(report=name,phase_checks=a['continuous_sky_phase_checks'],samples=a['committed_fullscene_sky_samples']))
base=json.loads((Path('work/camera/prototype-runs')/reports[1]).read_text());rejected=[]
for mutation in ('weight','mode','missing_source','duplicate_source','angle','asset'):
 r=copy.deepcopy(base);x=next(x for x in r['presentation_samples'] if x.get('interpolated') and x.get('hidden_window_presented'))
 key=(x['epoch'],x['source_older']);source=next(s for s in r['sky_capture_records'] if (s['epoch'],s['publication'])==key)
 if mutation=='weight':x['sky_fraction']=(x['sky_fraction']+.25)%1
 elif mutation=='mode':x['sky_phase_mode']='original_offsets'
 elif mutation=='missing_source':r['sky_capture_records'].remove(source)
 elif mutation=='duplicate_source':r['sky_capture_records'].append(copy.deepcopy(source))
 elif mutation=='angle':source['angle']=2**32
 elif mutation=='asset':source['asset_origin']+=1
 try:verify(r)
 except (AssertionError,KeyError):rejected.append(mutation)
 else:raise AssertionError('Corruption accepted:'+mutation)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',reports=passed,rejected=rejected,scope='Captured phase invariants only; not independent scanout or visual oracle'),indent=2));print(json.dumps(dict(passed=passed,rejected=rejected)))
