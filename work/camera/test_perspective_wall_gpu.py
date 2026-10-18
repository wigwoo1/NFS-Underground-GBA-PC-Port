from pathlib import Path
import struct,json,subprocess
p=Path('work/camera');out=Path('outputs/nfsug-native-renderer/camera-research')
projection=json.loads((out/'native-wall-projection-comparison.json').read_text())
world=json.loads((out/'native-world-audit.json').read_text());results=[]
for index in (10,25):
 surface=world['surfaces'][index];geometry=next(w for w in projection['walls'] if w['source']==surface['source'])
 material=(p/f'captured-wall-gpu-{index}.bin').read_bytes();width,height,mode=struct.unpack_from('<III',material);assert mode==2
 data=struct.pack('<II',width,height)+material[12:]
 for point,uv in zip(geometry['native_points'],surface['uv']):data+=struct.pack('<5d',*point['projected'],point['camera'][2],*uv)
 path=p/f'perspective-wall-gpu-{index}.bin';path.write_bytes(data)
 run=subprocess.run([str((p/'perspective-wall-gpu-preview.exe').resolve()),str(path.resolve())],capture_output=True,text=True,timeout=30)
 results.append(dict(surface=index,source=surface['source'],returncode=run.returncode,output=run.stdout.strip(),stderr=run.stderr.strip()));assert run.returncode==0,results[-1]
report=dict(result='PASS',materials=results,scope='Actual sampled world/camera wall projection with GPU perspective texture/shader tested against CPU rational barycentric sampling. Subpixel triangle-edge and texel-boundary neighborhoods excluded and counted; not original ARM column equivalence or whole-scene fidelity.')
(out/'perspective-wall-gpu-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
