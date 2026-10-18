import subprocess,sys,json
from pathlib import Path
fixture='work/camera/prototype-runs/owned-native-1791434872973979000.json';runs=[]
for name in ('world_upload','backdrop_batch'):
 p=Path('work/camera/test_owned_native_source_'+name+'_parity_candidate.py');source=p.read_text();marker="reference=json.loads(Path('work/camera/prototype-runs/source-direct-present-component.json').read_text());assert "
 assert source.count(marker)==1
 source=source[:source.index(marker)]+"\nprint(json.dumps(dict(hashes=[x['native_rgb_sha256'] for x in results],cache_after=cache_after)))\n"
 q=Path('work/camera/prototype-runs/backdrop-'+name+'-same-fixture-temp.py');q.write_text(source)
 done=subprocess.run([sys.executable,str(q),fixture,'unused'],env=__import__('os').environ|{'PYTHONPATH':str(Path('work/camera').resolve())},capture_output=True,text=True)
 assert done.returncode==0,done.stderr
 runs.append(dict(renderer=name,**json.loads(done.stdout)))
assert runs[0]['hashes']==runs[1]['hashes'],'Same-fixture backdrop batch differs'
out=dict(result='PASS_SAME_FIXTURE_BACKDROP_PARITY',fixture=fixture,runs=runs,scope='Five actual4K readbacks per isolated process, batch vs launcher same captured input. Original saved reference mismatch not overwritten. No independent fidelity or live cadence proof.')
Path('work/camera/prototype-runs/native-backdrop-same-fixture-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
