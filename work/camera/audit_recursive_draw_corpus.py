from pathlib import Path
import json,os,sys,subprocess
p=Path(__file__).resolve().parent;cases=[];folder=p/'recursive-draw-corpus';folder.mkdir(exist_ok=True)
for older,newer in [(16,17),(64,65)]:
 for tick in (range(101) if os.environ.get('NF_ORACLE_ALL') else [0,23,50,51,99,100]):
  label=f'{older}-{newer}-{tick}';env=dict(os.environ,NF_ORACLE_FIXTURE=f'arm-oracle-fresh-{label}-after.bin')
  for script in ['diagnose_original_road_writes.py','compare_original_recursive_draw.py']:
   run=subprocess.run([sys.executable,str(p/script)],env=env,capture_output=True,text=True,timeout=30);assert run.returncode==0,run.stderr
  original=json.loads((p/'original-road-write-diagnostic.json').read_text());native=json.loads((p/'recursive-original-native-comparison.json').read_text());(folder/(label+'-original.json')).write_text(json.dumps(original,indent=2));(folder/(label+'-native.json')).write_text(json.dumps(native,indent=2))
  exact=original['result']=='DIAGNOSTIC_RETURN' and native['native_ok'] and len(native['native'])==len(native['original']) and all(all(x[k] for k in ('source_exact','bounds_exact','material_exact','record_exact','pass_exact','wall_inputs_exact')) for x in native['comparisons'])
  cases.append(dict(label=label,exact=exact,world_count=len(native['native']),source_mismatches=[x['index'] for x in native['comparisons'] if not x['source_exact']],provenance_mismatches=[x for x in native['comparisons'] if not all(x[k] for k in ('material_exact','record_exact','pass_exact','wall_inputs_exact'))],bound_mismatches=[x['index'] for x in native['comparisons'] if not x['bounds_exact']]))
  print(label,exact,flush=True)
report=dict(result='PASS_SAMPLED_WORLD_PROVENANCE_AND_TEXTURE_INPUTS' if all(x['exact'] for x in cases) else 'MISMATCH',cases=cases,scope='Coherent sampled poses; original roads rasterized in dummy peripheral memory, walls bypassed. Kind/source order, region record/pass, visible road-write extents, expanded texture address/shift/height/framebuffer match. Shading/palette, model and complete occurrence ownership not proven.')
(p/'recursive-draw-corpus-audit.json').write_text(json.dumps(report,indent=2))



