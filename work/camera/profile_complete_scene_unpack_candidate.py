import cProfile,pstats,json,hashlib,statistics
from pathlib import Path
from owned_scene_process_transport import pack,unpack
setup=Path('work/camera/test_direct_shared_input_decode_service_parity.py').read_text().split(" alphas=(.01")[0].split(" manifest=")[1]
import textwrap
ns={};exec('from pathlib import Path\nimport json\n'+textwrap.dedent(' manifest='+setup),ns)
packets=[pack(ns['envs'][0]['frames'][i],ns['envs'][0]['scenes'][i]) for i in range(2)];rom=ns['envs'][0]['rom'];rows=[]
for iteration in range(8):
 profile=cProfile.Profile();profile.enable();decoded=[unpack(p,rom) for p in packets];profile.disable()
 assert [pack(f,s) for f,s in decoded]==packets
 stats=pstats.Stats(profile);functions=[]
 for (filename,line,name),(primitive,calls,own,inclusive,callers) in stats.stats.items():functions.append(dict(file=filename,line=line,name=name,calls=calls,own_ms=own*1000,inclusive_ms=inclusive*1000))
 rows.append(dict(iteration=iteration,total_ms=stats.total_tt*1000,functions=sorted(functions,key=lambda x:x['own_ms'],reverse=True)[:30]))
out=dict(result='PASS_EXACT_CAPTURED_SCENE_UNPACK_PROFILE',rounds=rows,median_ms=statistics.median(x['total_ms'] for x in rows),scope='Two current immutable captured endpoint packets, eight independent decode calls and exact re-encoding. Profile perturbs cost; not live cadence or target9566 pair.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/direct-decode9566-profile30-20261010');(cp/'unpack-profile.json').write_text(json.dumps(out,indent=2));print(out['result'],out['median_ms']);print(json.dumps(rows[-1]['functions'][:10],indent=2))

